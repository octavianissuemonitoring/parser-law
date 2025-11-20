# AI Integration - API Documentation

## Overview

API endpoints pentru procesarea automată a actelor normative de către servicii AI externe.

**Toate endpoint-urile AI sunt grupate sub**: `/api/v1/ai/`

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        AI SERVICE                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 1: Get acts needing processing            │
    │  GET /api/v1/ai/acte/pending                    │
    │  ?ai_status=pending&has_domenii=true            │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 2: Get complete act structure             │
    │  GET /api/v1/ai/acte/{id}                       │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 3: Mark article as processing             │
    │  POST /api/v1/ai/articole/{id}/mark-processing  │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 4: Analyze articles with AI               │
    │  - Extract issues from article text             │
    │  - Calculate relevance scores                   │
    │  - Determine domain context                     │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 5: Create new issues (if needed)          │
    │  POST /api/v1/issues                            │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 6: Link issues to articles (Tier 1)       │
    │  POST /api/v1/issues/link                       │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 7: Link issues to structures (Tier 2)     │
    │  POST /api/v1/issues/link-structure             │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 8: Mark article as processed              │
    │  POST /api/v1/ai/articole/{id}/mark-processed   │
    └─────────────────────────────────────────────────┘
```

---

## API Endpoints Reference

### 📋 Document Retrieval

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ai/acte/pending` | Get list of acts needing processing |
| GET | `/api/v1/ai/acte/{id}` | **⭐ MAIN** - Get complete act with all articles |

### 🔄 Status Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/articole/{id}/mark-processing` | Mark article as being processed |
| POST | `/api/v1/ai/articole/{id}/mark-processed` | Mark article as successfully processed |
| POST | `/api/v1/ai/articole/{id}/mark-error` | Mark article as failed with error |

### 📊 Processing Control (Internal/Manual)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/process` | Trigger AI processing (background) |
| GET | `/api/v1/ai/process/sync` | Trigger AI processing (synchronous) |
| GET | `/api/v1/ai/status` | Get processing statistics |
| GET | `/api/v1/ai/pending` | List pending articles |
| GET | `/api/v1/ai/errors` | List failed articles |
| POST | `/api/v1/ai/retry/{id}` | Retry processing for article |
| POST | `/api/v1/ai/reset/{id}` | Reset article status to pending |

### 🔗 Issues Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/issues` | Create new issue |
| POST | `/api/v1/issues/link` | Link issue to document (Tier 1) |
| POST | `/api/v1/issues/link-structure` | Link issue to structure (Tier 2) |
| DELETE | `/api/v1/issues/unlink` | Remove issue link |

---

## Detailed Endpoint Documentation

### 1. Get Acts for Processing

**Endpoint**: `GET /api/v1/ai/acte/pending`

**Purpose**: Retrieve list of legislative acts that need AI processing.

**Query Parameters**:
- `ai_status` (default: `pending`)
  - Values: `pending`, `processing`, `processed`, `error`, `needs_reprocessing`
- `has_domenii` (optional)
  - `true`: Only acts with domains
  - `false`: Only acts without domains
  - `null`: All acts
- `limit` (default: 10, max: 100)

**Example Request**:
```bash
GET /api/v1/ai/acte/pending?ai_status=pending&has_domenii=true&limit=5
```

**Example Response**:
```json
[
  {
    "id": 123,
    "tip_act": "LEGE",
    "nr_act": "95",
    "an_act": 2006,
    "titlu_act": "Legea nr. 95/2006 privind reforma în domeniul sănătății",
    "ai_status": "pending",
    "total_articole": 450,
    "pending_articole": 450,
    "domenii": [
      {
        "id": 1,
        "cod": "FARMA",
        "denumire": "Farmacie",
        "culoare": "#4CAF50"
      }
    ]
  }
]
```

---

### 2. Get Complete Act Structure ⭐

**Endpoint**: `GET /api/v1/ai/acte/{act_id}`

**Purpose**: **MAIN ENDPOINT** - Retrieve complete act with ALL articles for processing.

**Path Parameters**:
- `act_id` - Act ID

**Query Parameters**:
- `include_processed` (default: `false`)
  - `false`: Only pending articles
  - `true`: All articles

**Example Request**:
```bash
GET /api/v1/ai/acte/123?include_processed=false
```

