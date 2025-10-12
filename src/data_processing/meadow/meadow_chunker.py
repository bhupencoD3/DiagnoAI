import re
from typing import List, Dict, Any

class MeadowChunker:
    """Enhanced chunker for Medical Meadow QA data"""
    
    def __init__(self, target_chunk_size: int = 120, min_chunk_size: int = 30, max_chunk_size: int = 300):
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
    
    def chunk_topic(self, topic: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Smart chunking that works with Medical Meadow's concise nature"""
        content = topic.get('content', '')
        words = content.split()
        word_count = len(words)
        
        if self.min_chunk_size <= word_count <= self.max_chunk_size:
            return [self._create_chunk(topic, content, 1, 1)]
        elif word_count < self.min_chunk_size:
            return self._handle_small_content(topic, content, word_count)
        else:
            return self._split_balanced(topic, content, word_count)
    
    def _handle_small_content(self, topic: Dict[str, Any], content: str, word_count: int) -> List[Dict[str, Any]]:
        """Handle small content - enhance only when it adds meaningful context"""
        if word_count < 25 and self._would_benefit_from_context(topic, content):
            enhanced_content = self._add_meaningful_context(topic, content)
            return [self._create_chunk(topic, enhanced_content, 1, 1)]
        
        return [self._create_chunk(topic, content, 1, 1)]
    
    def _would_benefit_from_context(self, topic: Dict[str, Any], content: str) -> bool:
        """Check if adding context would actually improve the chunk"""
        question = topic.get('question', '')
        return (len(question.split()) > 5 and 
                len(content.split()) < 25 and
                self._has_medical_substance(question))
    
    def _has_medical_substance(self, text: str) -> bool:
        """Check if text contains meaningful medical content"""
        medical_terms = [
            'diagnosis', 'treatment', 'symptoms', 'causes', 'risk', 'prognosis',
            'complications', 'management', 'therapy', 'medication', 'surgery',
            'procedure', 'test', 'examination', 'findings', 'clinical', 'patient',
            'disease', 'disorder', 'syndrome', 'condition'
        ]
        text_lower = text.lower()
        return any(term in text_lower for term in medical_terms)
    
    def _add_meaningful_context(self, topic: Dict[str, Any], content: str) -> str:
        """Add context only when it enhances understanding"""
        question = topic.get('question', '')
        clean_content = content
        
        if content.startswith('Question:'):
            lines = content.split('\n\n')
            for line in lines:
                if line.startswith('Answer:'):
                    clean_content = line.replace('Answer:', '').strip()
                    break
        
        if question and not clean_content.startswith(question):
            return f"{question}\n\n{clean_content}"
        
        return clean_content
    
    def _split_balanced(self, topic: Dict[str, Any], content: str, word_count: int) -> List[Dict[str, Any]]:
        """Split large content while maintaining coherence"""
        sentences = self._split_into_sentences(content)
        chunks = []
        current_chunk = []
        current_word_count = 0
        
        for sentence in sentences:
            sentence_words = sentence.split()
            sentence_word_count = len(sentence_words)
            
            if (current_word_count + sentence_word_count > self.max_chunk_size and 
                current_word_count >= self.min_chunk_size):
                
                chunk_content = ' '.join(current_chunk)
                chunks.append(self._create_chunk(topic, chunk_content, len(chunks) + 1, 0))
                current_chunk = []
                current_word_count = 0
            
            current_chunk.append(sentence)
            current_word_count += sentence_word_count
        
        if current_chunk:
            chunk_content = ' '.join(current_chunk)
            
            if (len(chunk_content.split()) < 20 and 
                len(chunks) > 0 and 
                len(chunks[-1]['content'].split()) + len(chunk_content.split()) <= self.max_chunk_size):
                
                previous_chunk = chunks.pop()
                merged_content = previous_chunk['content'] + ' ' + chunk_content
                chunks.append(self._create_chunk(topic, merged_content, len(chunks) + 1, 0))
            else:
                chunks.append(self._create_chunk(topic, chunk_content, len(chunks) + 1, 0))
        
        for i, chunk in enumerate(chunks):
            chunk['total_chunks'] = len(chunks)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while handling medical abbreviations"""
        pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s'
        sentences = re.split(pattern, text)
        
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence.split()) > 0:
                if not cleaned_sentences or len(sentence.split()) > 1:
                    cleaned_sentences.append(sentence)
                else:
                    cleaned_sentences[-1] += ' ' + sentence
        
        return cleaned_sentences
    
    def _create_chunk(self, topic: Dict[str, Any], content: str, chunk_num: int, total_chunks: int) -> Dict[str, Any]:
        """Create standardized chunk"""
        words = content.split()
        
        return {
            'chunk_id': f"{topic['id']}_{chunk_num}",
            'topic_id': topic['id'],
            'topic_title': topic['title'],
            'content': content,
            'chunk_number': chunk_num,
            'total_chunks': total_chunks,
            'word_count': len(words),
            'char_count': len(content),
            'synonyms': topic.get('synonyms', []),
            'mesh_terms': topic.get('mesh_terms', []),
            'search_terms': topic.get('search_terms', []),
            'quality_score': topic.get('quality_score', 0),
            'source_url': topic.get('url', ''),
            'medical_concepts': topic.get('medical_concepts', []),
            'has_structured_content': topic.get('has_structured_content', False),
            'qa_format': True,
            'question': topic.get('question', ''),
            'answer': topic.get('answer', '')
        }
    
    def chunk_all_topics(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Chunk all topics with realistic expectations"""
        all_chunks = []
        
        for i, topic in enumerate(topics):
            if i % 1000 == 0:
                print(f"Chunking topic {i+1}/{len(topics)}")
            
            chunks = self.chunk_topic(topic)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def analyze_chunk_distribution(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the chunk size distribution"""
        word_counts = [c['word_count'] for c in chunks]
        
        return {
            'total_chunks': len(chunks),
            'small_chunks_<100': len([c for c in word_counts if c < 100]),
            'medium_chunks_100_300': len([c for c in word_counts if 100 <= c < 300]),
            'large_chunks_300_plus': len([c for c in word_counts if c >= 300]),
            'avg_chunk_size': sum(word_counts) / len(word_counts),
            'distribution_percentage': {
                'small': f"{(len([c for c in word_counts if c < 100])/len(word_counts)*100):.1f}%",
                'medium': f"{(len([c for c in word_counts if 100 <= c < 300])/len(word_counts)*100):.1f}%",
                'large': f"{(len([c for c in word_counts if c >= 300])/len(word_counts)*100):.1f}%"
            }
        }