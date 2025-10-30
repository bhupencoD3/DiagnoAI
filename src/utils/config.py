import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import validator

class Settings(BaseSettings):
    # Replicate Configuration
    REPLICATE_API_TOKEN: str  
    REPLICATE_MODEL: str = "mistralai/mistral-7b-v0.2" 
    LLM_PROVIDER: str ="grok" 
    
    # Ollama Configuration (keep for fallback)
    OLLAMA_HOST: str = "localhost"
    OLLAMA_PORT: int = 11434
    OLLAMA_MODEL: str = "mistral:7b-instruct"  

    # OpenAI Configuration for embeddings
    OPENAI_API_KEY: str  # Remove default value
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIMENSIONS: int = 1536

    GROK_API_KEY: str
    # Huggingface
    HF_TOKEN: Optional[str] = None

    # Embedding Configuration
    USE_LOCAL_EMBEDDINGS: bool = False
    LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    LOCAL_EMBEDDING_DIMENSIONS: int = 384

    # Vector Store Configuration
    VECTOR_STORE_PATH: str = "data/vector_store"
    COLLECTION_NAME: str = "medical_knowledge"

    # LLM Configuration
    LLM_PROVIDER: Literal['ollama', 'openai', 'grok'] = "grok"
    OPENAI_LLM_MODEL: str = "gpt-3.5-turbo"
    OLLAMA_TIMEOUT: int = 180
    REPLICATE_TIMEOUT: int = 120  # Reduced for Phi-3 speed

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # RAG Configuration
    DEFAULT_N_RESULTS: int = 5
    HYBRID_SEARCH_ALPHA: float = 0.7
    MAX_SAME_TOPIC_RESULTS: int = 2

    # Data Paths
    RAW_DATA_PATH: str = "data/raw/mplus_topics_2025-10-01.xml"
    PROCESSED_DATA_PATH: str = "data/processed/health_topics.json"
    CHUNKS_PATH: str = "data/processed/chunks/medical_chunks_cleaned.json"

    # Performance
    EMBEDDING_BATCH_SIZE: int = 100
    MAX_RETRY_ATTEMPTS: int = 3

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/api.log"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("OPENAI_API_KEY")
    def validate_openai_key(cls, v):
        if not v or v == "your-openai-api-key-here":
            raise ValueError("OPENAI_API_KEY must be set in environment variables or .env file")
        return v

    @validator("REPLICATE_API_TOKEN")
    def validate_replicate_token(cls, v):
        if not v or v == "your-replicate-api-token-here":
            raise ValueError("REPLICATE_API_TOKEN must be set in environment variables or .env file")
        return v
    
    @validator("GROK_API_KEY")
    def validate_grok_key(cls, v):
        if not v:
            raise ValueError("GROK_API_KEY must be set in environment variables or .env file")
        return v

# Global settings instance
settings = Settings()

def validate_settings():
    """Validate all settings are properly configured"""
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/processed/chunks",
        "data/vector_store",
        "logs"
    ]

    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)

    # Test Replicate connection if using Replicate LLM
    if settings.LLM_PROVIDER == 'replicate':
        try:
            import replicate
            print(f"Testing Replicate with model: {settings.REPLICATE_MODEL}")
            print(f"Token starts with: {settings.REPLICATE_API_TOKEN[:10]}...")
            
            client = replicate.Client(api_token=settings.REPLICATE_API_TOKEN)
            # Test connection by listing models
            models = client.models.list()
            print(f"Replicate API configured successfully. Found {len(list(models))} models")
        except Exception as e:
            raise ConnectionError(f"Replicate API connection failed: {e}")

    # Test Ollama connection if using Ollama LLM (fallback)
    elif settings.LLM_PROVIDER == 'ollama':
        try:
            import requests
            response = requests.get(f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}/api/tags", timeout=10)
            if response.status_code != 200:
                raise ConnectionError(f"Ollama server not accessible at {settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}")
            
            models = response.json().get('models', [])
            model_names = [model['name'] for model in models]
            if settings.OLLAMA_MODEL not in model_names:
                print(f"Warning: Model '{settings.OLLAMA_MODEL}' not found in Ollama. Available models: {model_names}")
                
        except Exception as e:
            raise ConnectionError(f"Ollama connection failed: {e}")

    # Test OpenAI connection if using OpenAI embeddings
    if not settings.USE_LOCAL_EMBEDDINGS:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            client.models.list()
            print("OpenAI embeddings configured successfully")
        except Exception as e:
            raise ValueError(f"OpenAI API key validation failed: {e}")

    print("All settings validated successfully")
    return True