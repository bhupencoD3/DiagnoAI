from typing import Dict, Any, Generator

class StreamingChunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_topic_streaming(self, topic: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Process a single topic and yield chunks one by one"""
        content = topic.get('content', '')
        
        if not content:
            return
        
        # Use word count instead of character count for better chunking
        word_count = len(content.split())
        
        # If content is short, yield as single chunk
        if word_count <= self.chunk_size:
            yield self._create_chunk(topic, content, 1, 1)
            return
        
        # Split by paragraphs (better for medical content)
        paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
        
        current_chunk = ""
        chunk_num = 1
        
        for paragraph in paragraphs:
            current_words = len(current_chunk.split())
            paragraph_words = len(paragraph.split())
            
            # If adding this paragraph doesn't exceed chunk size
            if current_words + paragraph_words <= self.chunk_size:
                current_chunk += paragraph + "\n"
            else:
                # Yield current chunk if it has content
                if current_chunk.strip():
                    yield self._create_chunk(topic, current_chunk.strip(), chunk_num, len(paragraphs))
                    chunk_num += 1
                    current_chunk = paragraph + "\n"
        
        # Yield final chunk
        if current_chunk.strip():
            yield self._create_chunk(topic, current_chunk.strip(), chunk_num, len(paragraphs))
    
    def _create_chunk(self, topic: Dict[str, Any], chunk_text: str, chunk_num: int, total_paragraphs: int) -> Dict[str, Any]:
        """Create a chunk with enhanced metadata"""
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
            'source_url': topic.get('url', '')
        }