**Example Response**:
```json
{
  "id": 123,
  "tip_act": "LEGE",
  "nr_act": "95",
  "data_act": "2006-04-05",
  "an_act": 2006,
  "titlu_act": "Legea nr. 95/2006 privind reforma în domeniul sănătății",
  "emitent_act": "Parlament",
  "url_legislatie": "https://legislatie.just.ro/...",
  "ai_status": "pending",
  "ai_processed_at": null,
  "domenii": [
    {
      "id": 1,
      "cod": "FARMA",
      "denumire": "Farmacie",
      "culoare": "#4CAF50"
    }
  ],
  "articole": [
    {
      "id": 1001,
      "articol_nr": "1",
      "articol_label": "Art. 1",
      "titlu_nr": 1,
      "titlu_denumire": "DISPOZIȚII GENERALE",
      "capitol_nr": null,
      "capitol_denumire": null,
      "sectiune_nr": null,
      "sectiune_denumire": null,
      "text_articol": "(1) Prezenta lege stabilește cadrul...",
      "ordine": 1,
      "ai_status": "pending",
      "ai_processed_at": null
    }
  ],
  "total_articole": 450,
  "pending_articole": 450
}
```

**Key Fields**:
- `articole[].text_articol` - Full article text for AI analysis
- `articole[].titlu_nr`, `capitol_nr`, `sectiune_nr` - Hierarchy
- `domenii[]` - Domains assigned to act (use for issue linking)

---

### 3. Mark Article as Processing

**Endpoint**: `POST /api/v1/ai/articole/{articol_id}/mark-processing`

**Purpose**: Set `ai_status='processing'` to prevent duplicate processing.

**Response**: `204 No Content`

---

### 4. Mark Article as Processed

**Endpoint**: `POST /api/v1/ai/articole/{articol_id}/mark-processed`

**Purpose**: Set `ai_status='processed'` and record timestamp.

**Response**: `204 No Content`

---

### 5. Mark Article as Error

**Endpoint**: `POST /api/v1/ai/articole/{articol_id}/mark-error`

**Query Parameters**:
- `error_message` (required) - Error description

**Response**:
```json
{
  "message": "Article marked as error",
  "error": "API timeout after 30s"
}
```

---

### 6. Create Issue

**Endpoint**: `POST /api/v1/issues`

**Request Body**:
```json
{
  "denumire": "Lipsa specificații pentru eticheta exterioară",
  "descriere": "Articolul nu specifică informațiile obligatorii...",
  "confidence_score": 0.89,
  "source": "ai"
}
```

**Response**:
```json
{
  "id": 42,
  "denumire": "Lipsa specificații pentru eticheta exterioară",
  "data_creare": "2025-01-15T10:30:45.123Z"
}
```

---

### 7. Link Issue to Article (Tier 1)

**Endpoint**: `POST /api/v1/issues/link`

**Purpose**: Link issue directly to document (article/act/annex).

**Request Body**:
```json
{
  "document_type": "articol",
  "document_id": 1001,
  "issue_id": 42,
  "domeniu_id": 1,
  "relevance_score": 0.89
}
```

**Fields**:
- `document_type`: `"articol"`, `"act"`, or `"anexa"`
- `domeniu_id`: **MANDATORY** - Domain context
- `relevance_score`: AI confidence (0.0-1.0)

---

### 8. Link Issue to Structure (Tier 2)

**Endpoint**: `POST /api/v1/issues/link-structure`

**Purpose**: Link issue to structural element (title/chapter/section).

**Request Body**:
```json
{
  "act_id": 123,
  "structure_type": "capitol",
  "titlu_nr": 2,
  "titlu_denumire": "AUTORIZAREA MEDICAMENTELOR",
  "capitol_nr": 1,
  "capitol_denumire": "Autorizarea de punere pe piață",
  "issue_id": 42,
  "domeniu_id": 1,
  "relevance_score": 0.85
}
```

**Fields**:
- `structure_type`: `"titlu"`, `"capitol"`, or `"sectiune"`
- Must match structure identifiers from `articole` table

---

## Complete Processing Example (Python)

