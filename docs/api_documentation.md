# DiagnoAI API Documentation

This document details the REST API for DiagnoAI, a medical RAG assistant. All endpoints are served via FastAPI at `/` (e.g., http://localhost:8000). Interactive docs available at `/docs` (Swagger) or `/redoc` (ReDoc).

**Base URL**: `http://<host>:8000`  
**Auth**: None (demo-only; add API keys in prod via middleware).  
**Rate Limits**: None enforced (add via `slowapi` if needed).  
**Errors**: Standard HTTP (e.g., 422 for validation, 503 for service down); responses include `detail` field.

## Core Endpoints

### POST /query
Process a medical query using RAG + LLM (Grok/Ollama). Returns structured answer with sources/metrics.

**Request Body** (JSON, required):
| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `query` | str | Medical question (e.g., "Symptoms of diabetes?") | - |
| `n_results` | int | # of retrieved docs | 4 |
| `context_type` | str | Optional filter (e.g., "symptoms") | null |
| `temperature` | float | LLM creativity (0.0-1.0) | 0.1 |
| `max_tokens` | int | Max response length | 1200 |
| `request_id` | str | Unique ID for cancellation/tracking | null |

**Example Request**:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the symptoms and treatment for diabetes?",
    "n_results": 5,
    "temperature": 0.1
  }'
```

**Response** (200 OK, JSON):
| Field | Type | Description |
|-------|------|-------------|
| `answer` | str | Generated response (Markdown-formatted bullets/headers) |
| `sources` | array[object] | Retrieved docs: `{content: str, metadata: object, combined_score: float}` |
| `retrieval_metrics` | object | `{relevance_score: float, sources_used: int, avg_combined_score: float}` |
| `processing_time` | float | Seconds elapsed |
| `request_id` | str | Echoed ID |

**Example Response**:
```json
{
  "answer": "**Diabetes Symptoms**\n• Increased thirst...\n**Medical Disclaimer:** ...",
  "sources": [{"content": "...", "metadata": {"source_dataset": "medline_plus"}, "combined_score": 0.85}],
  "retrieval_metrics": {"relevance_score": 0.85, "sources_used": 3, "avg_combined_score": 0.78},
  "processing_time": 2.45,
  "request_id": "req_abc123"
}
```

**Errors**:
- 422: Invalid input (e.g., empty query).
- 499: Client cancelled (via `/cancel-query`).
- 503: Service unavailable (e.g., no vector store).

### POST /medical-term
Lookup definition for a medical term (local dict + MedlinePlus/Wiki fallback).

**Request Body** (JSON, required):
| Field | Type | Description |
|-------|------|-------------|
| `term` | str | Term to define (e.g., "hypertension") | - |

**Example Request**:
```bash
curl -X POST http://localhost:8000/medical-term \
  -H "Content-Type: application/json" \
  -d '{"term": "hypertension"}'
```

**Response** (200 OK, JSON):
| Field | Type | Description |
|-------|------|-------------|
| `term` | str | Original term |
| `definition` | str | Detailed explanation |
| `category` | str | e.g., "cardiovascular" |
| `severity` | str | e.g., "serious" (Emergency/Serious/Moderate/Mild/Info) |
| `source` | str | e.g., "DiagnoAI Medical Dictionary" |
| `found` | bool | True if definition available |

**Example Response**:
```json
{
  "term": "hypertension",
  "definition": "High blood pressure... (full text)",
  "category": "cardiovascular",
  "severity": "serious",
  "source": "MedlinePlus Medical Encyclopedia",
  "found": true
}
```

**Errors**:
- 422: Empty term.

### POST /cancel-query
Cancel an active query by ID (supports long-running LLM calls).

**Request Body** (JSON, required):
| Field | Type | Description |
|-------|------|-------------|
| `request_id` | str | ID from /query response | - |

**Response** (200 OK, JSON): `{"status": "cancelled", "request_id": "req_abc123"}` or `{"status": "not_found"}`.

## Health/Monitoring Endpoints
All return JSON; used for K8s probes.

- **GET /health**: Full status (vector/LLM healthy? Docs count?). Example: `{"status": "healthy", "vector_store": {"document_count": 12635}}`.
- **GET /healthz**: Liveness (simple "alive"/"unhealthy").
- **GET /ready**: Readiness (services ready? "ready"/"degraded").
- **GET /service-status**: Debug details (active requests, model info).
- **GET /dictionary-stats**: Dict overview (e.g., `{"total_terms": 25, "categories": ["cardiovascular", ...]}`).

## Implementation Notes
- **Pydantic Models**: Defined in [../src/api/models.py](../src/api/models.py) for validation.
- **Security**: No auth; prod: Add JWT/middleware. Sanitize inputs to prevent prompt injection.
- **Testing**: Run `pytest ../app/tests/` for endpoint coverage.
- **Extensions**: Add auth via `fastapi-security`; rate-limit with `slowapi`.

For code-level details, see [../app/main.py](../app/main.py).