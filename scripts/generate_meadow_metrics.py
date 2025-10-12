import json
import os
from datetime import datetime

def generate_meadow_metrics():
    """Generate comprehensive metrics for Medical Meadow dataset analysis"""
    
    try:
        chunks_path = 'data/processed/meadow_chunks/meadow_medical_chunks.json'
        topics_path = 'data/processed/meadow_chunks/meadow_cleaned_topics.json'
        
        if not os.path.exists(chunks_path):
            print(f"Chunks file not found at specified path: {chunks_path}")
            return None
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        with open(topics_path, 'r', encoding='utf-8') as f:
            topics = json.load(f)
        
        chunk_sizes = [c['word_count'] for c in chunks]
        quality_scores = [t.get('quality_score', 0) for t in topics]
        
        metrics = {
            "generated_date": datetime.now().isoformat(),
            "data_source": "Medical Meadow Wikidoc",
            "dataset_overview": {
                "total_topics": len(topics),
                "total_chunks": len(chunks),
                "chunks_per_topic": round(len(chunks) / len(topics), 2),
                "avg_chunk_size_words": round(sum(chunk_sizes) / len(chunk_sizes), 1),
                "avg_quality_score": round(sum(quality_scores) / len(quality_scores), 1),
                "total_words": sum(chunk_sizes)
            },
            "chunk_size_analysis": {
                "small_chunks_<100": len([c for c in chunk_sizes if c < 100]),
                "medium_chunks_100_300": len([c for c in chunk_sizes if 100 <= c < 300]),
                "large_chunks_300_plus": len([c for c in chunk_sizes if c >= 300]),
                "size_distribution": f"{(len([c for c in chunk_sizes if c < 100])/len(chunk_sizes)*100):.1f}% small, {(len([c for c in chunk_sizes if 100 <= c < 300])/len(chunk_sizes)*100):.1f}% medium, {(len([c for c in chunk_sizes if c >= 300])/len(chunk_sizes)*100):.1f}% large"
            },
            "quality_analysis": {
                "excellent_80_100": len([s for s in quality_scores if s >= 80]),
                "good_60_79": len([s for s in quality_scores if 60 <= s < 80]),
                "fair_40_59": len([s for s in quality_scores if 40 <= s < 60]),
                "poor_0_39": len([s for s in quality_scores if s < 40]),
                "quality_grade": calculate_quality_grade(quality_scores)
            },
            "token_estimation": {
                "avg_tokens_per_chunk": round(sum(chunk_sizes) / len(chunk_sizes) * 1.3, 1),
                "max_tokens_any_chunk": round(max(chunk_sizes) * 1.3, 1),
                "openai_limit_safe": max(chunk_sizes) * 1.3 < 8000,
                "recommendation": "Dataset compatible with OpenAI embeddings" if max(chunk_sizes) * 1.3 < 8000 else "Some chunks may exceed token limits"
            }
        }
        
        metrics_file = 'data/processed/metrics/meadow_metrics.json'
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print("Medical Meadow metrics generation completed successfully")
        print_metrics_summary(metrics)
        return metrics
        
    except Exception as e:
        print(f"Error occurred during metrics generation: {e}")
        return None

def calculate_quality_grade(quality_scores):
    """Calculate overall quality grade based on average scores"""
    avg_quality = sum(quality_scores) / len(quality_scores)
    
    if avg_quality >= 80:
        return "A"
    elif avg_quality >= 70:
        return "B"
    elif avg_quality >= 60:
        return "C"
    elif avg_quality >= 50:
        return "D"
    else:
        return "F"

def print_metrics_summary(metrics):
    """Display formatted summary of dataset metrics"""
    print("\n" + "="*60)
    print("MEDICAL MEADOW DATASET METRICS SUMMARY")
    print("="*60)
    
    overview = metrics['dataset_overview']
    size_analysis = metrics['chunk_size_analysis']
    quality_analysis = metrics['quality_analysis']
    token_info = metrics['token_estimation']
    
    print(f"Dataset Overview:")
    print(f"   Topics: {overview['total_topics']}")
    print(f"   Chunks: {overview['total_chunks']}")
    print(f"   Chunks per Topic: {overview['chunks_per_topic']}")
    print(f"   Average Chunk Size: {overview['avg_chunk_size_words']} words")
    print(f"   Average Quality Score: {overview['avg_quality_score']}/100")
    
    print(f"\nChunk Size Analysis:")
    print(f"   Small chunks (<100 words): {size_analysis['small_chunks_<100']}")
    print(f"   Medium chunks (100-300): {size_analysis['medium_chunks_100_300']}")
    print(f"   Large chunks (300+): {size_analysis['large_chunks_300_plus']}")
    print(f"   Size distribution: {size_analysis['size_distribution']}")
    
    print(f"\nQuality Analysis:")
    print(f"   Excellent quality (80+): {quality_analysis['excellent_80_100']}")
    print(f"   Good quality (60-79): {quality_analysis['good_60_79']}")
    print(f"   Fair quality (40-59): {quality_analysis['fair_40_59']}")
    print(f"   Poor quality (0-39): {quality_analysis['poor_0_39']}")
    print(f"   Overall quality grade: {quality_analysis['quality_grade']}")
    
    print(f"\nOpenAI Compatibility Check:")
    print(f"   Average tokens per chunk: {token_info['avg_tokens_per_chunk']}")
    print(f"   Maximum tokens in any chunk: {token_info['max_tokens_any_chunk']}")
    print(f"   Compatibility status: {token_info['recommendation']}")
    
    print("="*60)

if __name__ == "__main__":
    generate_meadow_metrics()