```python
import requests

API_BASE = "http://localhost:8000/api/v1"

def process_acts():
    """Main AI processing loop."""
    
    # Step 1: Get acts needing processing
    response = requests.get(
        f"{API_BASE}/ai/acte/pending",
        params={"ai_status": "pending", "has_domenii": True, "limit": 5}
    )
    acts = response.json()
    
    for act in acts:
        print(f"Processing Act {act['id']}: {act['titlu_act']}")
        
        # Step 2: Get complete structure
        response = requests.get(f"{API_BASE}/ai/acte/{act['id']}")
        act_data = response.json()
        
        for article in act_data['articole']:
            if article['ai_status'] != 'pending':
                continue
            
            try:
                # Step 3: Mark as processing
                requests.post(f"{API_BASE}/ai/articole/{article['id']}/mark-processing")
                
                # Step 4: Analyze with AI
                issues = analyze_article_with_ai(article['text_articol'])
                
                # Step 5 & 6: Create and link issues
                for issue_data in issues:
                    # Create issue
                    issue_resp = requests.post(
                        f"{API_BASE}/issues",
                        json={
                            "denumire": issue_data['title'],
                            "descriere": issue_data['description'],
                            "confidence_score": issue_data['score'],
                            "source": "ai"
                        }
                    )
                    issue_id = issue_resp.json()['id']
                    
                    # Step 7: Link to article
                    for domain in act_data['domenii']:
                        requests.post(
                            f"{API_BASE}/issues/link",
                            json={
                                "document_type": "articol",
                                "document_id": article['id'],
                                "issue_id": issue_id,
                                "domeniu_id": domain['id'],
                                "relevance_score": issue_data['score']
                            }
                        )
                
                # Step 8: Mark as processed
                requests.post(f"{API_BASE}/ai/articole/{article['id']}/mark-processed")
                
            except Exception as e:
                # Mark as error
                requests.post(
                    f"{API_BASE}/ai/articole/{article['id']}/mark-error",
                    params={"error_message": str(e)}
                )


def analyze_article_with_ai(text: str):
    """Replace with your AI model."""
    # Your AI logic here
    return [{"title": "...", "description": "...", "score": 0.89}]


if __name__ == "__main__":
    process_acts()
```

---

## Domain Context Rules

### Mandatory Domain Assignment

**All issues MUST have domain context** (`domeniu_id` NOT NULL).

### Domain Inheritance

Articles inherit domains from act unless overridden:

1. **Act-level**: User assigns domains when adding act URL
2. **Article-level** (optional): Override for specific articles
3. **Effective domains**: Use `get_articol_domenii()` SQL function

### AI Service Usage

Link issue to **EACH relevant domain** separately:

```python
for domain in act_data['domenii']:
    score = calculate_domain_relevance(issue, domain)
    if score > 0.5:
        link_issue(article_id, issue_id, domain['id'], score)
```

---

## Error Handling

### Status Transitions

```
pending → processing → processed ✓
                     ↘ error ✗
error → needs_reprocessing → processing → ...
```

### Retry Logic

- Exponential backoff for API errors
- Batch processing with checkpoints
- Error threshold → skip after N failures
- Periodic retry of `error` status articles

---

## Testing

```bash
# 1. Get acts
curl http://localhost:8000/api/v1/ai/acte/pending?limit=1

# 2. Get structure
curl http://localhost:8000/api/v1/ai/acte/123

# 3. Mark processing
curl -X POST http://localhost:8000/api/v1/ai/articole/1001/mark-processing

# 4. Create issue
curl -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{"denumire": "Test Issue", "source": "ai", "confidence_score": 0.95}'

# 5. Link issue
curl -X POST http://localhost:8000/api/v1/issues/link \
  -H "Content-Type: application/json" \
  -d '{"document_type": "articol", "document_id": 1001, "issue_id": 42, "domeniu_id": 1, "relevance_score": 0.95}'

# 6. Mark processed
curl -X POST http://localhost:8000/api/v1/ai/articole/1001/mark-processed
```

---

## API Documentation

**Swagger UI**: http://localhost:8000/docs

**OpenAPI Spec**: http://localhost:8000/openapi.json

