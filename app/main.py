from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import uvicorn
import os
from pathlib import Path
import time
import requests
import asyncio
import uuid

from src.rag.retriever import MedicalRetriever
from src.rag.vector_store import MedicalVectorStore
from src.llm.ollama_client import OllamaClient
from src.utils.config import settings
from src.utils.logger import setup_logging

from data.medical_dictionary import MEDICAL_TERMS_DICTIONARY, CATEGORY_COLORS

PROJECT_ROOT = Path(__file__).parent.parent  
STATIC_PATH = PROJECT_ROOT / "static"

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DiagnoAI Medical Assistant",
    description="AI-powered medical diagnosis assistant using local LLM",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = None
llm_client = None

active_requests = {}

class QueryRequest(BaseModel):
    query: str
    n_results: Optional[int] = 4  
    context_type: Optional[str] = None
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 1200  
    request_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    retrieval_metrics: Dict[str, Any]
    processing_time: float
    request_id: Optional[str] = None

class MedicalTermRequest(BaseModel):
    term: str

class MedicalTermResponse(BaseModel):
    term: str
    definition: str
    category: str
    severity: str
    source: str
    found: bool

class HealthResponse(BaseModel):
    status: str
    vector_store: Dict[str, Any]
    llm_status: str
    model_info: Dict[str, Any]
    ollama_endpoint: str

class CancelRequest(BaseModel):
    request_id: str

