import xml.etree.ElementTree as ET
import html
from typing import List, Dict, Any, Generator
import re
from bs4 import BeautifulSoup

class MedlinePlusXMLParser:
    def __init__(self):
        self.namespace = {'': 'http://medlineplus.gov'}
    
    def parse_health_topics_batch(self, xml_file_path: str, batch_size: int = 50) -> Generator[List[Dict[str, Any]], None, None]:
        """Parse XML file in batches to manage memory usage efficiently"""
        print(f"Parsing XML file in batches: {xml_file_path}")
        
        try:
            context = ET.iterparse(xml_file_path, events=('end',))
            
            batch = []
            count = 0
            
            for event, elem in context:
                if elem.tag == 'health-topic':
                    topic_data = self._extract_topic_data(elem)
                    if topic_data and topic_data.get('language') == 'English':
                        batch.append(topic_data)
                        count += 1
                    
                    elem.clear()
                    
                    if len(batch) >= batch_size:
                        yield batch
                        batch = []
                        print(f"Processed {count} topics so far")
            
            if batch:
                yield batch
            
            print(f"Completed parsing {count} English health topics")
            
        except ET.ParseError as e:
            print(f"XML parsing error occurred: {e}")
        except Exception as e:
            print(f"Unexpected error during parsing: {e}")
    
    def _extract_topic_data(self, topic_element) -> Dict[str, Any]:
        """Extract and structure data from health topic elements"""
        try:
            topic_id = topic_element.get('id')
            title = topic_element.get('title', '').strip()
            url = topic_element.get('url', '')
            language = topic_element.get('language', 'English')
            
            if not title:
                return None
            
            synonyms = []
            for also_called in topic_element.findall('also-called'):
                synonym = also_called.text.strip() if also_called.text else ''
                if synonym:
                    synonyms.append(synonym)
            
            full_summary_element = topic_element.find('full-summary')
            if full_summary_element is not None and full_summary_element.text:
                raw_content = full_summary_element.text
                clean_content = self._clean_html_content_preserve_structure(raw_content)
            else:
                clean_content = ""
            
            mesh_terms = []
            for mesh_heading in topic_element.findall('mesh-heading'):
                descriptor = mesh_heading.find('descriptor')
                if descriptor is not None and descriptor.text:
                    mesh_terms.append(descriptor.text.strip())
            
            topic_data = {
                'id': topic_id,
                'title': title,
                'url': url,
                'language': language,
                'synonyms': synonyms,
                'content': clean_content,
                'mesh_terms': mesh_terms,
                'content_length': len(clean_content),
                'word_count': len(clean_content.split())
            }
            
            return topic_data
            
        except Exception as e:
            print(f"Error occurred while processing topic: {e}")
            return None
    
    def _clean_html_content_preserve_structure(self, html_content: str) -> str:
        """Clean HTML content while maintaining document structure and readability"""
        if not html_content:
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for unwanted in soup(["script", "style", "meta", "link"]):
                unwanted.decompose()
            
            text_parts = []
            
            for element in soup.find_all(['p', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4']):
                if element.name == 'p':
                    text = element.get_text().strip()
                    if text:
                        text_parts.append(text)
                elif element.name in ['ul', 'ol']:
                    list_items = []
                    for li in element.find_all('li'):
                        item_text = li.get_text().strip()
                        if item_text:
                            list_items.append(f"• {item_text}")
                    if list_items:
                        text_parts.append("\n".join(list_items))
                elif element.name in ['h1', 'h2', 'h3', 'h4']:
                    heading_text = element.get_text().strip()
                    if heading_text:
                        text_parts.append(f"\n{heading_text}\n")
            
            if not text_parts:
                all_text = soup.get_text()
                all_text = re.sub(r'\n+', '\n', all_text)
                all_text = re.sub(r' +', ' ', all_text)
                return all_text.strip()
            
            result = "\n\n".join(text_parts)
            
            result = re.sub(r'\n\s*\n', '\n\n', result)
            result = re.sub(r'[ \t]+', ' ', result)
            
            return result.strip()
            
        except Exception as e:
            print(f"Error during HTML content cleaning: {e}")
            clean_text = re.sub(r'<[^>]+>', ' ', html_content)
            clean_text = re.sub(r'\s+', ' ', clean_text)
            return clean_text.strip()