```
┌─────────────────────────────────────────────────────────────┐
│                        AI SERVICE                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 1: Get acts needing processing            │
    │  GET /api/v1/ai-integration/acte/pending        │
    │  ?ai_status=pending&has_domenii=true            │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 2: Get complete act structure             │
    │  GET /api/v1/ai-integration/acte/{id}/structure │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 3: Analyze articles with AI               │
    │  - Extract issues from article text             │
    │  - Calculate relevance scores                   │
    │  - Determine domain context                     │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 4: Create new issues (if needed)          │
    │  POST /api/v1/issues                            │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 5: Link issues to articles (Tier 1)       │
    │  POST /api/v1/issues/link                       │
    │  {document_type, document_id, issue_id,         │
    │   domeniu_id, relevance_score}                  │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 6: Link issues to structures (Tier 2)     │
    │  POST /api/v1/issues/link-structure             │
    │  {act_id, structure_type, titlu_nr, capitol_nr, │
    │   sectiune_nr, issue_id, domeniu_id}            │
    └─────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────┐
    │  STEP 7: Mark articles as processed             │
    │  POST /api/v1/ai-integration/articole/{id}/     │
    │       mark-processed                            │
    └─────────────────────────────────────────────────┘
```

---

## API Endpoints for AI Service

### 1. Get Acts Needing Processing

**Endpoint**: `GET /api/v1/ai-integration/acte/pending`

**Purpose**: Retrieve list of legislative acts that need AI processing.

**Query Parameters**:
- `ai_status` (default: `pending`) - Filter by status
  - Values: `pending`, `processing`, `processed`, `error`, `needs_reprocessing`
- `has_domenii` (optional) - Filter acts with domain assignments
  - `true`: Only acts that have domains assigned
  - `false`: Only acts without domains
  - `null`: All acts regardless of domains
- `limit` (default: 10, max: 100) - Number of results

**Example Request**:
```bash
GET /api/v1/ai-integration/acte/pending?ai_status=pending&has_domenii=true&limit=5
```

**Example Response**:
```json
[
  {
    "id": 123,
    "tip_act": "LEGE",
    "nr_act": "95",
    "an_act": 2006,
    "titlu_act": "Legea nr. 95/2006 privind reforma în domeniul sănătății",
    "ai_status": "pending",
    "total_articole": 450,
    "pending_articole": 450,
    "domenii": [
      {
        "id": 1,
        "cod": "FARMA",
        "denumire": "Farmacie",
        "culoare": "#4CAF50"
      },
      {
        "id": 5,
        "cod": "SANATATE",
        "denumire": "Sănătate Publică",
        "culoare": "#2196F3"
      }
    ]
  }
]
```

---

### 2. Get Complete Act Structure

**Endpoint**: `GET /api/v1/ai-integration/acte/{act_id}/structure`

**Purpose**: Retrieve complete act with ALL articles in hierarchical structure.

**Path Parameters**:
- `act_id` - Act ID

**Query Parameters**:
- `include_processed` (default: false) - Include already processed articles
  - `false`: Only returns articles with `ai_status='pending'`
  - `true`: Returns all articles regardless of status

**Example Request**:
```bash
GET /api/v1/ai-integration/acte/123/structure?include_processed=false
```

**Example Response**:
```json
{
  "id": 123,
  "tip_act": "LEGE",
  "nr_act": "95",
  "data_act": "2006-04-05",
  "an_act": 2006,
  "titlu_act": "Legea nr. 95/2006 privind reforma în domeniul sănătății",
  "emitent_act": "Parlament",
  "url_legislatie": "https://legislatie.just.ro/...",
  "ai_status": "pending",
  "ai_processed_at": null,
  "domenii": [
    {
      "id": 1,
      "cod": "FARMA",
      "denumire": "Farmacie",
      "culoare": "#4CAF50"
    }
  ],
  "articole": [
    {
      "id": 1001,
      "articol_nr": "1",
      "articol_label": "Art. 1",
      "titlu_nr": 1,
      "titlu_denumire": "DISPOZIȚII GENERALE",
      "capitol_nr": null,
      "capitol_denumire": null,
      "sectiune_nr": null,
      "sectiune_denumire": null,
      "subsectiune_nr": null,
      "subsectiune_denumire": null,
      "text_articol": "(1) Prezenta lege stabilește cadrul...",
      "ordine": 1,
      "ai_status": "pending",
      "ai_processed_at": null
    },
    {
      "id": 1002,
      "articol_nr": "2",
      "articol_label": "Art. 2",
      "titlu_nr": 1,
      "titlu_denumire": "DISPOZIȚII GENERALE",
      "capitol_nr": 1,
      "capitol_denumire": "Scopul și domeniul de aplicare",
      "sectiune_nr": null,
      "sectiune_denumire": null,
      "subsectiune_nr": null,
      "subsectiune_denumire": null,
      "text_articol": "În sensul prezentei legi, termenii...",
      "ordine": 2,
      "ai_status": "pending",
      "ai_processed_at": null
    }
  ],
  "total_articole": 450,
  "pending_articole": 450
}
```

