# scripts/run_context_preserving_pipeline.py
import sys
import os
import json
import logging
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_processing.xml_parser import MedlinePlusXMLParser
from src.data_processing.text_cleaner import MedicalTextCleaner
from data_processing.medlineplus_chunker import StreamingChunker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class ContextPreservingPipeline:
    """Pipeline that preserves maximum context and avoids aggressive splitting"""
    
    def __init__(self):
        self.stats = {
            'start_time': None,
            'end_time': None,
            'topics_parsed': 0,
            'topics_cleaned': 0,
            'chunks_created': 0
        }
    
    def run_pipeline(self, xml_file_path: str, output_dir: str = "data/processed/chunks_context"):
        """Run the context-preserving pipeline"""
        self.stats['start_time'] = datetime.now()
        logger.info("🚀 STARTING CONTEXT-PRESERVING PIPELINE")
        
        try:
            # Step 1: Parse XML with structure preservation
            logger.info("📖 Step 1: Parsing XML with structure preservation...")
            topics = self._parse_xml_data(xml_file_path)
            
            # Step 2: Clean topics minimally
            logger.info("🧹 Step 2: Cleaning topics minimally...")
            cleaned_topics = self._clean_topics(topics)
            
            # Step 3: Chunk with context preservation
            logger.info("✂️ Step 3: Chunking with context preservation...")
            chunks = self._chunk_topics_context_preserving(cleaned_topics)
            
            # Step 4: Save results
            logger.info("💾 Step 4: Saving context-rich chunks...")
            self._save_results(cleaned_topics, chunks, output_dir)
            
            # Final stats
            self.stats['end_time'] = datetime.now()
            self._log_final_stats()
            
            logger.info("✅ CONTEXT-PRESERVING PIPELINE FINISHED SUCCESSFULLY!")
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise
    
    def _parse_xml_data(self, xml_file_path: str) -> list:
        """Parse XML file"""
        if not os.path.exists(xml_file_path):
            raise FileNotFoundError(f"XML file not found: {xml_file_path}")
        
        parser = MedlinePlusXMLParser()
        all_topics = []
        
        for batch in parser.parse_health_topics_batch(xml_file_path, batch_size=100):
            all_topics.extend(batch)
            logger.info(f"📦 Parsed {len(all_topics)} topics...")
        
        self.stats['topics_parsed'] = len(all_topics)
        logger.info(f"✅ Parsed {len(all_topics)} total topics")
        return all_topics
    
    def _clean_topics(self, topics: list) -> list:
        """Clean topics with minimal changes"""
        cleaner = MedicalTextCleaner()
        cleaned_topics = []
        
        logger.info("🧹 Cleaning topics minimally...")
        for i, topic in enumerate(topics):
            cleaned_topic = cleaner.clean_topic(topic)
            cleaned_topics.append(cleaned_topic)
            
            if (i + 1) % 100 == 0:
                logger.info(f"  Cleaned {i + 1} topics...")
        
        self.stats['topics_cleaned'] = len(cleaned_topics)
        logger.info(f"✅ Cleaned {len(cleaned_topics)} topics")
        return cleaned_topics
    
    def _chunk_topics_context_preserving(self, topics: list) -> list:
        """Chunk topics with maximum context preservation"""
        # Use large chunk size to preserve context
        chunker = StreamingChunker(chunk_size=1500, chunk_overlap=300)
        all_chunks = []
        
        logger.info("🔍 Chunking with context preservation...")
        
        for i, topic in enumerate(topics):
            if i % 100 == 0:
                logger.info(f"  Processing topic {i+1}/{len(topics)}...")
            
            for chunk in chunker.process_topic_streaming(topic):
                if chunk:
                    all_chunks.append(chunk)
        
        self.stats['chunks_created'] = len(all_chunks)
        
        # Analyze chunk sizes
        if all_chunks:
            avg_size = sum(c['word_count'] for c in all_chunks) / len(all_chunks)
            logger.info(f"✅ Created {len(all_chunks)} chunks, average size: {avg_size:.1f} words")
        
        return all_chunks
    
    def _save_results(self, cleaned_topics: list, chunks: list, output_dir: str):
        """Save results"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save cleaned topics
        topics_file = os.path.join(output_dir, "cleaned_topics.json")
        with open(topics_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_topics, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved cleaned topics to: {topics_file}")
        
        # Save chunks
        chunks_file = os.path.join(output_dir, "medical_chunks_context.json")
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Saved context-rich chunks to: {chunks_file}")
        
        # Save simple analysis
        analysis_file = os.path.join(output_dir, "context_analysis.json")
        analysis = {
            "total_topics": len(cleaned_topics),
            "total_chunks": len(chunks),
            "chunks_per_topic": len(chunks) / len(cleaned_topics),
            "avg_chunk_size_words": sum(c['word_count'] for c in chunks) / len(chunks) if chunks else 0,
            "avg_chunk_size_chars": sum(c['char_count'] for c in chunks) / len(chunks) if chunks else 0,
            "processing_date": datetime.now().isoformat()
        }
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        logger.info(f"📊 Saved context analysis to: {analysis_file}")
    
    def _log_final_stats(self):
        """Log final statistics"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        logger.info("📊 PIPELINE STATISTICS:")
        logger.info(f"  Total duration: {duration}")
        logger.info(f"  Topics parsed: {self.stats['topics_parsed']}")
        logger.info(f"  Topics cleaned: {self.stats['topics_cleaned']}")
        logger.info(f"  Chunks created: {self.stats['chunks_created']}")
        logger.info(f"  Chunks per topic: {self.stats['chunks_created'] / self.stats['topics_parsed']:.2f}")

def main():
    """Run the context-preserving pipeline"""
    XML_FILE_PATH = "data/raw/mplus_topics_2025-10-01.xml"
    OUTPUT_DIR = "data/processed/chunks"
    
    pipeline = ContextPreservingPipeline()
    pipeline.run_pipeline(XML_FILE_PATH, OUTPUT_DIR)

if __name__ == "__main__":
    main()