def get_medical_definition(term: str) -> MedicalTermResponse:
    try:
        clean_term = term.lower().strip()
        
        if clean_term in MEDICAL_TERMS_DICTIONARY:
            term_data = MEDICAL_TERMS_DICTIONARY[clean_term]
            return MedicalTermResponse(
                term=term,
                definition=term_data["definition"],
                category=term_data["category"],
                severity=term_data["severity"],
                source="DiagnoAI Medical Dictionary",
                found=True
            )
        
        definition = None
        source = "DiagnoAI Medical Dictionary"
        
        try:
            search_url = f"https://medlineplus.gov/ency/search/encyclopedia_Search_JSON.aspx?q={clean_term}"
            response = requests.get(search_url, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    first_result = data[0]
                    article_id = first_result.get('id', '')
                    title = first_result.get('title', '')
                    
                    if article_id:
                        article_url = f"https://medlineplus.gov/ency/article/{article_id}.htm"
                        article_response = requests.get(article_url, timeout=8)
                        
                        if article_response.status_code == 200:
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(article_response.content, 'html.parser')
                            
                            content_div = soup.find('div', {'id': 'ency_summary'})
                            if not content_div:
                                content_div = soup.find('div', {'class': 'section'})
                            if not content_div:
                                content_div = soup.find('div', {'id': 'main-content'})
                            
                            if content_div:
                                definition = content_div.get_text(strip=True)
                                definition = ' '.join(definition.split()[:150])
                                source = "MedlinePlus Medical Encyclopedia"
                                
                                if len(definition) >= 150:
                                    definition += "..."
            
        except Exception as e:
            logger.debug(f"MedlinePlus fetch failed for {term}: {e}")
        
        if not definition:
            try:
                wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{clean_term.replace(' ', '_')}"
                response = requests.get(wiki_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    definition = data.get('extract', '')
                    if definition and 'may refer to:' not in definition:
                        source = "Wikipedia Medical"
            except:
                pass
        
        if not definition:
            definition = f"'{term}' is a medical term. Consult healthcare providers or reliable medical sources for detailed information about this condition."
            source = "DiagnoAI Medical Reference"
        
        return MedicalTermResponse(
            term=term,
            definition=definition,
            category="general",
            severity="info", 
            source=source,
            found=bool(definition and len(definition) > 20)
        )
        
    except Exception as e:
        logger.error(f"Error fetching definition for {term}: {e}")
        return MedicalTermResponse(
            term=term,
            definition="Unable to fetch definition at this time. Please consult medical references or healthcare providers.",
            category="unknown",
            severity="info",
            source="DiagnoAI Medical Dictionary",
            found=False
        )

@app.on_event("startup")
async def startup_event():
    global retriever, llm_client
    
    try:
        logger.info("Starting DiagnoAI services...")
        
        logger.info("Initializing vector store...")
        vector_store = MedicalVectorStore(use_local_embeddings=False)
        retriever = MedicalRetriever(vector_store)

        total = vector_store.get_collection_stats()
        logger.info(f"Total documents in vector store: {total}")
        
        logger.info("Initializing Ollama client...")
        llm_client = OllamaClient()
        
        logger.info("Testing Ollama connection...")
        ollama_healthy = await llm_client.health_check()
        
        if ollama_healthy:
            logger.info("Ollama connection successful")
        else:
            logger.error("Ollama connection failed")
            raise ConnectionError("Cannot connect to Ollama service")
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        logger.warning("Services may be partially available")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    try:
        with open(STATIC_PATH / "index.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Frontend not found")
    except Exception as e:
        logger.error(f"Error serving frontend: {e}")
        raise HTTPException(status_code=500, detail="Error serving frontend")

@app.post("/query", response_model=QueryResponse)
async def query_medical_assistant(request: QueryRequest):
    start_time = time.time()
    request_id = request.request_id or f"req_{uuid.uuid4().hex[:8]}"
    
    active_requests[request_id] = {
        'cancelled': False,
        'start_time': start_time,
        'query': request.query
    }
    
    try:
        logger.info(f"Received query: {request.query} (ID: {request_id})")
        
        if retriever is None or llm_client is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        if active_requests[request_id]['cancelled']:
            logger.info(f"Request {request_id} was cancelled before processing")
            raise HTTPException(status_code=499, detail="Request cancelled by client")
        
        retrieved_docs = retriever.retrieve(
            query=request.query,
            n_results=request.n_results,
            context_type=request.context_type
        )
        
        logger.info(f"Retrieved {len(retrieved_docs)} documents for request {request_id}")
        
        if active_requests[request_id]['cancelled']:
            logger.info(f"Request {request_id} was cancelled before LLM call")
            raise HTTPException(status_code=499, detail="Request cancelled by client")
        
        answer, generation_info = await llm_client.generate_answer_with_cancellation(
            query=request.query,
            context_docs=retrieved_docs,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            request_id=request_id,
            cancellation_check=lambda: active_requests.get(request_id, {}).get('cancelled', False)
        )
        
        if active_requests[request_id]['cancelled']:
            logger.info(f"Request {request_id} was cancelled before response")
            raise HTTPException(status_code=499, detail="Request cancelled by client")
        
        if not answer or answer.strip() == "":
            logger.warning("LLM returned empty answer, generating fallback")
            if retrieved_docs:
                first_source = retrieved_docs[0]
                source_content = first_source.get('content', '')
                topic = first_source.get('metadata', {}).get('topic_title', 'Medical information')
                answer = f"I found information about {topic}. Based on medical sources:\n\n{source_content}\n\nPlease consult a healthcare provider for personalized medical advice."
            else:
                answer = "I couldn't find specific medical information about your query. Please consult with a healthcare professional for medical advice."
        
        logger.info(f"Generated answer for request {request_id}: {answer[:100]}...")
        
        retrieval_metrics = retriever.get_retrieval_metrics(request.query, retrieved_docs)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Query processed in {processing_time:.2f}s for request {request_id}")
        
        return QueryResponse(
            answer=answer,
            sources=retrieved_docs,
            retrieval_metrics=retrieval_metrics,
            processing_time=processing_time,
            request_id=request_id
        )
        
    except HTTPException as e:
        if e.status_code == 499:
            logger.info(f"Request {request_id} was cancelled")
        raise e
    except Exception as e:
        logger.error(f"Query processing failed for request {request_id}: {e}")
        processing_time = time.time() - start_time
        return QueryResponse(
            answer=f"Sorry, I encountered an error while processing your query: {str(e)}",
            sources=[],
            retrieval_metrics={},
            processing_time=processing_time,
            request_id=request_id
        )
    finally:
        if request_id in active_requests:
            del active_requests[request_id]

@app.post("/cancel-query")
async def cancel_query(request: CancelRequest):
    request_id = request.request_id
    if request_id in active_requests:
        active_requests[request_id]['cancelled'] = True
        logger.info(f"Cancelled request {request_id}")
        return {"status": "cancelled", "request_id": request_id}
    else:
        return {"status": "not_found", "request_id": request_id}

@app.post("/medical-term", response_model=MedicalTermResponse)
async def get_medical_term_definition(request: MedicalTermRequest):
    logger.info(f"Fetching definition for medical term: {request.term}")
    return get_medical_definition(request.term)

@app.get("/dictionary-stats")
async def get_dictionary_stats():
    return {
        "total_terms": len(MEDICAL_TERMS_DICTIONARY),
        "categories": list(set(term_data["category"] for term_data in MEDICAL_TERMS_DICTIONARY.values())),
        "severity_levels": list(set(term_data["severity"] for term_data in MEDICAL_TERMS_DICTIONARY.values()))
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    try:
        vector_stats = {}
        llm_status = "unknown"
        model_info = {}
        
        if retriever:
            vector_stats = retriever.vector_store.get_collection_stats()
        else:
            vector_stats = {"error": "Vector store not initialized"}
        
        if llm_client:
            try:
                llm_healthy = await llm_client.health_check()
                llm_status = "healthy" if llm_healthy else "unhealthy"
                model_info = await llm_client.get_model_info()
            except Exception as e:
                llm_status = f"unhealthy: {str(e)}"
        else:
            llm_status = "not_initialized"
        
        overall_status = "healthy"
        if "error" in vector_stats or "unhealthy" in llm_status:
            overall_status = "degraded"
        if not retriever or not llm_client:
            overall_status = "initializing"
        
        return HealthResponse(
            status=overall_status,
            vector_store=vector_stats,
            llm_status=llm_status,
            model_info=model_info,
            ollama_endpoint=f"{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            vector_store={"error": str(e)},
            llm_status="unknown",
            model_info={},
            ollama_endpoint=f"{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}"
        )

@app.get("/ready")
async def readiness_probe():
    try:
        if not retriever or not llm_client:
            raise HTTPException(status_code=503, detail="Services not initialized")
        
        if llm_client:
            healthy = await llm_client.health_check()
            if not healthy:
                raise HTTPException(status_code=503, detail="Ollama not ready")
        
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")

@app.get("/live")
async def liveness_probe():
    return {"status": "alive"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )