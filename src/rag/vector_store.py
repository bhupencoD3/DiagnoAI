import chromadb
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import time
import uuid

from src.utils.config import settings
from .embeddings import EmbeddingManager

class MedicalVectorStore:
    def __init__(self, use_local_embeddings: bool = None):
        self.logger = logging.getLogger(__name__)
        
        self.embedding_manager = EmbeddingManager(force_local=use_local_embeddings or settings.USE_LOCAL_EMBEDDINGS)
        self.model_info = self.embedding_manager.get_model_info()
        
        self.source_weights = {
            'medline_plus': 1.5,
            'medical_meadow': 1.0,
            'fda_drugs': 1.3,
            'unknown': 1.0
        }

        self.client = chromadb.PersistentClient(path=settings.VECTOR_STORE_PATH)
        self.primary_collection = self._get_or_create_collection()
        
        self.logger.info(f"Vector store initialized with {self.model_info['provider']} embeddings")
    
    def _get_or_create_collection(self):
        """Get or create collection with proper embedding metadata"""
        try:
            collection = self.client.get_collection(settings.COLLECTION_NAME)
            
            if not self._validate_collection_compatibility(collection):
                self.logger.warning("Collection embedding mismatch, recreating...")
                self.client.delete_collection(settings.COLLECTION_NAME)
                raise ValueError("Embedding dimension mismatch")
                
            return collection
            
        except Exception as e:
            self.logger.info(f"Creating new collection: {e}")
            return self.client.create_collection(
                name=settings.COLLECTION_NAME,
                metadata={
                    "description": "Medical knowledge base with hybrid retrieval",
                    "embedding_provider": self.model_info["provider"],
                    "embedding_model": self.model_info["model"],
                    "embedding_dimensions": self.model_info["dimensions"],
                    "created_at": time.time(),
                    "version": "2.1",
                    "source_weights": str(self.source_weights)
                }
            )
    
    def _validate_collection_compatibility(self, collection) -> bool:
        """Validate that collection matches current embedding model"""
        try:
            metadata = collection.metadata
            if not metadata:
                return False
                
            stored_dims = metadata.get("embedding_dimensions")
            current_dims = self.model_info["dimensions"]
            
            if stored_dims and int(stored_dims) != current_dims:
                self.logger.error(f"Embedding dimension mismatch: collection has {stored_dims}, current model has {current_dims}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.warning(f"Could not validate collection compatibility: {e}")
            return False
    
    def add_documents(self, chunks: List[Dict[str, Any]]):
        """Add documents to vector store with enhanced metadata"""
        if not chunks:
            self.logger.warning("No chunks to add to vector store")
            return
        
        documents = []
        metadatas = []
        ids = []
        seen_ids = set()
        
        for chunk in chunks:
            try:
                content = chunk.get('content') or chunk.get('text') or chunk.get('document') or ''
                if not content or not content.strip():
                    self.logger.debug(f"Skipping chunk with no content: {chunk.get('chunk_id', 'unknown')}")
                    continue
                
                chunk_id = chunk.get('chunk_id') or str(uuid.uuid4())
                if chunk_id in seen_ids:
                    counter = 1
                    new_chunk_id = f"{chunk_id}_{counter}"
                    while new_chunk_id in seen_ids:
                        counter += 1
                        new_chunk_id = f"{chunk_id}_{counter}"
                    chunk_id = new_chunk_id
                seen_ids.add(chunk_id)
                
                metadata = {
                    'topic_title': str(chunk.get('topic_title') or chunk.get('brand_name') or chunk.get('title') or 'Untitled'),
                    'topic_id': str(chunk.get('topic_id') or chunk.get('doc_id') or chunk.get('set_id') or 'unknown'),
                    'chunk_number': int(chunk.get('chunk_number', 1)),
                    'word_count': int(chunk.get('word_count', len(content.split()))),
                    'quality_score': float(chunk.get('quality_score', 50)),
                    'source_dataset': str(chunk.get('source_dataset', 'unknown')),
                    'content_type': 'primary',
                    'synonyms': '|'.join(chunk.get('synonyms', [])) or 'none',
                    'mesh_terms': '|'.join(chunk.get('mesh_terms', [])) or 'none',
                    'search_terms': '|'.join(chunk.get('search_terms', [])) or 'none',
                    'source_url': str(chunk.get('source_url', '')),
                    'medical_concepts': '|'.join(chunk.get('medical_concepts', [])) or 'none',
                    'has_structured_content': bool(chunk.get('has_structured_content', False)),
                    'is_qa_format': bool(chunk.get('qa_format', False)),
                    'brand_name': str(chunk.get('brand_name', '')),
                    'generic_name': str(chunk.get('metadata', {}).get('generic_name', '')),
                    'product_type': str(chunk.get('metadata', {}).get('product_type', '')),
                    'route': str(chunk.get('metadata', {}).get('route', ''))
                }
                
                metadata['content_quality_tier'] = self._get_quality_tier(metadata['quality_score'])
                
                documents.append(content)
                metadatas.append(metadata)
                ids.append(chunk_id)
                
            except Exception as e:
                self.logger.warning(f"Failed to process chunk {chunk.get('chunk_id', 'unknown')}: {e}")
                continue
        
        if not documents:
            self.logger.error("No valid documents to add after processing")
            return
        
        self.logger.info(f"Processing {len(documents)} valid documents")
        
        batch_size = settings.EMBEDDING_BATCH_SIZE
        total_added = 0
        
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            try:
                embeddings = self.embedding_manager.get_embeddings(batch_docs)
                
                self.primary_collection.add(
                    embeddings=embeddings,
                    documents=batch_docs,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                
                total_added += len(batch_docs)
                self.logger.info(f"Added batch {i//batch_size + 1}")
                
            except Exception as e:
                self.logger.error(f"Failed to add batch starting at {i}: {e}")
                self.logger.info(f"Skipped {len(batch_docs)} chunks in failed batch")
        
        source_counts = {}
        for metadata in metadatas[:total_added]:
            source = metadata.get('source_dataset', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        self.logger.info(f"Added {total_added} documents to vector store")
        self.logger.info(f"Source distribution: {source_counts}")
        
    def _get_quality_tier(self, quality_score: float) -> str:
        """Convert quality score to tier for filtering"""
        if quality_score >= 80:
            return "excellent"
        elif quality_score >= 60:
            return "good"
        elif quality_score >= 40:
            return "fair"
        else:
            return "poor"
    
    def hybrid_search(self, query: str, n_results: int = None, alpha: float = None) -> List[Dict[str, Any]]:
        """Enhanced hybrid search with source-based weighting"""
        n_results = n_results or settings.DEFAULT_N_RESULTS
        alpha = alpha or settings.HYBRID_SEARCH_ALPHA
        
        try:
            start_time = time.time()
            
            query_embedding = self.embedding_manager.get_single_embedding(query)
            
            semantic_results = self.primary_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 4,
                include=['documents', 'metadatas', 'distances'],
            )
            
            boosted_results = self._apply_source_aware_boosting(semantic_results, query)
            reranked = self._rerank_results_with_source_priority(boosted_results, query, alpha)
            
            search_time = time.time() - start_time
            self.logger.info(f"Hybrid search for '{query}' took {search_time:.2f}s, found {len(reranked)} results")
            
            return reranked[:n_results]
            
        except Exception as e:
            self.logger.error(f"Hybrid search failed: {e}")
            return self.simple_search(query, n_results)
    
    def _apply_source_aware_boosting(self, results: Dict, query: str) -> List[Dict[str, Any]]:
        """Apply source-based boosting with medical matching"""
        query_terms = set(query.lower().split())
        boosted_results = []
        
        medical_concept_pairs = {
            'symptoms': ['symptom', 'sign', 'manifestation', 'presentation', 'experience', 'feel'],
            'treatment': ['treatment', 'therapy', 'medication', 'management', 'cure', 'drug'],
            'causes': ['cause', 'etiology', 'reason', 'risk factor', 'trigger'],
            'diagnosis': ['diagnosis', 'test', 'examination', 'screening', 'detect'],
            'prevention': ['prevention', 'prevent', 'avoid', 'protection', 'prophylaxis']
        }
        
        for i in range(len(results['documents'][0])):
            document = results['documents'][0][i]
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]
            
            score = 1.0 / (1.0 + distance)
            
            source = metadata.get('source_dataset', 'unknown')
            source_boost = self.source_weights.get(source, 1.0)
            score *= source_boost
            
            for query_concept, related_terms in medical_concept_pairs.items():
                if any(term in query.lower() for term in [query_concept] + related_terms):
                    doc_lower = document.lower()
                    if any(term in doc_lower for term in related_terms):
                        score *= 1.5
                        break
            
            synonyms = metadata.get('synonyms', '').lower().split('|')
            mesh_terms = metadata.get('mesh_terms', '').lower().split('|')
            search_terms = metadata.get('search_terms', '').lower().split('|')
            medical_concepts = metadata.get('medical_concepts', '').lower().split('|')
            
            all_terms = set(synonyms + mesh_terms + search_terms + medical_concepts)
            matching_terms = query_terms.intersection(all_terms)
            
            if matching_terms:
                score *= (1.0 + 0.2 * len(matching_terms))
            
            quality_score = metadata.get('quality_score', 50)
            score *= (0.9 + (quality_score / 100.0 * 0.2))
            
            if metadata.get('has_structured_content', False):
                score *= 1.15
            
            boosted_results.append({
                'content': document,
                'metadata': metadata,
                'score': score,
                'distance': distance
            })
        
        return boosted_results
    
    def _rerank_results_with_source_priority(self, results: List[Dict], query: str, alpha: float) -> List[Dict]:
        """Enhanced re-ranking with source priority"""
        if not results:
            return []
        
        for result in results:
            quality_score = result['metadata'].get('quality_score', 50) / 100.0
            semantic_score = result['score']
            source = result['metadata'].get('source_dataset', 'unknown')
            
            source_final_boost = self.source_weights.get(source, 1.0)
            
            medical_concepts = result['metadata'].get('medical_concepts', '').split('|')
            concept_bonus = 1.0
            if any(concept in query.lower() for concept in medical_concepts if concept):
                concept_bonus = 1.3
            
            combined_score = (alpha * semantic_score * concept_bonus * source_final_boost) + ((1 - alpha) * quality_score)
            result['combined_score'] = combined_score
        
        return sorted(results, key=lambda x: x['combined_score'], reverse=True)
    
    def simple_search(self, query: str, n_results: int = None) -> List[Dict[str, Any]]:
        """Simple semantic search as fallback"""
        n_results = n_results or settings.DEFAULT_N_RESULTS
        
        try:
            query_embedding = self.embedding_manager.get_single_embedding(query)
            
            results = self.primary_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'score': 1.0 / (1.0 + results['distances'][0][i]),
                    'combined_score': 1.0 / (1.0 + results['distances'][0][i])
                })
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Simple search also failed: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection"""
        try:
            count = self.primary_collection.count()
            metadata = self.primary_collection.metadata or {}
            
            all_results = self.primary_collection.get(include=['metadatas'])
            sources = {}
            for meta in all_results['metadatas']:
                source = meta.get('source_dataset', 'unknown')
                sources[source] = sources.get(source, 0) + 1
            
            return {
                "document_count": count,
                "embedding_provider": metadata.get("embedding_provider", "unknown"),
                "embedding_model": metadata.get("embedding_model", "unknown"),
                "embedding_dimensions": metadata.get("embedding_dimensions", "unknown"),
                "collection_name": settings.COLLECTION_NAME,
                "version": metadata.get("version", "1.0"),
                "source_distribution": sources
            }
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}