import json
from datetime import datetime

def generate_comprehensive_metrics():
    """Generate detailed quality metrics for the medical dataset"""
    
    try:
        with open('data/processed/chunks/medical_chunks_cleaned.json', 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        with open('data/processed/health_topics.json', 'r', encoding='utf-8') as f:
            topics = json.load(f)
        
        # Calculate comprehensive metrics
        metrics = {
            "generated_date": datetime.now().isoformat(),
            "dataset_overview": {
                "total_health_topics": len(topics),
                "total_chunks": len(chunks),
                "chunks_per_topic_ratio": round(len(chunks) / len(topics), 2),
                "total_words": sum(chunk['word_count'] for chunk in chunks),
                "avg_words_per_chunk": round(sum(chunk['word_count'] for chunk in chunks) / len(chunks), 1)
            },
            "chunk_analysis": {
                "small_chunks_0_200": len([c for c in chunks if c['word_count'] < 200]),
                "medium_chunks_200_500": len([c for c in chunks if 200 <= c['word_count'] < 500]),
                "large_chunks_500_plus": len([c for c in chunks if c['word_count'] >= 500]),
                "chunk_size_recommendation": "Optimal" if 200 <= sum(c['word_count'] for c in chunks)/len(chunks) <= 500 else "Adjust"
            },
            "content_quality": {
                "topics_with_synonyms": len([t for t in topics if t.get('synonyms')]),
                "topics_with_mesh_terms": len([t for t in topics if t.get('mesh_terms')]),
                "avg_synonyms_per_topic": round(sum(len(t.get('synonyms', [])) for t in topics) / len(topics), 1),
                "avg_mesh_terms_per_topic": round(sum(len(t.get('mesh_terms', [])) for t in topics) / len(topics), 1)
            },
            "performance_metrics": {
                "estimated_vector_db_size_mb": round(len(chunks) * 0.002, 2),  # Rough estimate
                "estimated_query_speed_ms": round(len(chunks) * 0.1, 1),  # Rough estimate
                "recommended_concurrent_users": min(100, len(chunks) // 10)
            }
        }
        
        # Save metrics
        with open('data/processed/dataset_metrics.json', 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        print("Comprehensive metrics generated!")
        return metrics
        
    except Exception as e:
        print(f"❌ Error generating metrics: {e}")

if __name__ == "__main__":
    generate_comprehensive_metrics()