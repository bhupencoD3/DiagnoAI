import json
import re
from typing import List, Dict, Any

class MedicalMeadowParser:
    def __init__(self):
        pass
    
    def parse_medical_meadow(self, json_file_path: str) -> List[Dict[str, Any]]:
        """Parse Medical Meadow Wikidoc JSON into standardized format"""
        print(f"Parsing Medical Meadow file: {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            topics = []
            for i, item in enumerate(data):
                topic = self._convert_to_standard_format(item, i)
                if topic:
                    topics.append(topic)
            
            print(f"Successfully parsed {len(topics)} Medical Meadow topics")
            return topics
            
        except Exception as e:
            print(f"Error parsing Medical Meadow: {e}")
            return []
    
    def _convert_to_standard_format(self, item: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Convert Medical Meadow QA item to standardized topic format"""
        try:
            question = item.get('input', '').replace('Answer this question truthfully', '').strip()
            if question.startswith(': '):
                question = question[2:]
            
            answer = item.get('output', '')
            title = self._generate_title(question, index)  # Pass index here
            content = self._create_comprehensive_content(title, question, answer)
            search_terms = self._generate_search_terms(title, content)
            quality_score = self._calculate_quality_score(content, answer)
            medical_concepts = self._extract_medical_concepts(content)
            
            return {
                'id': f"meadow_{index + 1:05d}",
                'title': title,
                'url': f"https://www.wikidoc.org/index.php/{title.replace(' ', '_')}",
                'language': 'English',
                'synonyms': self._extract_synonyms(question, answer),
                'content': content,
                'mesh_terms': self._extract_mesh_terms(content),
                'content_length': len(content),
                'word_count': len(content.split()),
                'search_terms': search_terms,
                'quality_score': quality_score,
                'medical_concepts': medical_concepts,
                'has_structured_content': self._has_structured_content(answer),
                'source': 'Medical Meadow Wikidoc'
            }
            
        except Exception as e:
            print(f"Error converting item {index}: {e}")
            return None
    
    def _generate_title(self, question: str, index: int) -> str:  # Add index parameter
        """Generate a proper medical title from the question"""
        title = question.replace('?', '').strip()
        
        patterns = [
            r'^can you provide (?:an? )?overview of ',
            r'^what does "([^"]+)" mean',
            r'^can you provide me with information regarding ',
            r'^what are the historical background and symptoms of ',
            r'^what does the "([^"]+)" refer to',
            r'^how prepared are ',
            r'^can you provide a brief summary of ',
            r'^what is the information regarding ',
            r'^what is ',
            r'^what are ',
            r'^how does ',
            r'^how do ',
            r'^can you explain '
        ]
        
        for pattern in patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        title = re.sub(r'^(?:about|regarding|on|the)\s+', '', title, flags=re.IGNORECASE)
        title = self._capitalize_medical_title(title.strip())
        
        if not title or len(title) < 2:
            title = f"Medical Topic {index + 1}"  # Now index is available
        
        return title
    
    def _capitalize_medical_title(self, title: str) -> str:
        """Capitalize medical titles appropriately"""
        if not title:
            return title
            
        lowercase_words = {'of', 'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'a', 'an'}
        
        words = title.split()
        capitalized_words = []
        
        for i, word in enumerate(words):
            if i == 0 or word.lower() not in lowercase_words:
                if word.upper() in ['HIV', 'AIDS', 'COVID', 'EBOLA', 'ECG', 'BP', 'WHO']:
                    capitalized_words.append(word.upper())
                elif len(word) > 1 and word.isupper():
                    capitalized_words.append(word)
                else:
                    capitalized_words.append(word.capitalize())
            else:
                capitalized_words.append(word.lower())
        
        return ' '.join(capitalized_words)
    
    # ... rest of the methods remain the same
    def _create_comprehensive_content(self, title: str, question: str, answer: str) -> str:
        """Create comprehensive medical content from Q&A"""
        clean_question = question.strip()
        clean_answer = self._clean_and_structure_answer(answer)
        
        if clean_question.lower().replace('?', '') == title.lower():
            content = clean_answer
        else:
            content = f"{clean_answer}"
        
        if len(content.split()) < 20:
            content = f"{title} is {clean_answer}"
        
        return content
    
    def _clean_and_structure_answer(self, answer: str) -> str:
        """Clean and structure the answer into proper medical content"""
        if not answer:
            return ""
        
        answer = re.sub(r'\n+', '\n', answer)
        answer = re.sub(r' +', ' ', answer)
        answer = re.sub(r'^\s*[\-\*]\s*', '• ', answer, flags=re.MULTILINE)
        
        sentences = re.split(r'(?<=[.!?])\s+', answer)
        cleaned_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                if sentence and not sentence[0].isupper():
                    sentence = sentence[0].upper() + sentence[1:]
                cleaned_sentences.append(sentence)
        
        content = ' '.join(cleaned_sentences)
        
        if not content.endswith(('.', '!', '?')):
            content += '.'
        
        return content
    
    def _generate_search_terms(self, title: str, content: str) -> List[str]:
        """Generate comprehensive search terms"""
        search_terms = set()
        
        search_terms.add(title.lower())
        search_terms.add(title)
        
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        title_words = [word.lower() for word in title.split() if word.lower() not in stop_words and len(word) > 2]
        search_terms.update(title_words)
        
        medical_terms = self._extract_medical_terms(content)
        search_terms.update(medical_terms)
        
        acronyms = self._extract_acronyms(content)
        search_terms.update(acronyms)
        
        return sorted(list(search_terms))
    
    def _extract_medical_terms(self, text: str) -> List[str]:
        """Extract medical terminology from text"""
        terms = set()
        text_lower = text.lower()
        
        medical_suffixes = [
            r'\b[a-z]*itis\b',
            r'\b[a-z]*oma\b',
            r'\b[a-z]*opathy\b',
            r'\b[a-z]*emia\b',
            r'\b[a-z]*osis\b',
            r'\b[a-z]*algia\b',
            r'\b[a-z]*ectomy\b',
            r'\b[a-z]*scopy\b',
            r'\b[a-z]*plasia\b',
            r'\b[a-z]*penia\b',
        ]
        
        for pattern in medical_suffixes:
            matches = re.findall(pattern, text_lower)
            terms.update(matches)
        
        specific_terms = [
            'carcinoma', 'sarcoma', 'leukemia', 'lymphoma', 'melanoma',
            'adenoma', 'glioma', 'myeloma', 'hematoma', 'granuloma',
            'hypertension', 'hypotension', 'tachycardia', 'bradycardia',
            'hyperthyroidism', 'hypothyroidism', 'diabetes', 'asthma',
            'arthritis', 'osteoporosis', 'alzheimer', 'parkinson',
            'vulvovaginitis', 'thyroiditis', 'rhabdomyolysis', 'cardiomyopathy',
            'anaphylaxis', 'syncope', 'hypothyroidism', 'hypercholesteraemia'
        ]
        
        for term in specific_terms:
            if term in text_lower:
                terms.add(term)
        
        return list(terms)
    
    def _extract_acronyms(self, text: str) -> List[str]:
        """Extract medical acronyms from text"""
        acronym_pattern = r'\b[A-Z]{2,6}\b'
        acronyms = re.findall(acronym_pattern, text)
        
        common_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN'}
        medical_acronyms = [acronym for acronym in acronyms if acronym not in common_words]
        
        return medical_acronyms
    
    def _extract_synonyms(self, question: str, answer: str) -> List[str]:
        """Extract synonyms from content"""
        synonyms = set()
        text = question + ' ' + answer
        
        synonym_patterns = [
            (r'also known as ([^.,]+)', 1),
            (r'called ([^.,]+)', 1),
            (r'referred to as ([^.,]+)', 1),
            (r'abbreviated as ([^.,]+)', 1),
            (r'also called ([^.,]+)', 1),
            (r'known as ([^.,]+)', 1),
        ]
        
        for pattern, group in synonym_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                synonym = match.strip()
                if len(synonym) > 2 and len(synonym) < 50:
                    synonyms.add(synonym)
        
        return list(synonyms)
    
    def _extract_mesh_terms(self, content: str) -> List[str]:
        """Extract MeSH-like terms from content"""
        mesh_terms = set()
        
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
    
    def _extract_medical_concepts(self, content: str) -> List[str]:
        """Extract medical concepts from content"""
        concepts = set()
        content_lower = content.lower()
        
        medical_concepts = {
            'diagnosis', 'symptoms', 'treatment', 'causes', 'risk factors',
            'prevention', 'complications', 'prognosis', 'epidemiology',
            'pathophysiology', 'management', 'screening', 'medications'
        }
        
        for concept in medical_concepts:
            if concept in content_lower:
                concepts.add(concept)
        
        return list(concepts)
    
    def _has_structured_content(self, answer: str) -> bool:
        """Check if answer has structured content"""
        structured_indicators = [
            '\n', '•', ' - ', ':', ';', 
            'symptoms include', 'treatment options', 'risk factors'
        ]
        
        return any(indicator in answer for indicator in structured_indicators)
    
    def _calculate_quality_score(self, content: str, answer: str) -> float:
        """Calculate quality score for the content"""
        score = 0.0
        
        content_words = len(content.split())
        if content_words > 100:
            score += 40
        elif content_words > 50:
            score += 30
        elif content_words > 25:
            score += 20
        else:
            score += 10
        
        answer_words = len(answer.split())
        if answer_words > 80:
            score += 30
        elif answer_words > 40:
            score += 25
        elif answer_words > 20:
            score += 15
        else:
            score += 5
        
        medical_terms = self._extract_medical_terms(content)
        score += min(len(medical_terms) * 3, 20)
        
        if self._has_structured_content(answer):
            score += 10
        
        sentences = re.split(r'[.!?]', content)
        avg_sentence_length = sum(len(sent.split()) for sent in sentences if sent) / len(sentences) if sentences else 0
        if 10 <= avg_sentence_length <= 25:
            score += 10
        
        return min(score, 100.0)