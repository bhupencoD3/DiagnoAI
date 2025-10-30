import requests
import logging
import time
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Callable
import re
import json

from src.utils.config import settings

class MedicalPromptTemplate:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def build_mistral_prompt(self, query: str, context: str) -> str:
        system_message = """You are a medical information provider. Deliver clear, factual explanations in a direct, structured format.

STRICT FORMATTING RULES:
- ALWAYS use **bold headers** for main sections
- ALWAYS use ONLY • bullet points - NO paragraphs or explanatory text before bullet points
- Each header must be immediately followed by bullet points, not paragraphs
- ALWAYS include the medical disclaimer at the end
- Keep bullet points concise and focused
- Create specific, action-oriented headers
- Organize information in the most logical order for the question

CONTENT GUIDELINES:
1. Start each section directly with bullet points - no introductory sentences
2. Make headers specific to the content that follows
3. Focus on the most relevant information for the question
4. Avoid repeating information across sections
5. Keep explanations within the bullet points themselves
6. Be direct and avoid unnecessary words

FORMATTING EXAMPLES:

CORRECT:
**Common Diabetes Symptoms**
• Increased thirst and frequent urination
• Unexplained fatigue and blurred vision
• Slow-healing cuts and tingling in extremities

INCORRECT:
**Understanding Diabetes Symptoms**
The symptoms of diabetes can vary from person to person, but there are several key signs to look out for. These include:
• Increased thirst
• Frequent urination

HEADER CREATION:
- Make headers describe the specific content that follows
- Use action-oriented language when possible
- Ensure each header covers a distinct aspect of the topic
- Avoid vague or overly broad headers

*Medical Disclaimer: This information is for educational purposes only and is not a substitute for professional medical advice. Always consult with a healthcare provider for any health concerns or before making any medical decisions.*"""

        user_message = f"""MEDICAL CONTEXT:
    {context}

    QUESTION: {query}

    Provide a direct, structured response using ONLY bullet points under each header with no introductory paragraphs:

    ANSWER:"""

        return f"""<s>[INST] {system_message}

    {user_message} [/INST]"""

class GrokClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = settings.GROK_API_KEY
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model_name = "llama-3.3-70b-versatile"
        self.prompt_template = MedicalPromptTemplate()
        self.total_requests = 0
        
    async def health_check(self) -> bool:
        """Check if Grok API is accessible"""
        try:
            response = requests.get(
                f"{self.base_url.replace('/chat/completions', '/models')}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            if response.status_code == 200:
                self.logger.info("Grok API is healthy")
                return True
            else:
                self.logger.error(f"Grok API health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Grok health check failed: {e}")
            return False

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
            
            # Use your existing prompt template
            prompt = self.prompt_template.build_mistral_prompt(query, context_text)
            
            self.logger.info(f"Sending request to Grok {self.model_name} (Request ID: {request_id})")
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a medical assistant that provides perfectly formatted answers using Markdown with bold headers and bullet points only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            full_response = ""
            
            try:
                # Check for cancellation before making the request
                if cancellation_check and cancellation_check():
                    self.logger.info(f"Generation cancelled before request for {request_id}")
                    return "Generation cancelled by user", {"cancelled": True, "generation_time": time.time() - start_time}
                
                response = await asyncio.wait_for(
                    self._make_grok_request(messages, temperature, max_tokens),
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    self.logger.error(f"Grok API error: {response.status_code} - {error_text}")
                    return self._create_error_answer(), {"error": f"API error: {response.status_code}", "generation_time": time.time() - start_time}
                
                data = response.json()
                full_response = data["choices"][0]["message"]["content"]
                
                # Clean up the response formatting
                full_response = self._clean_response_formatting(full_response)
                
            except asyncio.TimeoutError:
                self.logger.error(f"Grok request timeout for {request_id}")
                return self._create_timeout_answer(), {"timeout": True, "generation_time": time.time() - start_time}
            except Exception as e:
                self.logger.error(f"Grok API call failed: {e}")
                return self._create_error_answer(), {"error": str(e), "generation_time": time.time() - start_time}
            
            generation_time = time.time() - start_time
            
            generation_info = {
                "model": self.model_name,
                "tokens_used": data.get("usage", {}).get("total_tokens", 0),
                "generation_time": generation_time,
                "cancelled": False,
                "request_id": request_id
            }
            
            self.total_requests += 1
            
            self.logger.info(f"Generated {len(full_response)} chars in {generation_time:.2f}s for request {request_id}")
            
            if not full_response.strip():
                full_response = self._create_fallback_answer(context_text, query)
            
            return full_response.strip(), generation_info
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            return self._create_error_answer(), {"error": str(e), "generation_time": time.time() - start_time}

    def _clean_response_formatting(self, response: str) -> str:
        """Clean up formatting issues in the response"""
        # Remove code blocks if present
        response = response.replace('```', '')
        
        # Fix: Remove bullet points before headers
        response = re.sub(r'^•\s*\*\*', '**', response, flags=re.MULTILINE)
        
        # Standardize bullet points
        response = re.sub(r'^\s*[\*\+-]\s+', '• ', response, flags=re.MULTILINE)
        
        # Ensure headers are on their own line
        response = re.sub(r'\*\*([^*]+)\*\*', r'\n**\1**\n', response)
        
        # Remove excessive line breaks
        response = re.sub(r'\n\s*\n', '\n\n', response)
        
        # Clean up any remaining formatting issues
        response = re.sub(r'•\s+•', '•', response)
        
        return response.strip()

    async def _make_grok_request(self, messages: List[Dict], temperature: float, max_tokens: int):
        """Make async HTTP request to Grok API"""
        loop = asyncio.get_event_loop()
        
        def _sync_request():
            return requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": 0.9,
                    "stream": False
                },
                timeout=45
            )
        
        return await loop.run_in_executor(None, _sync_request)

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
            return "LIMITED RELEVANT CONTEXT: The retrieved documents are not highly relevant to your specific question."
        
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
            return {
                "model": self.model_name,
                "provider": "grok",
                "description": "Llama 3.3 70B Versatile - Excellent for medical QA",
                "context_window": "131K tokens",
                "max_completion_tokens": "32K tokens",
                "capabilities": ["Medical reasoning", "Structured formatting", "Information extraction"]
            }
        except Exception as e:
            self.logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "current_model": self.model_name,
            "provider": "grok"
        }

class HTTPError(Exception):
    pass