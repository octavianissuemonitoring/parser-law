# AI Service Integration Guide

## Overview

API-ul oferă 6 endpoint-uri dedicate pentru serviciul AI să gestioneze procesarea articolelor legislative.

**Base URL:** `https://legislatie.issuemonitoring.ro/api/v1/ai`

## Status Codes

| Code | Nume | Descriere | Când se setează |
|------|------|-----------|-----------------|
| 0 | NOT_PROCESSED | Articole neprocesate, așteaptă procesare AI | Default pentru articole noi |
| 1 | PROCESSING | Articol în curs de procesare de către AI | Când AI service preia articolul |
| 2 | PROCESSED | Procesare finalizată cu succes | După procesare reușită + salvare metadate |
| 9 | ERROR | Eroare în timpul procesării | Când procesarea eșuează |

**Tranzițiile normale:** 0 → 1 → 2 (sau 9 în caz de eroare)

## Workflow complet pentru AI Service

```
┌─────────────┐
│   STEP 1    │  Fetch pending articles (status=0)
│   FETCH     │  GET /api/v1/ai/articles/pending
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   STEP 2    │  Mark as processing (status=1)
│    MARK     │  POST /api/v1/ai/articles/mark-processing
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   STEP 3    │  Process with AI (external, not API)
│   PROCESS   │  Your AI logic here
└──────┬──────┘
       │
       ├─────────────┐
       │             │
       ▼             ▼
┌─────────────┐ ┌─────────────┐
│  SUCCESS    │ │   ERROR     │
│ status=2    │ │  status=9   │
│  + metadate │ │  + message  │
└─────────────┘ └─────────────┘
       │             │
       └──────┬──────┘
              │
              ▼
       POST /api/v1/ai/articles/update-status
       
       
┌─────────────┐
│   STEP 4    │  Monitor progress
│   MONITOR   │  GET /api/v1/ai/stats
└─────────────┘
```

---

## API Endpoints

### 1. Get Pending Articles ⭐ (START HERE)

**GET** `/api/v1/ai/articles/pending`

Obține articole care așteaptă procesare (ai_status=0). **Acesta este primul endpoint pe care AI service îl apelează.**

**Query Parameters:**
- `limit` (int, default=100): Max articole de returnat (1-1000)
- `act_id` (int, optional): Filtrează după ID-ul actului

**Response:** `List[ArticolResponse]`

Fiecare articol conține:
- `id`: ID-ul articolului (folosit în apeluri ulterioare)
- `text_articol`: Textul complet pentru procesare AI
- `act_id`: ID-ul actului legislativ părinte
- `ai_status`: Va fi 0 (NOT_PROCESSED)
- `articol_nr`, `articol_label`: Identificare

**Example:**
```bash
curl "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/pending?limit=50"
```

**Response Example:**
```json
[
  {
    "id": 330,
    "act_id": 5,
    "articol_nr": "2",
    "articol_label": "Articolul 2",
    "text_articol": "(1)...Conducerea ANRMPSG este asigurată...",
    "ai_status": 0,
    "ai_processed_at": null,
    "ai_status_message": null,
    "metadate": null,
    "ordine": 3
  }
]
```

---

### 2. Get Articles by Status

**GET** `/api/v1/ai/articles/by-status/{status}`

Obține articole după status AI. Util pentru debug sau reprocessare.

**Path Parameters:**
- `status` (int): 0, 1, 2, sau 9

**Query Parameters:**
- `limit` (int, default=100)
- `offset` (int, default=0): Pentru paginare

**Example:**
```bash
# Get articles with errors
curl "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/by-status/9"

# Get processing articles
curl "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/by-status/1?limit=10&offset=0"
```

**Use cases:**
- Status 9: Găsește articole cu erori pentru retry
- Status 1: Verifică articole blocate în procesare
- Status 2: Audit articole procesate cu succes

---

### 3. Mark Articles as Processing ⭐ (STEP 2)

**POST** `/api/v1/ai/articles/mark-processing`