**Response Structure**:
- **Act metadata**: Basic info (type, number, title, year)
- **Domains**: All domains assigned to this act
- **Articles array**: Complete list ordered by `ordine`
  - Each article includes:
    - `id`: Unique article identifier
    - `text_articol`: Full article text for AI analysis
    - **Hierarchy**: `titlu_nr`, `titlu_denumire`, `capitol_nr`, `capitol_denumire`, etc.
    - `ai_status`: Current processing status
    - `ordine`: Order in document
- **Statistics**: `total_articole`, `pending_articole`

---

### 3. Mark Article as Processing

**Endpoint**: `POST /api/v1/ai-integration/articole/{articol_id}/mark-processing`

**Purpose**: Mark article as currently being processed (prevents duplicate processing).

**Effect**: Sets `ai_status='processing'`

**Example Request**:
```bash
POST /api/v1/ai-integration/articole/1001/mark-processing
```

**Response**: `204 No Content`

---

### 4. Mark Article as Processed

**Endpoint**: `POST /api/v1/ai-integration/articole/{articol_id}/mark-processed`

**Purpose**: Mark article as successfully processed.

**Effect**: 
- Sets `ai_status='processed'`
- Records `ai_processed_at` timestamp

**Example Request**:
```bash
POST /api/v1/ai-integration/articole/1001/mark-processed
```

**Response**: `204 No Content`

---

### 5. Mark Article as Error

**Endpoint**: `POST /api/v1/ai-integration/articole/{articol_id}/mark-error`

**Purpose**: Mark article as failed during processing.

**Query Parameters**:
- `error_message` (required) - Error description

**Effect**: 
- Sets `ai_status='error'`
- Stores error message in `ai_error` field

**Example Request**:
```bash
POST /api/v1/ai-integration/articole/1001/mark-error?error_message=API+timeout
```

**Response**:
```json
{
  "message": "Article marked as error",
  "error": "API timeout"
}
```

---

## Issues Management Endpoints

### 6. Create New Issue

**Endpoint**: `POST /api/v1/issues`

**Purpose**: Create a new issue that can be linked to documents.

**Request Body**:
```json
{
  "denumire": "Lipsa specificații pentru eticheta exterioară",
  "descriere": "Articolul nu specifică informațiile obligatorii care trebuie să apară pe eticheta exterioară a medicamentului",
  "confidence_score": 0.89,
  "source": "ai",
  "extracted_text": "...text relevant extras...",
  "article_number": "5",
  "issue_monitoring_id": null
}
```

**Response**:
```json
{
  "id": 42,
  "denumire": "Lipsa specificații pentru eticheta exterioară",
  "issue_monitoring_id": null,
  "data_creare": "2025-01-15T10:30:45.123Z"
}
```

---

### 7. Link Issue to Article (Tier 1)

**Endpoint**: `POST /api/v1/issues/link`

**Purpose**: Link an issue directly to a document (article, act, or annex).

**Request Body**:
```json
{
  "document_type": "articol",
  "document_id": 1001,
  "issue_id": 42,
  "domeniu_id": 1,
  "relevance_score": 0.89
}
```

**Fields**:
- `document_type`: `"articol"`, `"act"`, or `"anexa"`
- `document_id`: ID of the document
- `issue_id`: Issue to link
- `domeniu_id`: **MANDATORY** - Domain context
- `relevance_score`: AI confidence (0.0 - 1.0)

**Response**:
```json
{
  "id": 500,
  "document_type": "articol",
  "document_id": 1001,
  "issue_id": 42,
  "domeniu_id": 1,
  "relevance_score": 0.89,
  "added_at": "2025-01-15T10:31:00.456Z"
}
```

---

### 8. Link Issue to Structure (Tier 2)

**Endpoint**: `POST /api/v1/issues/link-structure`

**Purpose**: Link an issue to a structural element (title, chapter, section).

**Use Case**: When an issue applies to an entire chapter, not just one article.

