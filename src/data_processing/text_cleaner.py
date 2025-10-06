import re
from typing import Dict, Any

class MedicalTextCleaner:
    def __init__(self):
        self.cleanup_patterns = [
            (r'NIH:.*? Diseases', ''),  # Remove NIH attribution lines
            (r'\s+', ' '),  # Normalize whitespace
        ]
    
    def clean_topic(self, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and enhance a single medical topic"""
        cleaned = topic_data.copy()
        
        # Clean content
        if 'content' in cleaned:
            cleaned['content'] = self._clean_content(cleaned['content'])
        
        # Enhance with search terms
        cleaned['search_terms'] = self._generate_search_terms(cleaned)
        
        # Calculate quality score
        cleaned['quality_score'] = self._calculate_quality_score(cleaned)
        
        return cleaned
    
    def _clean_content(self, content: str) -> str:
        """Clean medical content text"""
        if not content:
            return ""
        
        # Apply cleanup patterns
        cleaned = content
        for pattern, replacement in self.cleanup_patterns:
            cleaned = re.sub(pattern, replacement, cleaned)
        
        return cleaned.strip()
    
    def _generate_search_terms(self, topic: Dict[str, Any]) -> list:
        """Generate search terms from title, synonyms, and MeSH terms"""
        search_terms = set()
        
        # Add title
        search_terms.add(topic['title'].lower())
        
        # Add synonyms
        for synonym in topic.get('synonyms', []):
            search_terms.add(synonym.lower())
        
        # Add MeSH terms
        for mesh_term in topic.get('mesh_terms', []):
            search_terms.add(mesh_term.lower())
        
        return list(search_terms)
    
    def _calculate_quality_score(self, topic: Dict[str, Any]) -> float:
        """Calculate quality score based on content completeness"""
        score = 0.0
        
        # Content length (max 50 points)
        content_length = len(topic.get('content', ''))
        if content_length > 500:
            score += 50
        elif content_length > 200:
            score += 30
        elif content_length > 50:
            score += 10
        
        # Synonyms (max 20 points)
        if topic.get('synonyms'):
            score += min(len(topic['synonyms']) * 5, 20)
        
        # MeSH terms (max 20 points)
        if topic.get('mesh_terms'):
            score += min(len(topic['mesh_terms']) * 5, 20)
        
        # Related topics (max 10 points)
        if topic.get('related_topics'):
            score += min(len(topic['related_topics']) * 2, 10)
        
        return min(score, 100.0)

def clean_all_topics(topics_data: list) -> list:
    """Clean all medical topics"""
    cleaner = MedicalTextCleaner()
    cleaned_topics = []
    
    print("Cleaning medical topics...")
    for i, topic in enumerate(topics_data):
        cleaned_topic = cleaner.clean_topic(topic)
        cleaned_topics.append(cleaned_topic)
    
    print(f"Cleaned {len(cleaned_topics)} topics")
    
    # Show quality distribution
    quality_scores = [t['quality_score'] for t in cleaned_topics]
    avg_quality = sum(quality_scores) / len(quality_scores)
    print(f"Average quality score: {avg_quality:.1f}/100")
    
    return cleaned_topics