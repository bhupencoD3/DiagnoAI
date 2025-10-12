import re
from typing import Dict, Any, List

class MedicalTextCleaner:
    def __init__(self):
        self.cleanup_patterns = [
            (r'\s+', ' '),
        ]

    def clean_topic(self, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply minimal cleaning to preserve medical context"""
        cleaned = topic_data.copy()
        
        if 'content' in cleaned:
            cleaned['content'] = self._clean_content(cleaned['content'])
        
        cleaned['search_terms'] = self._generate_search_terms(cleaned)
        
        cleaned['quality_score'] = self._calculate_quality_score(cleaned)
        
        return cleaned
    
    def _clean_content(self, content: str) -> str:
        """Perform basic whitespace normalization"""
        if not content:
            return ""
        
        cleaned = content
        for pattern, replacement in self.cleanup_patterns:
            cleaned = re.sub(pattern, replacement, cleaned)
        
        return cleaned.strip()
    
    def _generate_search_terms(self, topic: Dict[str, Any]) -> list:
        """Compile search terms from topic metadata"""
        search_terms = set()
        
        search_terms.add(topic['title'].lower())
        
        for synonym in topic.get('synonyms', []):
            search_terms.add(synonym.lower())
        
        for mesh_term in topic.get('mesh_terms', []):
            search_terms.add(mesh_term.lower())
        
        return list(search_terms)
    
    def _calculate_quality_score(self, topic: Dict[str, Any]) -> float:
        """Assess topic quality based on content and metadata"""
        score = 0.0
        
        content_length = len(topic.get('content', ''))
        if content_length > 500:
            score += 70
        elif content_length > 200:
            score += 50
        elif content_length > 50:
            score += 30
        
        if topic.get('synonyms'):
            score += min(len(topic['synonyms']) * 5, 15)
        
        if topic.get('mesh_terms'):
            score += min(len(topic['mesh_terms']) * 5, 15)
        
        return min(score, 100.0)

def clean_all_topics(topics_data: list) -> list:
    """Process all medical topics through cleaning pipeline"""
    cleaner = MedicalTextCleaner()
    cleaned_topics = []
    
    print("Starting medical topics cleaning process...")
    for i, topic in enumerate(topics_data):
        cleaned_topic = cleaner.clean_topic(topic)
        cleaned_topics.append(cleaned_topic)
        
        if (i + 1) % 100 == 0:
            print(f"Completed cleaning for {i + 1} topics")
    
    print(f"Finished cleaning {len(cleaned_topics)} total topics")
    return cleaned_topics