**Request Body**:
```json
{
  "act_id": 123,
  "structure_type": "capitol",
  "titlu_nr": 2,
  "titlu_denumire": "AUTORIZAREA MEDICAMENTELOR",
  "capitol_nr": 1,
  "capitol_denumire": "Autorizarea de punere pe piață",
  "sectiune_nr": null,
  "sectiune_denumire": null,
  "issue_id": 42,
  "domeniu_id": 1,
  "relevance_score": 0.85
}
```

**Fields**:
- `structure_type`: `"titlu"`, `"capitol"`, or `"sectiune"`
- Structure identifiers (must match exactly with articole table):
  - `titlu_nr`, `titlu_denumire`
  - `capitol_nr`, `capitol_denumire`
  - `sectiune_nr`, `sectiune_denumire`
- `issue_id`: Issue to link
- `domeniu_id`: **MANDATORY** - Domain context
- `relevance_score`: AI confidence

**Response**:
```json
{
  "id": 600,
  "act_id": 123,
  "structure_type": "capitol",
  "titlu_nr": 2,
  "titlu_denumire": "AUTORIZAREA MEDICAMENTELOR",
  "capitol_nr": 1,
  "capitol_denumire": "Autorizarea de punere pe piață",
  "issue_id": 42,
  "domeniu_id": 1,
  "relevance_score": 0.85,
  "added_at": "2025-01-15T10:32:00.789Z"
}
```

---

## Complete Processing Example (Python)

```python
import requests
from typing import List, Dict

API_BASE = "http://localhost:8000/api/v1"

def process_acts():
    """Main AI processing loop."""
    
    # Step 1: Get acts needing processing
    response = requests.get(
        f"{API_BASE}/ai-integration/acte/pending",
        params={
            "ai_status": "pending",
            "has_domenii": True,
            "limit": 5
        }
    )
    acts = response.json()
    
    print(f"Found {len(acts)} acts to process")
    
    for act in acts:
        print(f"\nProcessing Act {act['id']}: {act['titlu_act']}")
        process_single_act(act)


def process_single_act(act: Dict):
    """Process one act."""
    
    # Step 2: Get complete structure
    response = requests.get(
        f"{API_BASE}/ai-integration/acte/{act['id']}/structure",
        params={"include_processed": False}
    )
    act_structure = response.json()
    
    print(f"  Articles to process: {act_structure['pending_articole']}")
    
    for article in act_structure['articole']:
        if article['ai_status'] != 'pending':
            continue
            
        try:
            # Mark as processing
            requests.post(
                f"{API_BASE}/ai-integration/articole/{article['id']}/mark-processing"
            )
            
            # Step 3: Analyze with AI
            issues = analyze_article_with_ai(article['text_articol'])
            
            # Step 4 & 5: Create and link issues
            for issue_data in issues:
                # Create issue if needed
                if not issue_data.get('existing_id'):
                    issue_resp = requests.post(
                        f"{API_BASE}/issues",
                        json={
                            "denumire": issue_data['title'],
                            "descriere": issue_data['description'],
                            "confidence_score": issue_data['score'],
                            "source": "ai",
                            "article_number": article['articol_nr']
                        }
                    )
                    issue_id = issue_resp.json()['id']
                else:
                    issue_id = issue_data['existing_id']
                
                # Link to article (Tier 1)
                for domain in act_structure['domenii']:
                    requests.post(
                        f"{API_BASE}/issues/link",
                        json={
                            "document_type": "articol",
                            "document_id": article['id'],
                            "issue_id": issue_id,
                            "domeniu_id": domain['id'],
                            "relevance_score": issue_data['score']
                        }
                    )
            
            # Step 6: Link structure issues (if applicable)
            if should_create_structure_issue(article, issues):
                structure_issue = aggregate_structure_issues(article, issues)
                requests.post(
                    f"{API_BASE}/issues/link-structure",
                    json={
                        "act_id": act_structure['id'],
                        "structure_type": "capitol",
                        "titlu_nr": article['titlu_nr'],
                        "titlu_denumire": article['titlu_denumire'],
                        "capitol_nr": article['capitol_nr'],
                        "capitol_denumire": article['capitol_denumire'],
                        "issue_id": structure_issue['id'],
                        "domeniu_id": act_structure['domenii'][0]['id'],
                        "relevance_score": structure_issue['score']
                    }
                )
            
            # Step 7: Mark as processed
            requests.post(
                f"{API_BASE}/ai-integration/articole/{article['id']}/mark-processed"
            )
            
            print(f"    ✓ Article {article['articol_nr']} processed")
            
        except Exception as e:
            # Mark as error
            requests.post(
                f"{API_BASE}/ai-integration/articole/{article['id']}/mark-error",
                params={"error_message": str(e)}
            )
            print(f"    ✗ Article {article['articol_nr']} failed: {e}")


def analyze_article_with_ai(text: str) -> List[Dict]:
    """
    Placeholder for actual AI analysis.
    Replace with your AI model.
    """
    # Your AI logic here
    # Return list of identified issues
    return [
        {
            "title": "Lipsa specificații",
            "description": "...",
            "score": 0.89,
            "existing_id": None  # or existing issue ID
        }
    ]


def should_create_structure_issue(article: Dict, issues: List) -> bool:
    """Determine if issues should be grouped at structure level."""
    # Logic to decide if this is a chapter-wide issue
    return False


def aggregate_structure_issues(article: Dict, issues: List) -> Dict:
    """Aggregate multiple article issues into structure issue."""
    return {"id": 42, "score": 0.85}


if __name__ == "__main__":
    process_acts()
```