Marchează articole ca fiind în procesare (ai_status=1). **Apelează imediat după fetch, înainte de procesare.**

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

**Important:** 
- Previne procesarea dublă când rulezi multiple instanțe AI
- Marchează articolele ca "claimed" de AI service
- Dacă un articol rămâne cu status=1 prea mult timp → blocat (verifică cu endpoint #2)

---

### 4. Update AI Status ⭐ (MAIN ENDPOINT - STEP 3)

**POST** `/api/v1/ai/articles/update-status`

Actualizează statusul AI pentru mai multe articole. **Acesta este endpoint-ul principal pentru raportarea rezultatelor.**

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
- `ai_status` (required): 2 (success) sau 9 (error)
- `metadate` (optional): AI-generated summary - **DOAR pentru status=2**
- `ai_status_message` (optional): Context message pentru orice status

**Important:**
- Pentru `ai_status=2` sau `9`, câmpul `ai_processed_at` se setează automat la timestamp-ul curent
- `metadate` ar trebui să conțină rezumatul AI (doar la succes)
- `ai_status_message` poate fi folosit pentru orice status (vezi exemple mai jos)

**Examples:**

**✅ Mark as processed (SUCCESS):**
```bash
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status" \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [330, 331],
    "ai_status": 2,
    "metadate": "Articolele reglementează aspecte administrative și de conducere pentru ANRMPSG",
    "ai_status_message": "Processed successfully with GPT-4, confidence: 0.95"
  }'
```

**Response:**
```json
{
  "success": true,
  "updated_count": 2,
  "failed_ids": [],
  "message": "Updated 2 articles to status 'processed'"
}
```

**❌ Mark as error:**
```bash
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status" \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [4],
    "ai_status": 9,
    "ai_status_message": "Timeout after 30s - will retry in 60s"
  }'
```

**🔄 Mark as processing with note:**
```bash
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status" \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [5, 6],
    "ai_status": 1,
    "ai_status_message": "Batch #42 - Started at 14:30 UTC"
  }'
```

---

### 5. Update Single Article (Alternative)

**POST** `/api/v1/ai/articles/{article_id}/status`

Actualizează statusul pentru un singur articol. Alternativă mai simplă la endpoint #4 pentru cazuri speciale.

**Path Parameters:**
- `article_id` (int): Article ID

**Query Parameters:**
- `ai_status` (int, required): 0, 1, 2, sau 9
- `ai_status_message` (str, optional): Message explaining status
- `metadate` (str, optional): AI-generated summary

**Response:** ArticolResponse complet

**Example:**
```bash
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/332/status?ai_status=2&metadate=Recovered%20successfully&ai_status_message=Retry%20successful" \
  -H "Content-Type: application/json"
```

**Use cases:**
- Retry individual pentru articole cu erori
- Update status pentru debugging
- Testing individual

---

### 6. Get Processing Stats ⭐ (MONITORING)

**GET** `/api/v1/ai/stats`

Obține statistici despre procesarea AI. **Folosește pentru monitoring în timp real.**

**Response:**
```json
{
  "not_processed": 431,
  "processing": 0,
  "processed": 5,
  "error": 0,
  "total": 436
}
```

**Fields:**
- `not_processed`: Articole cu ai_status=0 (așteaptă procesare)
- `processing`: Articole cu ai_status=1 (în procesare acum)
- `processed`: Articole cu ai_status=2 (finalizate cu succes)
- `error`: Articole cu ai_status=9 (erori)
- `total`: Total articole în database

**Example:**
```bash
curl "https://legislatie.issuemonitoring.ro/api/v1/ai/stats"
```

**Monitoring în timp real:**
```bash
# Linux/Mac - refresh every 5 seconds
watch -n 5 'curl -s https://legislatie.issuemonitoring.ro/api/v1/ai/stats | jq'

# Windows PowerShell
while($true) { 
  curl -s "https://legislatie.issuemonitoring.ro/api/v1/ai/stats" | python -m json.tool
  Start-Sleep -Seconds 5
}
```

---

## Typical Workflow - Python Example

### Complete End-to-End Implementation

```python
import requests
from typing import List, Dict

API_BASE = "https://legislatie.issuemonitoring.ro/api/v1"

def process_articles():
    """Complete workflow pentru procesare AI."""
    
    # STEP 1: Fetch pending articles
    print("🔍 Step 1: Fetching pending articles...")
    response = requests.get(
        f"{API_BASE}/ai/articles/pending",
        params={"limit": 10}
    )
    articles = response.json()
    article_ids = [a["id"] for a in articles]
    
    if not article_ids:
        print("✅ No articles to process!")
        return
    
    print(f"📥 Found {len(article_ids)} articles: {article_ids}")
    
    # STEP 2: Mark as processing
    print("🔄 Step 2: Marking articles as processing...")
    response = requests.post(
        f"{API_BASE}/ai/articles/mark-processing",
        json=article_ids
    )
    result = response.json()
    print(f"✓ Marked {result['updated_count']} articles")
    
    # STEP 3: Process with AI
    print("🤖 Step 3: Processing with AI...")
    successful_ids = []
    failed_ids = []
    
    for article in articles:
        try:
            # Your AI processing logic here
            ai_summary = process_with_ai(article["text_articol"])
            
            # Update to success
            requests.post(
                f"{API_BASE}/ai/articles/update-status",
                json={
                    "article_ids": [article["id"]],
                    "ai_status": 2,  # PROCESSED
                    "metadate": ai_summary,
                    "ai_status_message": f"Processed with GPT-4, tokens: {len(article['text_articol'])}"
                }
            )
            successful_ids.append(article["id"])
            print(f"  ✓ Article {article['id']} processed successfully")
            
        except Exception as e:
            # Update to error
            requests.post(
                f"{API_BASE}/ai/articles/update-status",
                json={
                    "article_ids": [article["id"]],
                    "ai_status": 9,  # ERROR
                    "ai_status_message": f"Error: {str(e)}"
                }
            )
            failed_ids.append(article["id"])
            print(f"  ✗ Article {article['id']} failed: {e}")
    
    # STEP 4: Report results
    print(f"\n📊 Processing complete:")
    print(f"   ✅ Success: {len(successful_ids)}")
    print(f"   ❌ Failed: {len(failed_ids)}")
    
    # Get updated stats
    stats = requests.get(f"{API_BASE}/ai/stats").json()
    print(f"\n📈 Current stats:")
    print(f"   Pending: {stats['not_processed']}")
    print(f"   Processing: {stats['processing']}")
    print(f"   Completed: {stats['processed']}")
    print(f"   Errors: {stats['error']}")


def process_with_ai(text: str) -> str:
    """
    Your AI processing logic here.
    
    Args:
        text: Article text to process
        
    Returns:
        AI-generated summary
    """
    # Example: Call OpenAI, Claude, or your AI model
    # return openai_client.generate_summary(text)
    return f"AI Summary of article with {len(text)} characters"


if __name__ == "__main__":
    process_articles()
```

### Batch Processing with Error Recovery

```python
def batch_process_with_retry(batch_size=50, max_retries=3):
    """Process articles in batches with automatic retry."""
    
    while True:
        # Fetch pending
        response = requests.get(
            f"{API_BASE}/ai/articles/pending",
            params={"limit": batch_size}
        )
        articles = response.json()
        
        if not articles:
            print("✅ All articles processed!")
            break
        
        article_ids = [a["id"] for a in articles]
        
        # Mark as processing
        requests.post(
            f"{API_BASE}/ai/articles/mark-processing",
            json=article_ids
        )
        
        # Process batch
        for article in articles:
            retry_count = 0
            while retry_count < max_retries:
                try:
                    summary = process_with_ai(article["text_articol"])
                    
                    # Success
                    requests.post(
                        f"{API_BASE}/ai/articles/update-status",
                        json={
                            "article_ids": [article["id"]],
                            "ai_status": 2,
                            "metadate": summary,
                            "ai_status_message": f"Processed on retry {retry_count + 1}"
                        }
                    )
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        # Final failure
                        requests.post(
                            f"{API_BASE}/ai/articles/update-status",
                            json={
                                "article_ids": [article["id"]],
                                "ai_status": 9,
                                "ai_status_message": f"Failed after {max_retries} retries: {str(e)}"
                            }
                        )
                    else:
                        print(f"Retry {retry_count}/{max_retries} for article {article['id']}")
                        time.sleep(2 ** retry_count)  # Exponential backoff
```

---

## Testing & Verification

### Quick Test Sequence

```bash
# 1. Check current stats
curl "https://legislatie.issuemonitoring.ro/api/v1/ai/stats"

# 2. Fetch 3 pending articles
curl "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/pending?limit=3" | python -m json.tool

# 3. Mark them as processing (use actual IDs from step 2)
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/mark-processing" \
  -H "Content-Type: application/json" \
  -d '[330,331,332]'

# 4. Verify they're in processing state
curl "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/by-status/1"

# 5. Mark as success
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status" \
  -H "Content-Type: application/json" \
  -d '{
    "article_ids": [330, 331],
    "ai_status": 2,
    "metadate": "Test AI summary",
    "ai_status_message": "Test successful"
  }'

# 6. Verify article details
curl "https://legislatie.issuemonitoring.ro/api/v1/articole/330" | python -m json.tool

# 7. Check final stats
curl "https://legislatie.issuemonitoring.ro/api/v1/ai/stats"
```

### Expected Results

After running the test sequence:
- `not_processed`: Should decrease by 2
- `processing`: Should be 1 (article 332 still processing)
- `processed`: Should increase by 2
- Articles 330, 331 should have:
  - `ai_status`: 2
  - `ai_processed_at`: Recent timestamp
  - `metadate`: "Test AI summary"
  - `ai_status_message`: "Test successful"

---

## Error Handling

### HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid input (e.g., missing required field, invalid status code)
- **404 Not Found**: Article ID not found
- **422 Unprocessable Entity**: Validation error (check response details)
- **500 Internal Server Error**: Server error (check logs)

### Common Errors

**1. Invalid Status Code**
```json
{
  "detail": "Invalid status. Must be 0, 1, 2, or 9"
}
```
→ Solution: Use only valid status codes

**2. Missing Required Field**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "article_ids"],
      "msg": "Field required"
    }
  ]
}
```
→ Solution: Ensure all required fields are present

**3. Article Not Found**
```json
{
  "detail": "Article 999 not found"
}
```
→ Solution: Verify article ID exists

### Best Practices

1. **Always check response status code**
   ```python
   response = requests.post(...)
   if response.status_code != 200:
       print(f"Error: {response.json()}")
   ```

2. **Handle network errors**
   ```python
   try:
       response = requests.post(..., timeout=30)
   except requests.exceptions.Timeout:
       # Retry or mark as error
       pass
   ```

3. **Batch size recommendations**
   - Mark processing: Max 1000 articles per request
   - Update status: Max 100-500 articles per request
   - Fetch pending: 10-100 articles per batch

4. **Rate limiting** (if implemented in future)
   - Respect `Retry-After` headers
   - Implement exponential backoff

---

## Database Schema

### Table: `legislatie.articole`

**AI Processing Columns:**

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `ai_status` | INTEGER | 0 | Status code: 0=not_processed, 1=processing, 2=processed, 9=error |
| `ai_processed_at` | TIMESTAMP | NULL | Timestamp when processing completed (auto-set for status 2 or 9) |
| `ai_status_message` | TEXT | NULL | Optional message for any status (context, errors, notes) |
| `metadate` | TEXT | NULL | AI-generated summary/metadata (only for status=2) |

**Index:**
- `idx_articole_ai_status` on `ai_status` - Fast filtering by status

**Use cases for `ai_status_message`:**

| Status | Example Message |
|--------|----------------|
| 0 | "Queued in batch #42" |
| 1 | "Processing started at 14:30 UTC with GPT-4" |
| 2 | "Processed successfully, confidence: 0.95, tokens: 1234" |
| 9 | "Timeout after 30s - will retry", "Rate limit exceeded", "Invalid response from AI" |

**Sample Query:**
```sql
-- Get all articles needing processing
SELECT id, articol_nr, text_articol 
FROM legislatie.articole 
WHERE ai_status = 0 
LIMIT 100;

