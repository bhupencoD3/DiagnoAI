#!/usr/bin/env python3
"""
Medical Meadow QA Processing Pipeline
Standalone pipeline that doesn't interfere with MedlinePlus processing
"""

import sys
import os
import logging
from datetime import datetime
from src.data_processing.meadow.meadow_pipeline import MedicalMeadowPipeline
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def main():
    """Run the standalone Medical Meadow QA processing pipeline"""
    JSON_FILE_PATH = "data/raw/medical_meadow_wikidoc.json"
    OUTPUT_DIR = "data/processed/meadow_chunks"
    
    os.makedirs(os.path.dirname(JSON_FILE_PATH), exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(JSON_FILE_PATH):
        logging.error(f"Medical Meadow input file not found: {JSON_FILE_PATH}")
        logging.info("Please ensure your Medical Meadow JSON file exists in data/raw/")
        return
    
    logging.info("Medical Meadow QA Processing Pipeline")
    
    try:
        pipeline = MedicalMeadowPipeline()
        chunks = pipeline.run_pipeline(JSON_FILE_PATH, OUTPUT_DIR)
        
        logging.info("Medical Meadow QA processing completed successfully")
        logging.info(f"Output directory: {OUTPUT_DIR}")
        
    except Exception as e:
        logging.error(f"Pipeline failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()