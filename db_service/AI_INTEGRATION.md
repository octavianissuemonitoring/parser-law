# AI Service Integration Guide

## Overview

API-ul oferă endpoint-uri dedicate pentru serviciul AI să raporteze statusul procesării articolelor.

## Status Codes

| Code | Nume | Descriere |
|------|------|-----------|
| 0 | NOT_PROCESSED | Articol neprocesate, asteaptă procesare AI |
| 1 | PROCESSING | Articol în curs de procesare de către AI |
| 2 | PROCESSED | Procesare finalizată cu succes |
| 9 | ERROR | Eroare în timpul procesării |

## API Endpoints

### 1. Get Pending Articles

**GET** `/api/v1/ai/articles/pending`

Obține articole care așteaptă procesare (ai_status=0).

**Query Parameters:**
- `limit` (int, default=100): Max articole de returnat (1-1000)
- `act_id` (int, optional): Filtrează după ID-ul actului

**Response:** `List[ArticolResponse]`

**Example:**
```bash
curl "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/pending?limit=50"
```

---

### 2. Get Articles by Status

**GET** `/api/v1/ai/articles/by-status/{status}`

Obține articole după status AI.

**Path Parameters:**
- `status` (int): 0, 1, 2, sau 9

**Query Parameters:**
- `limit` (int, default=100)
- `offset` (int, default=0)

**Example:**
```bash
# Get articles with errors
curl "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/by-status/9"
```

---

### 3. Mark Articles as Processing

**POST** `/api/v1/ai/articles/mark-processing`

Marchează articole ca fiind în procesare (ai_status=1).

**Request Body:**
```json
[1, 2, 3, 4, 5]  // Array of article IDs
```

**Response:**
```json
{
  "success": true,
  "updated_count": 5,
  "failed_ids": [],
  "message": "Marked 5 articles as processing"
}
```

**Example:**
```bash
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/mark-processing" \
  -H "Content-Type: application/json" \
  -d '[1,2,3,4,5]'
```

---

### 4. Update AI Status (Main Endpoint)

**POST** `/api/v1/ai/articles/update-status`

Actualizează statusul AI pentru mai multe articole.

**Request Body:**
```json
{
  "article_ids": [1, 2, 3],
  "ai_status": 2,
  "metadate": "Articolele vorbesc despre...",
  "ai_status_message": "Processing completed successfully"
}
```

**Fields:**
- `article_ids` (required): List of article IDs
- `ai_status` (required): 0, 1, 2, sau 9
- `metadate` (optional): AI-generated summary (when status=2)
- `ai_status_message` (optional): Message explaining status (error details, processing notes, etc)

**Examples:**

**Mark as processed:**
```bash
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status" \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [1, 2, 3],
    "ai_status": 2,
    "metadate": "Rezumat AI: Articolele reglementează..."
  }'
```

**Mark as error:**
```bash
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status" \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [4],
    "ai_status": 9,
    "ai_status_message": "Timeout after 30s"
  }'
```

**Mark as processing with note:**
```bash
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status" \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [5, 6],
    "ai_status": 1,
    "ai_status_message": "Batch #42 - Started at 14:30"
  }'
```

---

### 5. Update Single Article

**POST** `/api/v1/ai/articles/{article_id}/status`

Actualizează statusul pentru un singur articol.

**Path Parameters:**
- `article_id` (int): Article ID

**Query Parameters:**
- `ai_status` (int, required): 0, 1, 2, sau 9
- `ai_status_message` (str, optional): Message explaining status
- `metadate` (str, optional): AI-generated summary

**Example:**
```bash
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/123/status?ai_status=2&metadate=Summary...&ai_status_message=Processed%20successfully" \
  -H "Content-Type: application/json"
```

---

### 6. Get Processing Stats

**GET** `/api/v1/ai/stats`

Obține statistici despre procesarea AI.

**Response:**
```json
{
  "not_processed": 150,
  "processing": 5,
  "processed": 45,
  "error": 1,
  "total": 201
}
```

**Example:**
```bash
curl "https://legislatie.issuemonitoring.ro/api/v1/ai/stats"
```

---

## Typical Workflow

### Step 1: Fetch Pending Articles
```python
import requests

response = requests.get(
    "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/pending",
    params={"limit": 10}
)
articles = response.json()
article_ids = [a["id"] for a in articles]
```

### Step 2: Mark as Processing
```python
requests.post(
    "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/mark-processing",
    json=article_ids
)
```

### Step 3: Process with AI
```python
# Your AI processing logic here
results = process_with_ai(articles)
```

### Step 4: Update Status
```python
# Success case
requests.post(
    "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status",
    json={
        "article_ids": successful_ids,
        "ai_status": 2,  # PROCESSED
        "metadate": "AI generated summary...",
        "ai_status_message": "Processed with GPT-4, confidence: 0.95"
    }
)

# Error case
requests.post(
    "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status",
    json={
        "article_ids": failed_ids,
        "ai_status": 9,  # ERROR
        "ai_status_message": "Rate limit exceeded - will retry in 60s"
    }
)
```

---

## Error Handling

- Status 400: Invalid request (e.g., missing required field)
- Status 404: Article not found
- Status 500: Server error

---

## Database Schema

### Table: `legislatie.articole`

New columns added:
- `ai_status` (INTEGER, default=0): Status code (0, 1, 2, 9)
- `ai_processed_at` (TIMESTAMP): When processing completed
- `ai_status_message` (TEXT): **Optional message for any status** (error details, processing notes, completion info)
- `metadate` (TEXT): AI-generated summary/metadata

**Use cases for `ai_status_message`:**
- Status 0: "Queued in batch #42"
- Status 1: "Processing started at 14:30 UTC"
- Status 2: "Processed successfully with GPT-4, confidence: 0.95"
- Status 9: "Timeout after 30s - will retry"

---

## Authentication

Currently, endpoints are public. Consider adding API key authentication:

```bash
curl -H "X-API-Key: your-secret-key" \
  "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/pending"
```

---

## Monitoring

Check processing stats periodically:

```bash
watch -n 10 'curl -s https://legislatie.issuemonitoring.ro/api/v1/ai/stats | jq'
```

This will show live updates every 10 seconds.
