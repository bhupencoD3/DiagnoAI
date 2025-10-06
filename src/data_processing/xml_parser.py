# src/data_processing/xml_parser.py
import xml.etree.ElementTree as ET
import html
from typing import List, Dict, Any, Generator
import re

class MedlinePlusXMLParser:
    def __init__(self):
        self.namespace = {'': 'http://medlineplus.gov'}
    
    def parse_health_topics_batch(self, xml_file_path: str, batch_size: int = 50) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Parse XML in batches to save memory
        """
        print(f"📖 Parsing XML file in batches: {xml_file_path}")
        
        try:
            # Use iterparse for memory efficiency
            context = ET.iterparse(xml_file_path, events=('end',))
            
            batch = []
            count = 0
            
            for event, elem in context:
                if elem.tag == 'health-topic':
                    topic_data = self._extract_topic_data(elem)
                    if topic_data and topic_data.get('language') == 'English':
                        batch.append(topic_data)
                        count += 1
                    
                    # Clear the element to save memory
                    elem.clear()
                    
                    # Yield batch when size is reached
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                        print(f"📦 Processed {count} topics...")
            
            # Yield final batch
            if batch:
                yield batch
            
            print(f"✅ Successfully parsed {count} English health topics")
            
        except ET.ParseError as e:
            print(f"❌ XML parsing error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    def _extract_topic_data(self, topic_element) -> Dict[str, Any]:
        """Extract structured data from a single health-topic element"""
        try:
            # Basic metadata
            topic_id = topic_element.get('id')
            title = topic_element.get('title', '').strip()
            url = topic_element.get('url', '')
            language = topic_element.get('language', 'English')
            
            if not title:
                return None
            
            # Extract also-called (synonyms)
            synonyms = []
            for also_called in topic_element.findall('also-called'):
                synonym = also_called.text.strip() if also_called.text else ''
                if synonym:
                    synonyms.append(synonym)
            
            # Extract FULL medical content from full-summary
            full_summary_element = topic_element.find('full-summary')
            if full_summary_element is not None and full_summary_element.text:
                raw_content = full_summary_element.text
                clean_content = self._clean_html_content(raw_content)
            else:
                clean_content = ""
            
            # Extract MeSH terms
            mesh_terms = []
            for mesh_heading in topic_element.findall('mesh-heading'):
                descriptor = mesh_heading.find('descriptor')
                if descriptor is not None and descriptor.text:
                    mesh_terms.append(descriptor.text.strip())
            
            # Extract related topics
            related_topics = []
            for related in topic_element.findall('related-topic'):
                related_title = related.text.strip() if related.text else ''
                if related_title:
                    related_topics.append(related_title)
            
            # Extract groups/categories
            groups = []
            for group in topic_element.findall('group'):
                group_name = group.text.strip() if group.text else ''
                if group_name:
                    groups.append(group_name)
            
            # Build structured data
            topic_data = {
                'id': topic_id,
                'title': title,
                'url': url,
                'language': language,
                'synonyms': synonyms,
                'content': clean_content,
                'mesh_terms': mesh_terms,
                'related_topics': related_topics,
                'groups': groups,
                'content_length': len(clean_content),
                'word_count': len(clean_content.split())
            }
            
            return topic_data
            
        except Exception as e:
            print(f"Error processing topic: {e}")
            return None
    
    def _clean_html_content(self, html_content: str) -> str:
        """Clean HTML entities and extract readable text"""
        if not html_content:
            return ""
        
        try:
            unescaped = html.unescape(html_content)
            clean_text = re.sub(r'<[^>]+>', ' ', unescaped)
            clean_text = re.sub(r'\s+', ' ', clean_text)
            return clean_text.strip()
        except Exception as e:
            print(f"HTML cleaning error: {e}")
            return html_content