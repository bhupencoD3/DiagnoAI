import aiohttp
import json
import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Callable
import time
import asyncio

from src.utils.config import settings
from .prompts import MedicalPromptTemplate

class OllamaClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_url = f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}"
        self.model_name = settings.OLLAMA_MODEL
        self.prompt_template = MedicalPromptTemplate()
        self._model_template = None
        
    async def health_check(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        self.logger.info("Ollama server is healthy")
                        return True
                    else:
                        self.logger.error(f"Ollama server returned status: {response.status}")
                        return False
        except Exception as e:
            self.logger.error(f"Ollama health check failed: {e}")
            raise ConnectionError(f"Cannot connect to Ollama server at {self.base_url}")

    async def generate_answer_with_cancellation(
        self,
        query: str,
        context_docs: List[Dict[str, Any]],
        temperature: float = 0.1,
        max_tokens: int = 1000,
        request_id: str = None,
        cancellation_check: Callable[[], bool] = None
    ) -> Tuple[str, Dict[str, Any]]:
        start_time = time.time()
        
        try:
            context_text = self._format_context(context_docs, query)
            
            self.logger.info(f"Formatted Context for query '{query}': {len(context_text)} chars")
            
            has_limited_context = "LIMITED RELEVANT CONTEXT" in context_text
            
            if has_limited_context:
                system_message = """You are a medical assistant. The available medical sources have limited information for this specific question.

IMPORTANT:
- Use whatever information is available in the context
- Be transparent about what information is missing
- Do not make up information not in the context
- Always recommend consulting healthcare professionals"""

                user_message = f"""LIMITED MEDICAL CONTEXT:
{context_text}

QUESTION: {query}

Based on the limited context above, provide what information is available and clearly state what is missing."""
            else:
                system_message = """You are a medical assistant. Analyze the provided medical context and create a well-structured, easy-to-understand answer.

IMPORTANT INSTRUCTIONS:
- DO NOT just copy-paste from the context
- Analyze, synthesize and reason about the information
- Organize the answer in a logical flow
- Use bullet points or numbered lists when appropriate
- Make it readable and patient-friendly
- If context is limited, explain what's available vs what's missing
- Always emphasize consulting healthcare professionals"""

                user_message = f"""CONTEXT INFORMATION:
{context_text}

QUESTION: {query}

Based on the context above, provide a comprehensive, well-formatted answer that:
1. Synthesizes the key information
2. Organizes it logically  
3. Makes it easy to understand
4. Does NOT just repeat the context verbatim

Answer:"""

            prompt = self._build_mistral_prompt(system_message, user_message)
            
            self.logger.info(f"Sending streaming request to Ollama (Request ID: {request_id})")
            
            full_response = ""
            tokens_received = 0
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": True,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                            "num_thread": 8,
                            "repeat_penalty": 1.1,
                            "stop": ["</s>", "[INST]", "[/INST]"]
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=300)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Ollama API error: {response.status} - {error_text}")
                        return self._create_fallback_answer(context_text, query), {"error": True, "generation_time": time.time() - start_time}
                    
                    async for line in response.content:
                        if cancellation_check and cancellation_check():
                            self.logger.info(f"Generation cancelled for request {request_id}")
                            return "Generation cancelled by user", {"cancelled": True, "generation_time": time.time() - start_time}
                        
                        if line:
                            try:
                                line_text = line.decode('utf-8').strip()
                                if line_text:
                                    data = json.loads(line_text)
                                    if 'response' in data:
                                        full_response += data['response']
                                        tokens_received += 1
                                    
                                    if data.get('done', False):
                                        break
                            except json.JSONDecodeError:
                                continue
                            except Exception as e:
                                self.logger.warning(f"Error processing stream line: {e}")
                                continue
            
            generation_time = time.time() - start_time
            
            generation_info = {
                "model": self.model_name,
                "tokens_used": tokens_received,
                "generation_time": generation_time,
                "cancelled": False
            }
            
            self.logger.info(f"Generated {len(full_response)} chars in {generation_time:.2f}s for request {request_id}")
            
            if not full_response.strip():
                full_response = self._create_fallback_answer(context_text, query)
            
            return full_response.strip(), generation_info
            
        except asyncio.TimeoutError:
            self.logger.error("Generation timeout")
            return self._create_timeout_answer(), {"timeout": True, "generation_time": time.time() - start_time}
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            return self._create_error_answer(), {"error": str(e), "generation_time": time.time() - start_time}

    async def generate_answer(
        self,
        query: str,
        context_docs: List[Dict[str, Any]],
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> Tuple[str, Dict[str, Any]]:
        return await self.generate_answer_with_cancellation(
            query=query,
            context_docs=context_docs,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def _build_mistral_prompt(self, system_message: str, user_message: str) -> str:
        return f"""<s>[INST] {system_message}

{user_message} [/INST]"""

    def _create_fallback_answer(self, context: str, query: str) -> str:
        return f"I found some information about your query but encountered an issue generating a detailed response. Please try your question again or consult a healthcare provider for medical advice."

    def _create_timeout_answer(self) -> str:
        return "The response is taking longer than expected. Please try your question again or consult a healthcare provider for immediate medical advice."

    def _create_error_answer(self) -> str:
        return "I encountered a technical issue while processing your question. Please try again or consult a healthcare professional for medical advice."

    def _format_context(self, context_docs: List[Dict[str, Any]], query: str) -> str:
        if not context_docs:
            return "No relevant medical information found."
        
        is_relevant_retrieval = self._is_relevant_retrieval(context_docs, query)
        
        if not is_relevant_retrieval:
            return "LIMITED RELEVANT CONTEXT: The retrieved documents are not highly relevant to your specific question. The assistant will provide general medical information based on comprehensive knowledge."
        
        context_parts = []
        relevant_docs_count = 0
        
        for i, doc in enumerate(context_docs[:5], 1):
            if not self._is_doc_relevant_to_query(doc, query):
                continue
                
            content = doc['content']
            metadata = doc['metadata']
            score = doc.get('combined_score', 0)
            source = metadata.get('source_dataset', 'Unknown Source')
            
            compact_content = self._make_content_compact(content, query)
            
            context_part = f"[Source {i}: {source.upper()} - Score: {score:.3f}]\nTopic: {metadata.get('topic_title', 'Unknown')}\nContent: {compact_content}"
            context_parts.append(context_part)
            relevant_docs_count += 1
            
            if relevant_docs_count >= 3:
                break
        
        if relevant_docs_count == 0:
            return "LIMITED RELEVANT CONTEXT: No highly relevant documents found for this specific question."
        
        return "\n\n".join(context_parts)

    def _is_relevant_retrieval(self, context_docs: List[Dict], query: str) -> bool:
        if not context_docs:
            return False
        
        query_lower = query.lower()
        
        relevant_count = 0
        for doc in context_docs[:5]:
            if self._is_doc_relevant_to_query(doc, query):
                relevant_count += 1
        
        if relevant_count >= 2:
            return True
        
        avg_score = sum(doc.get('combined_score', 0) for doc in context_docs[:3]) / min(3, len(context_docs))
        if avg_score > 0.7 and relevant_count >= 1:
            return True
            
        return False

    def _is_doc_relevant_to_query(self, doc: Dict, query: str) -> bool:
        content = doc.get('content', '').lower()
        title = doc.get('metadata', {}).get('topic_title', '').lower()
        query_lower = query.lower()
        
        query_terms = self._extract_key_medical_terms(query_lower)
        
        title_match = any(term in title for term in query_terms if len(term) > 3)
        content_match = any(term in content for term in query_terms if len(term) > 3)
        
        return title_match or (content_match and len([t for t in query_terms if t in content]) >= 2)

    def _extract_key_medical_terms(self, query: str) -> List[str]:
        stop_words = {
            'what', 'are', 'the', 'symptoms', 'of', 'and', 'or', 'is', 'for', 'how', 
            'to', 'do', 'i', 'have', 'a', 'does', 'can', 'could', 'would', 'should',
            'tell', 'me', 'about', 'treatment', 'treatments', 'cause', 'causes',
            'diagnosis', 'prevention', 'medicine', 'medicines', 'drug', 'drugs'
        }
        
        words = re.findall(r'\b[a-z]{3,}\b', query.lower())
        medical_terms = [word for word in words if word not in stop_words]
        
        return medical_terms

    def _make_content_compact(self, content: str, query: str) -> str:
        content = ' '.join(content.split())
        
        if len(content) <= 400:
            return content
        
        relevant_section = self._extract_relevant_section(content, query)
        if relevant_section and len(relevant_section) > 100:
            return relevant_section
        
        if len(content) > 400:
            for pos in range(350, 450):
                if pos < len(content) and content[pos] in '.!?':
                    return content[:pos + 1]
            
            return content[:400] + "..."
        
        return content

    def _extract_relevant_section(self, content: str, query: str) -> str:
        query_lower = query.lower()
        content_lower = content.lower()
        
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        query_terms = self._extract_key_medical_terms(query_lower)
        
        scored_sentences = []
        for sentence in sentences:
            if len(sentence) < 20:
                continue
                
            sentence_lower = sentence.lower()
            score = 0
            
            for term in query_terms:
                if term in sentence_lower:
                    score += 3 if len(term) > 4 else 1
            
            medical_indicators = ['treatment', 'therapy', 'symptom', 'cause', 'diagnosis', 'prevention', 'medication']
            for indicator in medical_indicators:
                if indicator in sentence_lower:
                    score += 2
            
            if score > 0:
                scored_sentences.append((score, sentence))
        
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [s[1] for s in scored_sentences[:4]]
        
        if top_sentences:
            combined = '. '.join(top_sentences) + '.'
            if len(combined) <= 500:
                return combined
        
        return ""

    async def get_model_info(self) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/show",
                    json={"name": self.model_name}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"Failed to get model info: {response.status}"}
        except Exception as e:
            self.logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}

    async def get_model_template(self) -> str:
        if self._model_template:
            return self._model_template
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/show",
                    json={"name": self.model_name}
                ) as response:
                    if response.status == 200:
                        model_info = await response.json()
                        template = model_info.get('template', 'No template found in model info')
                        self._model_template = template
                        self.logger.info(f"Model template: {template[:200]}...")
                        return template
                    else:
                        error_msg = f"Failed to get model info: {response.status}"
                        self.logger.error(f"{error_msg}")
                        return error_msg
        except Exception as e:
            error_msg = f"Failed to get model template: {e}"
            self.logger.error(f"{error_msg}")
            return error_msg

class HTTPError(Exception):
    pass