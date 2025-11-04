# DiagnoAI Data Schemas

This doc defines JSON schemas for processed data, API payloads, and internal structures. Uses JSON Schema format for validation (e.g., via `pydantic-jsonschema`). All schemas are extensible.

## 1. Processed Chunks (medical_knowledge_base_v2.json)
Unified KB from datasets (MedlinePlus/Meadow/OpenFDA). Array of chunk objects.

**Schema** (JSON Schema Draft 2020-12):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "chunk_id": {"type": "string", "description": "Unique ID"},
      "content": {"type": "string", "description": "Chunk text (200-800 words)"},
      "metadata": {
        "type": "object",
        "properties": {
          "topic_title": {"type": "string"},
          "topic_id": {"type": "string"},
          "source_dataset": {"type": "string", "enum": ["medline_plus", "medical_meadow", "fda_drugs"]},
          "chunk_number": {"type": "integer"},
          "word_count": {"type": "integer"},
          "quality_score": {"type": "number", "minimum": 0, "maximum": 100},
          "medical_concepts": {"type": "array", "items": {"type": "string"}},
          "synonyms": {"type": "array", "items": {"type": "string"}},
          "mesh_terms": {"type": "array", "items": {"type": "string"}},
          "source_url": {"type": "string"},
          "has_structured_content": {"type": "boolean"},
          "qa_format": {"type": "boolean"}
        },
        "required": ["source_dataset", "topic_title"]
      }
    },
    "required": ["chunk_id", "content", "metadata"]
  }
}
```

**Example Chunk** (Meadow QA):
```json
{
  "chunk_id": "meadow_qa_123",
  "content": "Q: What causes diabetes? A: Insulin resistance...",
  "metadata": {
    "topic_title": "Diabetes Etiology",
    "source_dataset": "medical_meadow",
    "quality_score": 85.2,
    "medical_concepts": ["diabetes", "insulin"],
    "qa_format": true
  }
}
```

## 2. API Request/Response Schemas
From Pydantic models in [../src/api/models.py](../src/api/models.py).

### QueryRequest (POST /query)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "query": {"type": "string", "minLength": 1},
    "n_results": {"type": "integer", "minimum": 1, "maximum": 20},
    "context_type": {"type": "string"},
    "temperature": {"type": "number", "minimum": 0, "maximum": 1},
    "max_tokens": {"type": "integer", "minimum": 100, "maximum": 2000},
    "request_id": {"type": "string"}
  },
  "required": ["query"]
}
```

### QueryResponse (POST /query)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "answer": {"type": "string"},
    "sources": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "content": {"type": "string"},
          "metadata": {"$ref": "#/definitions/ChunkMetadata"},
          "combined_score": {"type": "number"}
        }
      }
    },
    "retrieval_metrics": {
      "type": "object",
      "properties": {
        "relevance_score": {"type": "number"},
        "sources_used": {"type": "integer"},
        "avg_combined_score": {"type": "number"}
      }
    },
    "processing_time": {"type": "number"},
    "request_id": {"type": "string"}
  },
  "definitions": {
    "ChunkMetadata": { /* Same as above metadata */ }
  },
  "required": ["answer", "sources", "retrieval_metrics"]
}
```

### MedicalTermResponse (POST /medical-term)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "term": {"type": "string"},
    "definition": {"type": "string"},
    "category": {"type": "string"},
    "severity": {"type": "string", "enum": ["emergency", "serious", "moderate", "mild", "info"]},
    "source": {"type": "string"},
    "found": {"type": "boolean"}
  },
  "required": ["term", "definition", "severity", "source", "found"]
}
```

## 3. Metrics Files
- **meadow_metrics.json**: QA quality stats. Schema: `{ "total_chunks": int, "avg_quality": number, "quality_analysis": object }`.
- **medlineplus_chunking_metrics.json**: Chunking stats. Schema: `{ "total_chunks": int, "avg_chunk_size_words": number, "size_distribution": string }`.

## Validation Tips
- Use `pydantic` in code: `QueryRequest.model_validate(data)`.
- Tools: jsonschema.net for testing; integrate with CI (e.g., pre-commit hooks).
- Evolution: v1.0 schemas; bump on changes (see CHANGELOG.md).

For raw files, see [../data/processed/](../data/processed/).