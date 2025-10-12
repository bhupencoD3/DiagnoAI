import sys
import os
import json
import logging
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.rag.vector_store import MedicalVectorStore
from src.rag.retriever import MedicalRetriever
from src.utils.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class ComprehensiveChunksIngestor:
    def __init__(self):
        self.stats = {
            'start_time': None,
            'end_time': None,
            'chunks_loaded': 0,
            'vector_docs': 0
        }
    
    def ingest_comprehensive_chunks(self, comprehensive_chunks_path: str = None):
        self.stats['start_time'] = datetime.now()
        logger.info("Starting comprehensive chunks ingestion")
        
        try:
            logger.info("Step 1: Loading comprehensive chunks...")
            chunks = self._load_comprehensive_chunks(comprehensive_chunks_path)
            
            logger.info("Step 2: Building vector store...")
            vector_store = self._build_vector_store(chunks)
            
            logger.info("Step 3: Testing retrieval...")
            self._test_retrieval(vector_store)
            
            self.stats['end_time'] = datetime.now()
            self._log_final_stats()
            
            logger.info("Comprehensive chunks ingestion completed successfully!")
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            raise
    
    def _load_comprehensive_chunks(self, chunks_file_path: str = None) -> list:
        if chunks_file_path is None:
            chunks_file_path = "data/processed/medical_knowledge_base_v2.json.json"
        
        if not os.path.exists(chunks_file_path):
            raise FileNotFoundError(f"Comprehensive chunks file not found: {chunks_file_path}")
        
        logger.info(f"Loading comprehensive chunks from: {chunks_file_path}")
        
        if chunks_file_path.endswith('.jsonl'):
            chunks = []
            with open(chunks_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        chunk = json.loads(line.strip())
                        chunks.append(chunk)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON at line {line_num}: {e}")
                        continue
        else:
            with open(chunks_file_path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
        
        self.stats['chunks_loaded'] = len(chunks)
        logger.info(f"Loaded {len(chunks)} comprehensive chunks")
        
        meadow_chunks = [c for c in chunks if c.get('source_dataset') == 'medical_meadow']
        medline_chunks = [c for c in chunks if c.get('source_dataset') == 'medline_plus']
        fda_chunks = [c for c in chunks if c.get('source_dataset') == 'fda_drugs']
        unknown_source = [c for c in chunks if not c.get('source_dataset')]
        
        logger.info("Dataset Composition:")
        logger.info(f"  Medical Meadow: {len(meadow_chunks)} chunks")
        logger.info(f"  Medline Plus: {len(medline_chunks)} chunks")
        logger.info(f"  FDA Drugs: {len(fda_chunks)} chunks")
        if unknown_source:
            logger.info(f"  Unknown source: {len(unknown_source)} chunks")
        
        if fda_chunks:
            no_content_fda = [c for c in fda_chunks if not c.get('content')]
            duplicate_ids = {}
            for c in fda_chunks:
                chunk_id = c.get('chunk_id')
                if chunk_id:
                    duplicate_ids[chunk_id] = duplicate_ids.get(chunk_id, 0) + 1
            
            duplicate_ids = {k: v for k, v in duplicate_ids.items() if v > 1}
            
            logger.info(f"FDA Chunks Debug:")
            logger.info(f"  FDA chunks with no content: {len(no_content_fda)}")
            logger.info(f"  Duplicate chunk IDs: {len(duplicate_ids)}")
            if duplicate_ids:
                logger.info(f"  Duplicate IDs: {list(duplicate_ids.keys())[:5]}")
        
        return chunks
    
    def _build_vector_store(self, chunks: list) -> MedicalVectorStore:
        if os.path.exists(settings.VECTOR_STORE_PATH):
            logger.info("Clearing existing vector store...")
            import shutil
            shutil.rmtree(settings.VECTOR_STORE_PATH)
        
        vector_store = MedicalVectorStore()
        
        logger.info(f"Adding {len(chunks)} comprehensive chunks to vector store...")
        
        batch_size = 1000
        successful_batches = 0
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            try:
                vector_store.add_documents(batch)
                successful_batches += 1
                logger.info(f"Processed batch {successful_batches}: {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")
            except Exception as e:
                logger.error(f"Failed to process batch starting at {i}: {e}")
                individual_success = 0
                for j, chunk in enumerate(batch):
                    try:
                        vector_store.add_documents([chunk])
                        individual_success += 1
                    except Exception as chunk_error:
                        logger.warning(f"Failed to add chunk {i+j}: {chunk_error}")
                logger.info(f"Recovered {individual_success}/{len(batch)} chunks from failed batch")
        
        self.stats['vector_docs'] = len(chunks)
        
        stats = vector_store.get_collection_stats()
        logger.info(f"Vector store built successfully!")
        logger.info(f"Documents: {stats['document_count']}")
        logger.info(f"Embeddings: {stats['embedding_provider']} ({stats['embedding_model']})")
        logger.info(f"Location: {settings.VECTOR_STORE_PATH}")
        
        return vector_store
    
    def _test_retrieval(self, vector_store: MedicalVectorStore):
        retriever = MedicalRetriever(vector_store)
        
        test_queries = [
            "What are the symptoms and treatment for diabetes?",
            "How to manage high blood pressure with lifestyle changes?",
            "What causes chest pain and when to seek emergency care?",
            "COVID-19 prevention methods and vaccination",
            "Mental health strategies for anxiety and depression"
        ]
        
        logger.info("Running comprehensive retrieval tests...")
        
        for i, query in enumerate(test_queries, 1):
            try:
                results = retriever.retrieve(query, top_k=3)
                metrics = retriever.get_retrieval_metrics(query, results)
                
                logger.info(f"Test {i}: '{query}'")
                logger.info(f"Results: {len(results)}, avg score: {metrics['avg_combined_score']:.3f}")
                
                if results:
                    sources = {}
                    for result in results[:3]:
                        source = result.get('source_dataset', 'unknown')
                        sources[source] = sources.get(source, 0) + 1
                    
                    logger.info(f"Sources: {dict(sources)}")
                    
                    top_result = results[0]
                    preview = top_result['content'][:120] + "..." if len(top_result['content']) > 120 else top_result['content']
                    source = top_result.get('source_dataset', 'unknown')
                    logger.info(f"Top result [{source}]: {preview}")
                    
            except Exception as e:
                logger.error(f"Retrieval test failed for '{query}': {e}")
    
    def _log_final_stats(self):
        duration = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("Comprehensive Ingestion Statistics:")
        logger.info(f"Total duration: {duration}")
        logger.info(f"Comprehensive chunks loaded: {self.stats['chunks_loaded']}")
        logger.info(f"Vector store documents: {self.stats['vector_docs']}")
        logger.info(f"Vector store location: {settings.VECTOR_STORE_PATH}")
        logger.info(f"Combined knowledge: Medical Meadow + Medline Plus")

def main():
    COMPREHENSIVE_CHUNKS_PATH = "data/processed/medical_knowledge_base_v2.json"
    
    ingestor = ComprehensiveChunksIngestor()
    ingestor.ingest_comprehensive_chunks(COMPREHENSIVE_CHUNKS_PATH)

if __name__ == "__main__":
    main()