import re
from typing import Dict, Any, List

class MeadowCleaner:
    """Cleaner specifically for Medical Meadow QA data"""
    
    def __init__(self):
        self.cleanup_patterns = [
            (r'\s+', ' '),
            (r'\n+', ' '),
        ]
    
    def clean_topic(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and enhance Medical Meadow topic"""
        cleaned = topic.copy()
        
        if 'content' in cleaned:
            cleaned['content'] = self._clean_content(cleaned['content'])
        
        cleaned = self._enhance_qa_topic(cleaned)
        cleaned['search_terms'] = self._generate_search_terms(cleaned)
        cleaned['medical_concepts'] = self._extract_medical_concepts(cleaned)
        cleaned['synonyms'] = self._extract_synonyms(cleaned)
        cleaned['mesh_terms'] = self._extract_mesh_terms(cleaned)
        cleaned['has_structured_content'] = self._has_structured_content(cleaned)
        cleaned['quality_score'] = self._calculate_quality_score(cleaned)
        
        return cleaned
    
    def _clean_content(self, content: str) -> str:
        """Clean content with minimal changes"""
        cleaned = content
        for pattern, replacement in self.cleanup_patterns:
            cleaned = re.sub(pattern, replacement, cleaned)
        return cleaned.strip()
    
    def _enhance_qa_topic(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance topic with QA-specific fields"""
        topic.setdefault('question', '')
        topic.setdefault('answer', '')
        topic.setdefault('word_count', len(topic.get('content', '').split()))
        topic.setdefault('char_count', len(topic.get('content', '')))
        
        return topic
    
    def _generate_search_terms(self, topic: Dict[str, Any]) -> List[str]:
        """Generate search terms from QA content"""
        search_terms = set()
        
        search_terms.add(topic['title'].lower())
        
        all_text = f"{topic['title']} {topic['content']}".lower()
        words = re.findall(r'\b[a-z]{3,}\b', all_text)
        
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'with', 'this', 'that'}
        meaningful_words = [word for word in words if word not in stop_words]
        
        search_terms.update(meaningful_words[:20])
        
        return list(search_terms)
    
    def _extract_medical_concepts(self, topic: Dict[str, Any]) -> List[str]:
        """Extract medical concepts from QA content"""
        concepts = set()
        content_lower = topic['content'].lower()
        
        medical_concepts = {
            'diagnosis', 'symptoms', 'treatment', 'causes', 'risk factors',
            'prevention', 'complications', 'prognosis', 'classification',
            'management', 'screening', 'medications', 'pathophysiology'
        }
        
        for concept in medical_concepts:
            if concept in content_lower:
                concepts.add(concept)
        
        return list(concepts)
    
    def _extract_synonyms(self, topic: Dict[str, Any]) -> List[str]:
        """Extract synonyms from QA content"""
        synonyms = set()
        text = topic['content']
        
        synonym_patterns = [
            (r'also known as ([^.,]+)', 1),
            (r'called ([^.,]+)', 1),
            (r'referred to as ([^.,]+)', 1),
            (r'abbreviated as ([^.,]+)', 1),
        ]
        
        for pattern, group in synonym_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                synonym = match.strip()
                if 2 < len(synonym) < 50:
                    synonyms.add(synonym)
        
        return list(synonyms)
    
    def _extract_mesh_terms(self, topic: Dict[str, Any]) -> List[str]:
        """Extract MeSH-like terms"""
        mesh_terms = set()
        content = topic['content']
        
        disease_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:disease|syndrome|disorder|condition)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+carcinoma\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+oma\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+itis\b',
        ]
        
        for pattern in disease_patterns:
            matches = re.findall(pattern, content)
            mesh_terms.update(matches)
        
        return list(mesh_terms)
    
    def _has_structured_content(self, topic: Dict[str, Any]) -> bool:
        """Check if content has structure"""
        content = topic.get('content', '')
        structured_indicators = ['•', '\n', ';', ':', ' - ']
        return any(indicator in content for indicator in structured_indicators)
    
    def _calculate_quality_score(self, topic: Dict[str, Any]) -> float:
        """Calculate quality score for QA content"""
        score = 0.0
        
        content_words = topic.get('word_count', 0)
        if content_words > 100:
            score += 40
        elif content_words > 50:
            score += 30
        elif content_words > 25:
            score += 20
        else:
            score += 10
        
        answer = topic.get('answer', '')
        answer_words = len(answer.split())
        if answer_words > 50:
            score += 30
        elif answer_words > 25:
            score += 20
        elif answer_words > 10:
            score += 15
        else:
            score += 5
        
        if self._has_structured_content(topic):
            score += 10
        
        if topic.get('medical_concepts'):
            score += min(len(topic['medical_concepts']) * 5, 20)
        
        return min(score, 100.0)
    
    def clean_all_topics(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean all Medical Meadow topics"""
        cleaned_topics = []
        
        for topic in topics:
            cleaned_topic = self.clean_topic(topic)
            cleaned_topics.append(cleaned_topic)
        
        return cleaned_topics