-- Get processing stats
SELECT 
  ai_status,
  COUNT(*) as count,
  MAX(ai_processed_at) as last_processed
FROM legislatie.articole
GROUP BY ai_status;

-- Find stuck articles (processing for >1 hour)
SELECT id, articol_nr, created_at
FROM legislatie.articole
WHERE ai_status = 1 
  AND created_at < NOW() - INTERVAL '1 hour';
```

---

## Authentication & Security

### Current Status
**⚠️ Endpoints are currently PUBLIC** - No authentication required.

### Recommended for Production

**Option 1: API Key Authentication**
```bash
curl -H "X-API-Key: your-secret-key" \
  "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/pending"
```

**Option 2: Bearer Token (JWT)**
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/pending"
```

**Option 3: IP Whitelisting**
- Restrict access to known AI service IPs
- Configure in nginx or application level

### Security Best Practices

1. **Use HTTPS only** - Already implemented ✅
2. **Add authentication** - TODO for production
3. **Rate limiting** - Prevent abuse
4. **Logging** - Track all API calls
5. **Monitoring** - Alert on suspicious activity

---

## Monitoring & Observability

### Metrics to Track

1. **Processing Rate**
   - Articles processed per hour
   - Average processing time per article
   
2. **Success Rate**
   - Ratio of status=2 vs status=9
   - Error types distribution
   
