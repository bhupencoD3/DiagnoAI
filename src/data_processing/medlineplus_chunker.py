from typing import Dict, Any, Generator, List
import re

class StreamingChunker:
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 300):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_topic_streaming(self, topic: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Process topics with context-preserving chunking strategy"""
        content = topic.get('content', '')
        
        if not content:
            return
        
        word_count = len(content.split())
        
        if word_count <= self.chunk_size:
            chunk = self._create_chunk(topic, content, 1, 1)
            if chunk:
                yield chunk
        elif word_count <= self.chunk_size * 2:
            midpoint = self._find_optimal_split_point(content)
            chunk1 = content[:midpoint]
            chunk2 = content[midpoint - self.chunk_overlap:]
            
            chunk1_obj = self._create_chunk(topic, chunk1, 1, 2)
            chunk2_obj = self._create_chunk(topic, chunk2, 2, 2)
            
            if chunk1_obj:
                yield chunk1_obj
            if chunk2_obj:
                yield chunk2_obj
        else:
            for chunk in self._chunk_by_paragraphs_preserve_context(topic, content, 1):
                if chunk:
                    yield chunk
    
    def _find_optimal_split_point(self, content: str) -> int:
        """Locate natural break points for content splitting"""
        para_break = content.find('\n\n')
        if para_break != -1 and para_break > len(content) * 0.3:
            return para_break
        
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) > 1:
            mid_sentence = len(sentences) // 2
            current_pos = 0
            for i, sentence in enumerate(sentences):
                if i == mid_sentence:
                    return current_pos + len(sentence)
                current_pos += len(sentence) + 1
        
        return len(content) // 2
    
    def _chunk_by_paragraphs_preserve_context(self, topic: Dict[str, Any], content: str, base_chunk_num: int) -> Generator[Dict[str, Any], None, None]:
        """Create chunks by combining paragraphs while maintaining context"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and len(p.strip()) > 50]
        
        combined_paragraphs = []
        current_combined = ""
        
        for para in paragraphs:
            if len(current_combined.split()) + len(para.split()) <= self.chunk_size:
                if current_combined:
                    current_combined += "\n\n" + para
                else:
                    current_combined = para
            else:
                if current_combined:
                    combined_paragraphs.append(current_combined)
                current_combined = para
        
        if current_combined:
            combined_paragraphs.append(current_combined)
        
        if len(combined_paragraphs) > len(content.split()) // 200:
            chunks_needed = max(1, len(content.split()) // self.chunk_size)
            words_per_chunk = len(content.split()) // chunks_needed
            
            chunks = []
            current_chunk = ""
            current_word_count = 0
            
            for para in paragraphs:
                para_word_count = len(para.split())
                if current_word_count + para_word_count <= words_per_chunk * 1.2:
                    if current_chunk:
                        current_chunk += "\n\n" + para
                    else:
                        current_chunk = para
                    current_word_count += para_word_count
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = para
                    current_word_count = para_word_count
            
            if current_chunk:
                chunks.append(current_chunk)
            
            combined_paragraphs = chunks
        
        for i, chunk_content in enumerate(combined_paragraphs, base_chunk_num):
            chunk = self._create_chunk(topic, chunk_content, i, len(combined_paragraphs))
            if chunk:
                yield chunk
    
    def _create_chunk(self, topic: Dict[str, Any], chunk_text: str, chunk_num: int, total_chunks: int) -> Dict[str, Any]:
        """Construct chunk dictionary with relevant metadata"""
        if not chunk_text or len(chunk_text.strip()) < 30:
            return None
        
        medical_concepts = self._extract_medical_concepts(chunk_text)
        
        return {
            'chunk_id': f"{topic['id']}_{chunk_num}",
            'topic_id': topic['id'],
            'topic_title': topic['title'],
            'content': chunk_text,
            'chunk_number': chunk_num,
            'word_count': len(chunk_text.split()),
            'char_count': len(chunk_text),
            'synonyms': topic.get('synonyms', []),
            'mesh_terms': topic.get('mesh_terms', []),
            'search_terms': topic.get('search_terms', []),
            'quality_score': topic.get('quality_score', 0),
            'source_url': topic.get('url', ''),
            'medical_concepts': medical_concepts,
            'has_structured_content': any(indicator in chunk_text.lower() for indicator in [
                'symptoms', 'treatment', 'causes', 'diagnosis', 'prevention'
            ])
        }
    
    def _extract_medical_concepts(self, text: str) -> List[str]:
        """Identify medical concept categories present in the text"""
        concepts = []
        medical_indicators = {
            'symptoms': ['symptom', 'sign', 'manifestation', 'presentation'],
            'treatment': ['treatment', 'therapy', 'medication', 'management', 'drug'],
            'causes': ['cause', 'etiology', 'reason', 'risk factor'],
            'diagnosis': ['diagnosis', 'test', 'examination', 'screening'],
            'prevention': ['prevention', 'prevent', 'avoid', 'protection']
        }
        
        text_lower = text.lower()
        for concept_type, indicators in medical_indicators.items():
            if any(f" {indicator} " in f" {text_lower} " for indicator in indicators):
                concepts.append(concept_type)
        
        return concepts