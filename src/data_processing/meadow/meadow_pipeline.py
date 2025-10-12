import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

from .meadow_parser import MedicalMeadowParser
from .meadow_cleaner import MeadowCleaner
from .meadow_chunker import MeadowChunker

class MedicalMeadowPipeline:
    """Standalone pipeline for Medical Meadow QA processing"""
    
    def __init__(self):
        self.stats = {
            'start_time': None,
            'end_time': None,
            'topics_parsed': 0,
            'topics_cleaned': 0,
            'chunks_created': 0
        }
        self.parser = MedicalMeadowParser()
        self.cleaner = MeadowCleaner()
        self.chunker = MeadowChunker()
    
    def run_pipeline(self, json_file_path: str, output_dir: str = "data/processed/meadow_chunks"):
        """Run the complete Medical Meadow processing pipeline"""
        self.stats['start_time'] = datetime.now()
        logging.info("Starting Medical Meadow QA processing pipeline")
        
        try:
            logging.info("Step 1: Parsing Medical Meadow QA JSON")
            topics = self._parse_meadow_qa(json_file_path)
            
            logging.info("Step 2: Cleaning Medical Meadow topics")
            cleaned_topics = self._clean_topics(topics)
            
            logging.info("Step 3: Chunking Medical Meadow topics")
            chunks = self._chunk_topics(cleaned_topics)
            
            logging.info("Step 4: Saving Medical Meadow chunks")
            self._save_results(cleaned_topics, chunks, output_dir)
            
            self.stats['end_time'] = datetime.now()
            self._log_final_stats()
            
            logging.info("Medical Meadow QA pipeline finished successfully")
            return chunks
            
        except Exception as e:
            logging.error(f"Medical Meadow pipeline failed: {e}")
            raise
    
    def _parse_meadow_qa(self, json_file_path: str) -> List[Dict[str, Any]]:
        """Parse Medical Meadow QA data"""
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"Medical Meadow file not found: {json_file_path}")
        
        topics = self.parser.parse_medical_meadow(json_file_path)
        self.stats['topics_parsed'] = len(topics)
        logging.info(f"Parsed {len(topics)} Medical Meadow QA topics")
        return topics
    
    def _clean_topics(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean Medical Meadow topics"""
        cleaned_topics = self.cleaner.clean_all_topics(topics)
        self.stats['topics_cleaned'] = len(cleaned_topics)
        logging.info(f"Cleaned {len(cleaned_topics)} topics")
        return cleaned_topics
    
    def _chunk_topics(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Chunk Medical Meadow topics"""
        chunks = self.chunker.chunk_all_topics(topics)
        self.stats['chunks_created'] = len(chunks)
        
        if chunks and hasattr(self.chunker, 'analyze_chunk_distribution'):
            distribution = self.chunker.analyze_chunk_distribution(chunks)
            avg_size = distribution['avg_chunk_size']
            logging.info(f"Created {len(chunks)} chunks, average size: {avg_size:.1f} words")
            
            logging.info("Chunk Distribution:")
            logging.info(f"  Small (<100 words): {distribution['small_chunks_<100']} ({distribution['distribution_percentage']['small']})")
            logging.info(f"  Medium (100-300): {distribution['medium_chunks_100_300']} ({distribution['distribution_percentage']['medium']})")
            logging.info(f"  Large (300+): {distribution['large_chunks_300_plus']} ({distribution['distribution_percentage']['large']})")
        else:
            avg_size = sum(c['word_count'] for c in chunks) / len(chunks) if chunks else 0
            logging.info(f"Created {len(chunks)} chunks, average size: {avg_size:.1f} words")
        
        return chunks
    
    def _save_results(self, cleaned_topics: List[Dict[str, Any]], chunks: List[Dict[str, Any]], output_dir: str):
        """Save processing results"""
        os.makedirs(output_dir, exist_ok=True)
        
        topics_file = os.path.join(output_dir, "meadow_cleaned_topics.json")
        with open(topics_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_topics, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved cleaned topics to: {topics_file}")
        
        chunks_file = os.path.join(output_dir, "medical_meadow_chunks.json")
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved Medical Meadow chunks to: {chunks_file}")
        
        analysis_file = os.path.join(output_dir, "meadow_pipeline_analysis.json")
        
        duration = "Unknown"
        if self.stats['start_time'] and self.stats['end_time']:
            duration = str(self.stats['end_time'] - self.stats['start_time'])
        
        analysis = {
            "pipeline_stats": {
                "total_topics": len(cleaned_topics),
                "total_chunks": len(chunks),
                "chunks_per_topic": len(chunks) / len(cleaned_topics) if cleaned_topics else 0,
                "avg_chunk_size_words": sum(c['word_count'] for c in chunks) / len(chunks) if chunks else 0,
                "avg_chunk_size_chars": sum(c['char_count'] for c in chunks) / len(chunks) if chunks else 0,
                "processing_date": datetime.now().isoformat(),
                "pipeline_duration": duration
            },
            "chunk_distribution": self._calculate_chunk_distribution(chunks),
            "data_source": "Medical Meadow QA",
            "data_format": "Question-Answer",
            "chunker_config": {
                "target_chunk_size": 250,
                "min_chunk_size": 100,
                "max_chunk_size": 400,
                "chunker_type": "Enhanced Balanced Chunker"
            }
        }
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved pipeline analysis to: {analysis_file}")
    
    def _calculate_chunk_distribution(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate chunk size distribution"""
        if not chunks:
            return {}
        
        word_counts = [c['word_count'] for c in chunks]
        
        return {
            'small_chunks_<100': len([c for c in word_counts if c < 100]),
            'medium_chunks_100_300': len([c for c in word_counts if 100 <= c < 300]),
            'large_chunks_300_plus': len([c for c in word_counts if c >= 300]),
            'distribution_percentage': {
                'small': f"{(len([c for c in word_counts if c < 100])/len(word_counts)*100):.1f}%",
                'medium': f"{(len([c for c in word_counts if 100 <= c < 300])/len(word_counts)*100):.1f}%",
                'large': f"{(len([c for c in word_counts if c >= 300])/len(word_counts)*100):.1f}%"
            },
            'size_range': {
                'min': min(word_counts),
                'max': max(word_counts),
                'avg': sum(word_counts) / len(word_counts)
            }
        }
    
    def _log_final_stats(self):
        """Log final pipeline statistics"""
        duration = "Unknown"
        if self.stats['start_time'] and self.stats['end_time']:
            duration = str(self.stats['end_time'] - self.stats['start_time'])
        
        logging.info("Medical Meadow QA Pipeline Statistics:")
        logging.info(f"  Total duration: {duration}")
        logging.info(f"  Topics parsed: {self.stats['topics_parsed']}")
        logging.info(f"  Topics cleaned: {self.stats['topics_cleaned']}")
        logging.info(f"  Chunks created: {self.stats['chunks_created']}")
        if self.stats['topics_parsed'] > 0:
            chunks_per_topic = self.stats['chunks_created'] / self.stats['topics_parsed']
            logging.info(f"  Chunks per topic: {chunks_per_topic:.2f}")