3. **Queue Depth**
   - Number of articles with status=0
   - Trend over time
   
4. **Stuck Articles**
   - Articles with status=1 for >1 hour
   - Possible dead workers

### Monitoring Dashboard (Example)

```python
import requests
import time
from datetime import datetime

def monitor_stats():
    """Simple monitoring dashboard."""
    while True:
        stats = requests.get(
            "https://legislatie.issuemonitoring.ro/api/v1/ai/stats"
        ).json()
        
        total_completed = stats['processed'] + stats['error']
        success_rate = (stats['processed'] / total_completed * 100) if total_completed > 0 else 0
        
        print(f"\n{'='*50}")
        print(f"📊 AI Processing Dashboard - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*50}")
        print(f"⏳ Pending:     {stats['not_processed']:>5} ({stats['not_processed']/stats['total']*100:.1f}%)")
        print(f"🔄 Processing:  {stats['processing']:>5}")
        print(f"✅ Completed:   {stats['processed']:>5}")
        print(f"❌ Errors:      {stats['error']:>5}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"{'='*50}")
        
        # Alert if too many stuck in processing
        if stats['processing'] > 50:
            print("⚠️  WARNING: Many articles stuck in processing!")
        
        time.sleep(10)

if __name__ == "__main__":
    monitor_stats()
```

### Alerts Setup

**Check for stuck articles:**
```bash
# Run this as a cron job every hour
curl -s "https://legislatie.issuemonitoring.ro/api/v1/ai/articles/by-status/1" | \
  python -c "import sys, json; data = json.load(sys.stdin); print(f'ALERT: {len(data)} stuck articles') if len(data) > 10 else None"
```

**Track error rate:**
```bash
# Alert if error rate > 5%
curl -s "https://legislatie.issuemonitoring.ro/api/v1/ai/stats" | \
  python -c "import sys, json; s = json.load(sys.stdin); print(f'ALERT: Error rate {s['error']/(s['processed']+s['error'])*100:.1f}%') if s['error']/(s['processed']+s['error']) > 0.05 else None"
```