---

## Domain Context Rules

### Mandatory Domain Assignment

**All issues MUST have domain context** (`domeniu_id` NOT NULL).

### Domain Inheritance

Articles inherit domains from their parent act, unless overridden:

1. **Act-level domains**: Assigned when user submits act URL
   ```sql
   INSERT INTO acte_domenii (act_id, domeniu_id, relevanta)
   VALUES (123, 1, 100);  -- FARMA domain
   ```

2. **Article-level override** (optional):
   ```sql
   INSERT INTO articole_domenii (articol_id, domeniu_id, relevanta)
   VALUES (1001, 5, 90);  -- Override with SANATATE domain
   ```

3. **Effective domains** for article:
   ```sql
   SELECT * FROM get_articol_domenii(1001);
   -- Returns domains with source='act' or source='articol'
   ```

### AI Service Usage

When linking issues, AI service should:

1. Use domains from `act_structure['domenii']` array
2. Link issue to **EACH relevant domain** separately
3. Adjust `relevance_score` based on domain applicability

Example:
```python
# Act has 2 domains: FARMA and SANATATE
for domain in act_structure['domenii']:
    score = calculate_domain_relevance(issue, domain)  # AI logic
    if score > 0.5:  # Threshold
        link_issue(article_id, issue_id, domain['id'], score)
```

---

## Error Handling

### Status Transitions

```
pending → processing → processed ✓
                     ↘ error ✗
                     
error → needs_reprocessing → processing → ...
```

### Retry Logic

AI service should implement:

1. **Exponential backoff** for API errors
2. **Batch processing** with checkpoints
3. **Error threshold**: After N failures, mark as `error` and skip
4. **Reprocessing queue**: Periodically retry `error` status articles

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 404 | Act/Article not found | Skip and log |
| 400 | Invalid domeniu_id | Verify domain exists |
| 409 | Duplicate link | Already processed, skip |
| 500 | Database error | Retry with backoff |

---

## Performance Considerations

### Batch Processing

Process acts in batches:
- Use `limit` parameter
- Process overnight/off-hours
- Monitor `pending_articole` count

### Rate Limiting

Implement client-side rate limiting:
- Max 10 acts processed simultaneously
- 100 requests/minute to API
- Use async/await for parallel article processing

### Monitoring

Track metrics:
- Acts processed per hour
- Average processing time per article
- Error rate by error type
- Domain coverage (% articles with issues)

---

## Testing

### Test with Sample Act

```bash
# 1. Get test act
curl http://localhost:8000/api/v1/ai-integration/acte/pending?limit=1

# 2. Get structure
curl http://localhost:8000/api/v1/ai-integration/acte/123/structure

# 3. Create test issue
curl -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{
    "denumire": "Test Issue",
    "confidence_score": 0.95,
    "source": "ai"
  }'

# 4. Link to article
curl -X POST http://localhost:8000/api/v1/issues/link \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "articol",
    "document_id": 1001,
    "issue_id": 42,
    "domeniu_id": 1,
    "relevance_score": 0.95
  }'

# 5. Mark processed
curl -X POST http://localhost:8000/api/v1/ai-integration/articole/1001/mark-processed
```

---

## Questions?

Contact: [Your Contact Info]

API Docs: http://localhost:8000/docs

OpenAPI Spec: http://localhost:8000/openapi.json
