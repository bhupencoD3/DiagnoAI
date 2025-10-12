from typing import List, Optional
import logging
import time
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from src.utils.config import settings

class EmbeddingManager:
    """Centralized embedding management with OpenAI primary + local fallback"""
    
    def __init__(self, force_local: bool = False):
        self.logger = logging.getLogger(__name__)
        self.embedding_model = "local" if force_local else "openai"
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize embedding models with OpenAI as primary"""
        try:
            if self.embedding_model == "openai" and settings.OPENAI_API_KEY:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self.logger.info(f"Using OpenAI embeddings: {settings.OPENAI_EMBEDDING_MODEL}")
                
                # Pre-initialize local model for fallback
                self.local_embedder = SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL)
                self.logger.info(f"Local fallback initialized: {settings.LOCAL_EMBEDDING_MODEL}")
                
            else:
                self.local_embedder = SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL)
                self.embedding_model = "local"
                self.logger.info(f"Using local embeddings: {settings.LOCAL_EMBEDDING_MODEL}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI, falling back to local: {e}")
            self.local_embedder = SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL)
            self.embedding_model = "local"
    
    def get_embeddings(self, texts: List[str], batch_size: int = None) -> List[List[float]]:
        """Get embeddings for multiple texts with automatic fallback"""
        if not texts:
            return []
        
        batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        all_embeddings = []
        
        if self.embedding_model == "openai":
            try:
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    
                    response = self.openai_client.embeddings.create(
                        model=settings.OPENAI_EMBEDDING_MODEL,
                        input=batch
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(batch_embeddings)
                    
                    self.logger.debug(f"Processed OpenAI batch {i//batch_size + 1}")
                
                self.logger.info(f"Generated OpenAI embeddings for {len(texts)} texts")
                return all_embeddings
                
            except Exception as e:
                self.logger.warning(f"OpenAI embedding failed, falling back to local: {e}")
                self.embedding_model = "local"
        
        # Local embeddings fallback
        try:
            if len(texts) > batch_size:
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    batch_embeddings = self.local_embedder.encode(batch).tolist()
                    all_embeddings.extend(batch_embeddings)
            else:
                all_embeddings = self.local_embedder.encode(texts).tolist()
            
            self.logger.info(f"Generated local embeddings for {len(texts)} texts")
            return all_embeddings
            
        except Exception as e:
            self.logger.error(f"All embedding methods failed: {e}")
            raise
    
    def get_single_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text"""
        return self.get_embeddings([text])[0]
    
    def get_model_info(self) -> dict:
        """Get information about the current embedding model"""
        if self.embedding_model == "openai":
            return {
                "provider": "openai",
                "model": settings.OPENAI_EMBEDDING_MODEL,
                "dimensions": settings.OPENAI_EMBEDDING_DIMENSIONS
            }
        else:
            return {
                "provider": "local",
                "model": settings.LOCAL_EMBEDDING_MODEL,
                "dimensions": settings.LOCAL_EMBEDDING_DIMENSIONS
            }
    
    def force_local_mode(self):
        """Force using local embeddings"""
        self.embedding_model = "local"
        if not hasattr(self, 'local_embedder'):
            self.local_embedder = SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL)
        self.logger.info("Forced to local embedding mode")

embedding_manager = EmbeddingManager()