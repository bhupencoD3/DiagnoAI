import json
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_processing.text_cleaner import MedicalTextCleaner
from src.data_processing.chunker import StreamingChunker

def save_quality_metrics(quality_scores, total_topics, total_chunks, output_file):
    """Save comprehensive quality metrics"""
    metrics = {
        "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": "MedlinePlus XML",
        "summary": {
            "total_topics": total_topics,
            "total_chunks": total_chunks,
            "average_quality_score": round(sum(quality_scores) / len(quality_scores), 1),
            "chunks_per_topic": round(total_chunks / total_topics, 2)
        },
        "quality_distribution": {
            "excellent_80_100": len([q for q in quality_scores if q >= 80]),
            "good_50_79": len([q for q in quality_scores if 50 <= q < 80]),
            "poor_0_49": len([q for q in quality_scores if q < 50])
        },
        "percentages": {
            "excellent_percent": round(len([q for q in quality_scores if q >= 80]) / total_topics * 100, 1),
            "good_percent": round(len([q for q in quality_scores if 50 <= q < 80]) / total_topics * 100, 1),
            "poor_percent": round(len([q for q in quality_scores if q < 50]) / total_topics * 100, 1)
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    print(f"Quality metrics saved to: {output_file}")
    return metrics

def process_integrated():
    """Process with text cleaning AND chunking"""
    print("Integrated Processing: Cleaning + Chunking...")
    
    # Ensure output directory
    os.makedirs('data/processed/chunks', exist_ok=True)
    
    # Initialize both processors
    cleaner = MedicalTextCleaner()
    chunker = StreamingChunker(chunk_size=800, chunk_overlap=150)
    
    total_topics = 0
    total_chunks = 0
    quality_scores = []
    
    try:
        with open('data/processed/health_topics.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            total_topics = len(data)
            
            # Output file for cleaned chunks
            output_file = 'data/processed/chunks/medical_chunks_cleaned.json'
            
            with open(output_file, 'w', encoding='utf-8') as out_file:
                out_file.write('[\n')  # Start JSON array
                
                first_chunk = True
                
                for i, topic in enumerate(data):
                    if i % 50 == 0:
                        print(f"Processing topic {i+1}/{total_topics}...")
                    
                    # STEP 1: Clean the topic
                    cleaned_topic = cleaner.clean_topic(topic)
                    quality_scores.append(cleaned_topic['quality_score'])
                    
                    # STEP 2: Chunk the cleaned topic
                    for chunk in chunker.process_topic_streaming(cleaned_topic):
                        if not first_chunk:
                            out_file.write(',\n')
                        
                        json.dump(chunk, out_file, ensure_ascii=False)
                        first_chunk = False
                        total_chunks += 1
                
                out_file.write('\n]')  # End JSON array
        
        # Final statistics
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        avg_chunks_per_topic = total_chunks / total_topics if total_topics > 0 else 0
        
        print(f"\nINTEGRATED PROCESSING COMPLETE!")
        print(f"Topics processed: {total_topics}")
        print(f"Total chunks created: {total_chunks}")
        print(f"Average quality score: {avg_quality:.1f}/100")
        print(f"Avg chunks per topic: {avg_chunks_per_topic:.1f}")
        print(f"Saved to: {output_file}")
        
        # Quality distribution
        excellent = len([q for q in quality_scores if q >= 80])
        good = len([q for q in quality_scores if 50 <= q < 80])
        poor = len([q for q in quality_scores if q < 50])
        
        print(f"\nQUALITY DISTRIBUTION:")
        print(f"   Excellent (80-100): {excellent} topics")
        print(f"   Good (50-79): {good} topics") 
        print(f"   Poor (0-49): {poor} topics")
        
        # Return values so they can be used outside
        return quality_scores, total_topics, total_chunks
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return [], 0, 0

if __name__ == "__main__":
    # Process data and get the metrics
    quality_scores, total_topics, total_chunks = process_integrated()
    
    # Save quality metrics
    if quality_scores:  # Only save if processing was successful
        metrics_file = 'data/processed/quality_metrics.json'
        quality_metrics = save_quality_metrics(quality_scores, total_topics, total_chunks, metrics_file)