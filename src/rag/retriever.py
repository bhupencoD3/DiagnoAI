from typing import List, Dict, Any, Optional
import logging
import re
import time
from src.rag.vector_store import MedicalVectorStore
from src.utils.config import settings  

class MedicalRetriever:
    def __init__(self, vector_store: MedicalVectorStore):
        self.vector_store = vector_store
        self.logger = logging.getLogger(__name__)
        
        self.symptom_patterns = [
            r'symptom', r'signs?', r'pain', r'hurt', r'ache', r'fever', r'cough',
            r'headache', r'nausea', r'vomit', r'dizzy', r'fatigue', r'weakness',
            r'thirst', r'hunger', r'urination', r'vision', r'breath', r'chest',
            r'feel', r'experience', r'manifestation'
        ]
        
        self.treatment_patterns = [
            r'treatment', r'treat', r'cure', r'medicine', r'drug', r'therapy',
            r'medication', r'surgery', r'remedy', r'management', r'how to', 
            r'what.*do', r'how.*treat', r'therapy'
        ]
        
        self.cause_patterns = [
            r'cause', r'causes', r'why', r'reason', r'risk factor', r'what causes',
            r'what leads to', r'what.*cause', r'why.*happen', r'etiology'
        ]
        
        self.diagnosis_patterns = [
            r'diagnos', r'test', r'examination', r'screening', r'detect',
            r'identify', r'how.*know', r'how.*diagnose', r'assessment'
        ]
        
        self.prevention_patterns = [
            r'prevent', r'prevention', r'avoid', r'protection', r'prophylaxis',
            r'how.*prevent', r'how.*avoid', r'stop.*from'
        ]
        
        self.drug_patterns = [
            r'drug', r'medicine', r'medication', r'pill', r'tablet', r'capsule',
            r'prescription', r'otc', r'over.the.counter', r'pharmaceutical',
            r'treatment', r'therapy', r'dosage', r'dose', r'ingredient',
            r'side effect', r'warning', r'contraindication', r'interaction',
            r'brand', r'generic', r'manufacturer', r'fda', r'approval',
            r'suggest', r'recommend', r'what.*take', r'what.*use'
        ]
        
        self.medical_concept_pairs = {
            'symptoms': ['symptom', 'sign', 'manifestation', 'presentation', 'indication', 'complaint', 'experience'],
            'treatment': ['treatment', 'therapy', 'medication', 'management', 'drug', 'cure', 'intervention', 'prescription'],
            'causes': ['cause', 'etiology', 'reason', 'risk factor', 'trigger', 'pathogenesis'],
            'diagnosis': ['diagnosis', 'test', 'examination', 'screening', 'detection', 'assessment'],
            'prevention': ['prevention', 'prevent', 'avoid', 'protection', 'prophylaxis', 'lifestyle'],
            'drugs': ['drug', 'medicine', 'medication', 'pharmaceutical', 'pill', 'tablet', 'capsule', 'dosage']
        }
        
        self.source_quality_weights = {
            'medline_plus': 1.5,
            'fda_drugs': 1.4,
            'medical_meadow': 1.0,
            'unknown': 1.0
        }
        
        self.common_conditions = [
            'acne', 'headache', 'fever', 'cough', 'dengue', 'diabetes', 'hypertension',
            'asthma', 'dermatitis', 'arthritis', 'influenza', 'flu', 'covid', 'malaria',
            'allergy', 'migraine', 'obesity', 'anemia', 'anxiety', 'depression'
        ]
    
    def retrieve(self, query: str, n_results: Optional[int] = None, context_type: Optional[str] = None) -> List[Dict[str, Any]]:
        start_time = time.time()
        
        try:
            intent = self._analyze_query_intent(query)
            
            if n_results is None:
                n_results = self._determine_result_count(query, intent)
            
            initial_results = min(n_results * 3, 30)
            
            self.logger.info(f"Searching for {n_results} results for: '{query}' (intent: {intent['primary_concept']})")
            
            results = self.vector_store.hybrid_search(
                query,
                n_results=initial_results,
                alpha=self._get_optimal_alpha(query, intent)
            )
            
            if not results:
                self.logger.warning("No results found from vector store")
                return []
            
            filtered_results = self._filter_with_strict_relevance(results, intent, query)
            
            if len(filtered_results) < 3:
                self.logger.info("Few relevant results found, including some high-scoring alternatives")
                high_score_results = [r for r in results if r['combined_score'] > 0.7][:2]
                for result in high_score_results:
                    if result not in filtered_results:
                        filtered_results.append(result)
            
            final_results = self._ensure_diversity(
                filtered_results,
                max_same_topic=settings.MAX_SAME_TOPIC_RESULTS
            )
            
            quality_results = [r for r in final_results if r['combined_score'] > 0.3]
            
            if len(quality_results) < 2 and len(final_results) > len(quality_results):
                quality_results = final_results[:max(2, n_results)]
            
            retrieval_time = time.time() - start_time
            
            source_counts = {}
            for result in quality_results[:n_results]:
                source = result['metadata'].get('source_dataset', 'unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
            
            relevant_count = sum(1 for r in quality_results if self._is_doc_relevant(r, query))
            
            self.logger.info(f"Retrieved {len(quality_results)} quality results in {retrieval_time:.2f}s")
            self.logger.info(f"Relevant results: {relevant_count}/{len(quality_results)}")
            self.logger.info(f"Top scores: {[round(r['combined_score'], 2) for r in quality_results[:3]]}")
            self.logger.info(f"Source distribution: {source_counts}")
            
            return quality_results[:n_results]
            
        except Exception as e:
            self.logger.error(f"Retrieval failed: {e}")
            try:
                fallback_results = self.vector_store.simple_search(query, n_results or 5)
                self.logger.info(f"Using fallback search, found {len(fallback_results)} results")
                return fallback_results
            except Exception as fallback_error:
                self.logger.error(f"Fallback search also failed: {fallback_error}")
                return []
    
    def _filter_with_strict_relevance(self, results: List[Dict], intent: Dict, query: str) -> List[Dict]:
        filtered = []
        query_lower = query.lower()
        
        main_condition = self._extract_main_condition(query_lower)
        
        for result in results:
            metadata = result['metadata']
            content = result['content'].lower()
            title = metadata.get('topic_title', '').lower()
            
            boost = 1.0
            
            if not self._is_result_relevant(result, query, main_condition):
                continue
            
            source = metadata.get('source_dataset', 'unknown')
            source_boost = self.source_quality_weights.get(source, 1.0)
            boost *= source_boost
            
            if intent['is_drug_query'] and source == 'fda_drugs':
                boost *= 2.5
                brand_name = metadata.get('brand_name', '').lower()
                if brand_name and any(word in query_lower for word in brand_name.split()):
                    boost *= 1.5
            
            elif intent['is_treatment_query']:
                if source == 'medline_plus':
                    boost *= 1.8
                elif source == 'fda_drugs':
                    boost *= 1.4
            
            medical_concepts = metadata.get('medical_concepts', '').split('|')
            
            if intent['primary_concept'] in medical_concepts:
                boost *= 1.8
            
            elif intent['is_symptom_query'] and any(term in content for term in ['symptom', 'sign', 'manifestation']):
                boost *= 1.6
            elif intent['is_treatment_query'] and any(term in content for term in ['treatment', 'therapy', 'medication']):
                boost *= 1.6
            elif intent['is_cause_query'] and any(term in content for term in ['cause', 'reason', 'risk factor']):
                boost *= 1.6
            
            synonyms = metadata.get('synonyms', '').lower().split('|')
            mesh_terms = metadata.get('mesh_terms', '').lower().split('|')
            all_keywords = set(synonyms + mesh_terms + medical_concepts)
            query_terms = set(query_lower.split())
            keyword_matches = query_terms.intersection(all_keywords)
            
            if keyword_matches:
                boost *= (1.0 + 0.15 * len(keyword_matches))
            
            if metadata.get('has_structured_content', False):
                boost *= 1.2
            
            quality_boost = metadata.get('quality_score', 50) / 100.0
            boost *= (0.9 + (quality_boost * 0.2))
            
            result['combined_score'] *= boost
            filtered.append(result)
        
        return sorted(filtered, key=lambda x: x['combined_score'], reverse=True)

    def _is_result_relevant(self, result: Dict, query: str, main_condition: str = None) -> bool:
        if not main_condition:
            main_condition = self._extract_main_condition(query.lower())
        
        content = result['content'].lower()
        title = result['metadata'].get('topic_title', '').lower()
        
        if main_condition:
            condition_in_title = main_condition in title
            condition_in_content = main_condition in content
            
            if result['combined_score'] > 0.8:
                return condition_in_title or condition_in_content
            else:
                return condition_in_title or (condition_in_content and content.count(main_condition) >= 2)
        
        query_terms = set(query.lower().split())
        stop_words = {'what', 'are', 'the', 'symptoms', 'of', 'and', 'or', 'is', 'for'}
        relevant_terms = query_terms - stop_words
        
        title_matches = sum(1 for term in relevant_terms if term in title and len(term) > 3)
        content_matches = sum(1 for term in relevant_terms if term in content and len(term) > 3)
        
        return title_matches >= 1 or content_matches >= 2

    def _extract_main_condition(self, query: str) -> str:
        query_lower = query.lower()
        
        for condition in self.common_conditions:
            if condition in query_lower:
                return condition
        
        patterns = [
            r'symptoms of (\w+)',
            r'treatment for (\w+)', 
            r'what causes (\w+)',
            r'how to treat (\w+)',
            r'what is (\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                condition = match.group(1)
                if len(condition) > 3:
                    return condition
        
        return ""

    def _is_doc_relevant(self, doc: Dict, query: str) -> bool:
        return self._is_result_relevant(doc, query)

    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        
        intent = {
            'is_symptom_query': any(re.search(pattern, query_lower) for pattern in self.symptom_patterns),
            'is_treatment_query': any(re.search(pattern, query_lower) for pattern in self.treatment_patterns),
            'is_cause_query': any(re.search(pattern, query_lower) for pattern in self.cause_patterns),
            'is_diagnosis_query': any(re.search(pattern, query_lower) for pattern in self.diagnosis_patterns),
            'is_prevention_query': any(re.search(pattern, query_lower) for pattern in self.prevention_patterns),
            'is_drug_query': any(re.search(pattern, query_lower) for pattern in self.drug_patterns),
            'is_general_query': True,
            'query_complexity': self._assess_complexity(query),
            'primary_concept': self._identify_primary_concept(query),
            'query_terms': query_lower.split()
        }
        
        intent['is_general_query'] = not any([
            intent['is_symptom_query'],
            intent['is_treatment_query'], 
            intent['is_cause_query'],
            intent['is_diagnosis_query'],
            intent['is_prevention_query'],
            intent['is_drug_query']
        ])
        
        return intent
    
    def _identify_primary_concept(self, query: str) -> str:
        query_lower = query.lower()
        
        for concept, indicators in self.medical_concept_pairs.items():
            for indicator in indicators:
                if f" {indicator} " in f" {query_lower} " or query_lower.startswith(indicator) or query_lower.endswith(indicator):
                    return concept
        
        return 'general'
    
    def _assess_complexity(self, query: str) -> str:
        word_count = len(query.split())
        medical_terms = len([word for word in query.split() if len(word) > 8 and any(c.isalpha() for c in word)])
        
        has_multiple_questions = query.count('?') > 1 or (' and ' in query.lower() and '?' in query)
        
        if word_count > 12 or medical_terms > 3 or has_multiple_questions:
            return "complex"
        elif word_count > 6 or medical_terms > 1:
            return "medium"
        else:
            return "simple"
    
    def _get_optimal_alpha(self, query: str, intent: Dict) -> float:
        if intent['is_drug_query']:
            return 0.6
        elif intent['is_general_query']:
            return 0.7
        elif intent['query_complexity'] == "complex":
            return 0.6
        else:
            return 0.8
    
    def _determine_result_count(self, query: str, intent: Dict) -> int:
        complexity = intent['query_complexity']
        
        if complexity == "complex":
            return 10
        elif complexity == "medium":
            return 8
        else:
            return 6
    
    def _ensure_diversity(self, results: List[Dict], max_same_topic: int) -> List[Dict]:
        if not results:
            return []
            
        topic_count = {}
        source_count = {}
        diverse_results = []
        
        for result in results:
            topic_id = result['metadata']['topic_id']
            source = result['metadata'].get('source_dataset', 'unknown')
            
            topic_count[topic_id] = topic_count.get(topic_id, 0) + 1
            source_count[source] = source_count.get(source, 0) + 1
            
            if topic_count[topic_id] <= max_same_topic:
                diverse_results.append(result)
            else:
                if result['combined_score'] > 0.8 or source_count[source] < 2:
                    diverse_results.append(result)
        
        return diverse_results
    
    def get_retrieval_metrics(self, query: str, results: List[Dict]) -> Dict[str, Any]:
        if not results:
            return {
                'query': query,
                'results_count': 0,
                'avg_quality_score': 0,
                'topics_covered': 0,
                'avg_combined_score': 0,
                'relevant_results': 0,
                'retrieval_quality': 'poor'
            }
        
        relevant_count = sum(1 for r in results if self._is_doc_relevant(r, query))
        avg_score = sum(r['combined_score'] for r in results) / len(results)
        
        relevance_ratio = relevant_count / len(results)
        
        if avg_score > 0.8 and relevance_ratio > 0.8:
            retrieval_quality = 'excellent'
        elif avg_score > 0.6 and relevance_ratio > 0.6:
            retrieval_quality = 'good'
        elif avg_score > 0.4 and relevance_ratio > 0.4:
            retrieval_quality = 'fair'
        else:
            retrieval_quality = 'poor'
        
        return {
            'query': query,
            'results_count': len(results),
            'avg_quality_score': sum(r['metadata'].get('quality_score', 0) for r in results) / len(results),
            'topics_covered': len(set(r['metadata']['topic_id'] for r in results)),
            'avg_combined_score': avg_score,
            'relevant_results': relevant_count,
            'relevance_ratio': relevance_ratio,
            'retrieval_quality': retrieval_quality
        }

    def debug_retrieval(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        debug_info = {
            'query': query,
            'intent_analysis': self._analyze_query_intent(query),
            'main_condition': self._extract_main_condition(query.lower()),
            'raw_results': [],
            'filtered_results': [],
            'final_results': []
        }
        
        raw_results = self.vector_store.hybrid_search(query, n_results=n_results * 3)
        debug_info['raw_results'] = [
            {
                'content_preview': r['content'][:100] + '...',
                'source': r['metadata']['topic_title'],
                'source_dataset': r['metadata'].get('source_dataset', 'unknown'),
                'raw_score': r.get('score', 0),
                'distance': r.get('distance', 0),
                'quality': r['metadata'].get('quality_score', 0),
                'concepts': r['metadata'].get('medical_concepts', ''),
                'is_relevant': self._is_doc_relevant(r, query)
            }
            for r in raw_results[:10]
        ]
        
        intent = debug_info['intent_analysis']
        filtered_results = self._filter_with_strict_relevance(raw_results, intent, query)
        debug_info['filtered_results'] = [
            {
                'content_preview': r['content'][:100] + '...',
                'source': r['metadata']['topic_title'],
                'source_dataset': r['metadata'].get('source_dataset', 'unknown'),
                'final_score': r.get('combined_score', 0),
                'boost_applied': r.get('combined_score', 0) / r.get('score', 1) if r.get('score', 0) > 0 else 1,
                'is_relevant': self._is_doc_relevant(r, query)
            }
            for r in filtered_results[:8]
        ]
        
        final_results = self._ensure_diversity(filtered_results, settings.MAX_SAME_TOPIC_RESULTS)
        debug_info['final_results'] = [
            {
                'content_preview': r['content'][:100] + '...',
                'source': r['metadata']['topic_title'],
                'source_dataset': r['metadata'].get('source_dataset', 'unknown'),
                'final_score': r.get('combined_score', 0),
                'topic_id': r['metadata']['topic_id'],
                'is_relevant': self._is_doc_relevant(r, query)
            }
            for r in final_results[:n_results]
        ]
        
        return debug_info