import sys
import os
import json
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.config import settings, validate_settings
from src.rag.vector_store import MedicalVectorStore
from src.rag.retriever import MedicalRetriever

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_vector_store():
    """Initialize the vector store with medical data using consistent embeddings"""
    validate_settings()

    vector_store = MedicalVectorStore()

    try:
        with open(settings.CHUNKS_PATH, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        logger.info(f"Loaded {len(chunks)} chunks for vector store")
        
        model_info = vector_store.embedding_manager.get_model_info()
        logger.info(f"Using {model_info['provider']} embeddings: {model_info['model']} ({model_info['dimensions']}D)")

        vector_store.add_documents(chunks)
        
        stats = vector_store.get_collection_stats()
        logger.info(f"Vector store setup completed: {stats['document_count']} documents")
        logger.info(f"Provider: {stats['embedding_provider']}")
        logger.info(f"Model: {stats['embedding_model']}")
        logger.info(f"Dimensions: {stats['embedding_dimensions']}")

        retriever = MedicalRetriever(vector_store)

        test_queries = [
            "What are the symptoms of diabetes?",
            "How to treat high blood pressure?",
            "What causes abdominal pain?"
        ]

        logger.info("Testing retrieval...")
        for query in test_queries:
            results = retriever.retrieve(query)
            metrics = retriever.get_retrieval_metrics(query, results)
            logger.info(f"'{query}' -> {len(results)} results, avg score: {metrics['avg_combined_score']:.3f}")

    except Exception as e:
        logger.error(f"Vector store setup failed: {e}")
        raise

if __name__ == "__main__":
    setup_vector_store()