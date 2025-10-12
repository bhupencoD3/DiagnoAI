import tiktoken
import json
from typing import Dict, List, Any
import argparse
import os

class FDADrugChunker:
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.encoding = tiktoken.encoding_for_model(model)
    
    def count_tokens(self, text: str) -> int:
        """Calculate token count for text using specified model encoding"""
        return len(self.encoding.encode(text))
    
    def create_content_string(self, drug_data: Dict) -> str:
        """Construct optimized content string from drug data"""
        content_parts = []
        
        if drug_data.get('openfda', {}).get('brand_name'):
            content_parts.append(f"Brand Name: {', '.join(drug_data['openfda']['brand_name'])}")
        
        if drug_data.get('purpose'):
            purposes = ' '.join(drug_data['purpose'])
            content_parts.append(f"Purpose: {purposes}")
        
        if drug_data.get('active_ingredient'):
            ingredients = ' '.join(drug_data['active_ingredient'])
            content_parts.append(f"Active Ingredients: {ingredients}")
        
        if drug_data.get('indications_and_usage'):
            indications = ' '.join(drug_data['indications_and_usage'])
            content_parts.append(f"Indications: {indications}")
        
        if drug_data.get('dosage_and_administration'):
            dosage = ' '.join(drug_data['dosage_and_administration'])
            content_parts.append(f"Dosage: {dosage}")
        
        if drug_data.get('warnings'):
            warnings = ' '.join(drug_data['warnings'])
            if len(warnings) > 500:
                warnings = warnings[:500] + "..."
            content_parts.append(f"Warnings: {warnings}")
        
        if drug_data.get('openfda', {}).get('generic_name'):
            content_parts.append(f"Generic Name: {', '.join(drug_data['openfda']['generic_name'])}")
        
        if drug_data.get('openfda', {}).get('route'):
            content_parts.append(f"Route: {', '.join(drug_data['openfda']['route'])}")
        
        if drug_data.get('openfda', {}).get('manufacturer_name'):
            content_parts.append(f"Manufacturer: {', '.join(drug_data['openfda']['manufacturer_name'])}")
        
        if drug_data.get('inactive_ingredient'):
            inactive = ' '.join(drug_data['inactive_ingredient'])
            if len(inactive) < 200:
                content_parts.append(f"Inactive Ingredients: {inactive}")
        
        return "\n".join(content_parts)
    
    def create_metadata(self, drug_data: Dict) -> Dict:
        """Extract relevant metadata for drug filtering and organization"""
        openfda = drug_data.get('openfda', {})
        return {
            "brand_name": openfda.get('brand_name', [None])[0],
            "generic_name": openfda.get('generic_name', [None])[0],
            "product_type": openfda.get('product_type', [None])[0],
            "route": openfda.get('route', [None])[0],
            "manufacturer": openfda.get('manufacturer_name', [None])[0],
            "substance_name": openfda.get('substance_name', [None])[0],
            "product_ndc": openfda.get('product_ndc', [None])[0],
            "has_warnings": bool(drug_data.get('warnings')),
            "has_dosage": bool(drug_data.get('dosage_and_administration')),
            "source_dataset": "fda_drugs",
            "set_id": drug_data.get('set_id'),
            "id": drug_data.get('id')
        }
    
    def create_chunk(self, drug_data: Dict, content: str, metadata: Dict, 
                    chunk_num: int, total_chunks: int, chunk_strategy: str = "single") -> Dict:
        """Generate standardized chunk document with comprehensive metadata"""
        brand_name = metadata['brand_name'] or 'unknown_drug'
        safe_brand_name = "".join(c for c in brand_name if c.isalnum() or c in ('-', '_')).rstrip()
        chunk_id = f"fda_{safe_brand_name}_{chunk_num}"
        
        return {
            "chunk_id": chunk_id,
            "doc_id": drug_data.get('id', 'unknown'),
            "content": content,
            "metadata": metadata,
            "chunk_number": chunk_num,
            "total_chunks": total_chunks,
            "word_count": len(content.split()),
            "char_count": len(content),
            "token_count": self.count_tokens(content),
            "source_dataset": "fda_drugs",
            "chunk_strategy": chunk_strategy,
            "brand_name": brand_name
        }
    
    def chunk_by_sections(self, drug_data: Dict, base_metadata: Dict, max_tokens: int) -> List[Dict]:
        """Split drug data into logical sections based on content type"""
        sections = []
        
        section_definitions = [
            {
                'name': 'basic_info',
                'fields': ['openfda', 'purpose', 'active_ingredient', 'indications_and_usage'],
                'priority': 1
            },
            {
                'name': 'usage_instructions', 
                'fields': ['dosage_and_administration', 'warnings', 'stop_use'],
                'priority': 2
            },
            {
                'name': 'safety_info',
                'fields': ['pregnancy_or_breast_feeding', 'keep_out_of_reach_of_children', 'do_not_use'],
                'priority': 3
            },
            {
                'name': 'additional_info',
                'fields': ['inactive_ingredient', 'storage_and_handling', 'questions'],
                'priority': 4
            }
        ]
        
        for section_def in section_definitions:
            section_data = {}
            for field in section_def['fields']:
                if field in drug_data and drug_data[field]:
                    section_data[field] = drug_data[field]
            
            if section_data:
                content = self.create_content_string(section_data)
                token_count = self.count_tokens(content)
                sections.append({
                    'name': section_def['name'],
                    'content': content,
                    'token_count': token_count,
                    'priority': section_def['priority']
                })
        
        chunks = []
        current_chunk_sections = []
        current_token_count = 0
        
        for section in sorted(sections, key=lambda x: x['priority']):
            if current_token_count + section['token_count'] <= max_tokens:
                current_chunk_sections.append(section)
                current_token_count += section['token_count']
            else:
                if current_chunk_sections:
                    chunk_content = "\n\n".join([s['content'] for s in current_chunk_sections])
                    section_names = [s['name'] for s in current_chunk_sections]
                    
                    chunk_metadata = base_metadata.copy()
                    chunk_metadata['sections_included'] = section_names
                    
                    chunk = self.create_chunk(
                        drug_data, 
                        chunk_content, 
                        chunk_metadata,
                        len(chunks) + 1, 
                        None,
                        "section_combination"
                    )
                    chunks.append(chunk)
                
                current_chunk_sections = [section]
                current_token_count = section['token_count']
        
        if current_chunk_sections:
            chunk_content = "\n\n".join([s['content'] for s in current_chunk_sections])
            section_names = [s['name'] for s in current_chunk_sections]
            
            chunk_metadata = base_metadata.copy()
            chunk_metadata['sections_included'] = section_names
            
            chunk = self.create_chunk(
                drug_data, 
                chunk_content, 
                chunk_metadata,
                len(chunks) + 1, 
                None,
                "section_combination"
            )
            chunks.append(chunk)
        
        for i, chunk in enumerate(chunks):
            chunk['total_chunks'] = len(chunks)
            chunk['chunk_number'] = i + 1
        
        return chunks
    
    def chunk_drug_data(self, drug_data: Dict, max_tokens: int = 8000) -> List[Dict]:
        """Process single drug record into appropriately sized chunks"""
        base_metadata = self.create_metadata(drug_data)
        
        content = self.create_content_string(drug_data)
        token_count = self.count_tokens(content)
        
        if token_count <= max_tokens:
            return [self.create_chunk(drug_data, content, base_metadata, chunk_num=1, total_chunks=1, chunk_strategy="single")]
        else:
            return self.chunk_by_sections(drug_data, base_metadata, max_tokens)
    
    def process_drugs_in_batches(self, input_file: str, output_file: str, max_tokens: int = 8000, batch_size: int = 100):
        """Process FDA dataset using batch processing for memory efficiency"""
        print(f"Starting data processing from {input_file}")
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        stats = {
            'total_drugs': 0,
            'single_chunk_drugs': 0,
            'multi_chunk_drugs': 0,
            'total_chunks': 0,
            'token_stats': [],
            'failed_drugs': 0
        }
        
        with open(input_file, 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)
        stats['total_drugs'] = total_lines
        
        print(f"Processing {total_lines} drug records in batches of {batch_size}")
        
        with open(input_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:
            
            current_batch = []
            processed_drugs = 0
            
            for line_num, line in enumerate(infile, 1):
                try:
                    drug = json.loads(line)
                    current_batch.append(drug)
                    
                    if len(current_batch) >= batch_size or line_num == total_lines:
                        self._process_batch(current_batch, outfile, stats, max_tokens)
                        processed_drugs += len(current_batch)
                        current_batch = []
                        
                        if processed_drugs % 500 == 0:
                            print(f"Progress: {processed_drugs}/{total_lines} drugs processed")
                            
                except json.JSONDecodeError as e:
                    print(f"JSON decoding error at line {line_num}: {e}")
                    stats['failed_drugs'] += 1
                    continue
                except Exception as e:
                    print(f"Processing error at line {line_num}: {e}")
                    stats['failed_drugs'] += 1
                    continue
        
        self._print_statistics(stats)
        
        return stats
    
    def _process_batch(self, batch: List[Dict], outfile, stats: Dict, max_tokens: int):
        """Process individual batch of drug records"""
        for drug in batch:
            try:
                chunks = self.chunk_drug_data(drug, max_tokens)
                
                if len(chunks) == 1:
                    stats['single_chunk_drugs'] += 1
                else:
                    stats['multi_chunk_drugs'] += 1
                
                stats['total_chunks'] += len(chunks)
                
                for chunk in chunks:
                    stats['token_stats'].append(chunk['token_count'])
                    outfile.write(json.dumps(chunk, ensure_ascii=False) + '\n')
                    
            except Exception as e:
                print(f"Error processing drug record: {e}")
                stats['failed_drugs'] += 1
                continue
    
    def _print_statistics(self, stats: Dict):
        """Display comprehensive processing statistics"""
        print(f"\n{'='*50}")
        print(f"PROCESSING COMPLETION SUMMARY")
        print(f"{'='*50}")
        print(f"Total drugs processed: {stats['total_drugs']}")
        print(f"Single-chunk drugs: {stats['single_chunk_drugs']}")
        print(f"Multi-chunk drugs: {stats['multi_chunk_drugs']}")
        print(f"Failed processing attempts: {stats['failed_drugs']}")
        print(f"Total chunks generated: {stats['total_chunks']}")
        
        if stats['token_stats']:
            avg_tokens = sum(stats['token_stats']) / len(stats['token_stats'])
            max_tokens = max(stats['token_stats'])
            chunks_under_limit = sum(1 for t in stats['token_stats'] if t <= 8000)
            
            print(f"Average tokens per chunk: {avg_tokens:.1f}")
            print(f"Maximum tokens in any chunk: {max_tokens}")
            print(f"Chunks within 8K token limit: {chunks_under_limit}/{len(stats['token_stats'])}")
            
            if max_tokens > 8000:
                print(f"Note: {len(stats['token_stats']) - chunks_under_limit} chunks exceed 8K token limit")
            else:
                print("All chunks comply with 8K token limit")
    
    def verify_chunks(self, chunk_file: str, max_tokens: int = 8000):
        """Validate that all chunks meet token limit requirements"""
        print(f"Validating chunks in {chunk_file}")
        
        over_limit = []
        total_chunks = 0
        
        with open(chunk_file, 'r', encoding='utf-8') as f:
            for line in f:
                total_chunks += 1
                chunk = json.loads(line)
                if chunk.get('token_count', 0) > max_tokens:
                    over_limit.append((chunk.get('chunk_id', 'unknown'), chunk['token_count']))
        
        if over_limit:
            print(f"{len(over_limit)} chunks exceed {max_tokens} token limit:")
            for chunk_id, tokens in over_limit[:10]:
                print(f"  - {chunk_id}: {tokens} tokens")
            return False
        else:
            print(f"All {total_chunks} chunks comply with {max_tokens} token limit")
            return True

def main():
    parser = argparse.ArgumentParser(description='Process FDA drug data into embedding-ready chunks')
    parser.add_argument('--input', type=str, required=True, help='Input JSONL file containing FDA drug data')
    parser.add_argument('--output', type=str, required=True, help='Output JSONL file for processed chunks')
    parser.add_argument('--max_tokens', type=int, default=8000, help='Maximum tokens allowed per chunk')
    parser.add_argument('--batch_size', type=int, default=100, help='Number of records to process in each batch')
    parser.add_argument('--verify', action='store_true', help='Perform chunk verification after processing')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}")
        return
    
    chunker = FDADrugChunker()
    
    stats = chunker.process_drugs_in_batches(
        input_file=args.input,
        output_file=args.output,
        max_tokens=args.max_tokens,
        batch_size=args.batch_size
    )
    
    if args.verify:
        chunker.verify_chunks(args.output, args.max_tokens)

if __name__ == "__main__":
    main()