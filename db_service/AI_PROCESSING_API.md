# AI Processing API - Documentație Completă

## Prezentare Generală

API-ul de AI Processing este destinat serviciilor externe de analiză AI și automatizărilor interne pentru procesarea articolelor din acte legislative.

**Base URL (Production):** `https://legislatie.issuemonitoring.ro/api/v1`

**Autentificare:** Majoritatea endpoint-urilor necesită API Key în header:
```
X-API-Key: your-api-key-here
```

---

## 📋 Categorii de Endpoint-uri

1. **Document Retrieval** - Obținerea actelor și articolelor pentru procesare
2. **Status Management** - Actualizarea statusului de procesare
3. **Processing Control** - Declanșarea și monitorizarea procesării
4. **Query & Monitoring** - Interogarea statusului și statisticilor

---

## 1️⃣ Document Retrieval

### GET `/ai/acte/pending`

**Scop:** Obține lista actelor care necesită procesare AI.

**Query Parameters:**
- `ai_status` (string, default: `"pending"`) - Filtrează după status: `pending`, `processing`, `processed`, `error`
- `has_domenii` (boolean, optional) - Filtrează acte care au/nu au domenii asignate
- `limit` (integer, 1-100, default: 10) - Număr maxim de rezultate

**Response:** Lista de `ActListItemForAI`
```json
[
  {
    "id": 1,
    "tip_act": "LEGE",
    "nr_act": "123",
    "an_act": 2024,
    "titlu_act": "Titlu act legislativ",
    "ai_status": "pending",
    "total_articole": 50,
    "pending_articole": 45,
    "domenii": [
      {
        "id": 1,
        "cod": "MEDIU",
        "denumire": "Mediu",
        "culoare": "#28a745"
      }
    ]
  }
]
```

**Use Case:**
```python
# Descoperă actele care necesită procesare
response = requests.get(
    "https://legislatie.issuemonitoring.ro/api/v1/ai/acte/pending",
    headers={"X-API-Key": API_KEY},
    params={"ai_status": "pending", "limit": 10}
)
acts = response.json()
```

---

### GET `/ai/acte/{act_id}`

**Scop:** Obține structura completă a unui act cu toate articolele pentru procesare. **Acesta este endpoint-ul principal pentru AI.**

**Path Parameters:**
- `act_id` (integer) - ID-ul actului legislativ

**Query Parameters:**
- `include_processed` (boolean, default: `false`) - Dacă `true`, include și articolele deja procesate

**Response:** Obiect `ActForAI`
```json
{
  "id": 1,
  "tip_act": "LEGE",
  "nr_act": "123",
  "an_act": 2024,
  "data_act": "2024-01-15",
  "titlu_act": "Titlu act legislativ",
  "emitent_act": "Parlament",
  "url_legislatie": "https://legislatie.just.ro/...",
  "ai_status": "pending",
  "ai_processed_at": null,
  "domenii": [
    {
      "id": 1,
      "cod": "MEDIU",
      "denumire": "Mediu",
      "culoare": "#28a745"
    }
  ],
  "articole": [
    {
      "id": 100,
      "articol_nr": "1",
      "articol_label": "Art. 1",
      "titlu_nr": "I",
      "titlu_denumire": "Dispoziții generale",
      "capitol_nr": null,
      "capitol_denumire": null,
      "sectiune_nr": null,
      "sectiune_denumire": null,
      "text_articol": "Textul complet al articolului...",
      "ordine": 1,
      "ai_status": "pending",
      "ai_processed_at": null
    }
  ],
  "total_articole": 50,
  "pending_articole": 45
}
```

**Use Case:**
```python
# Workflow complet de procesare
act = requests.get(
    f"https://legislatie.issuemonitoring.ro/api/v1/ai/acte/{act_id}",
    headers={"X-API-Key": API_KEY}
).json()

for article in act["articole"]:
    if article["ai_status"] == "pending":
        # 1. Marchează articolul ca fiind în procesare
        requests.post(
            f"https://legislatie.issuemonitoring.ro/api/v1/ai/articole/{article['id']}/mark-processing",
            headers={"X-API-Key": API_KEY}
        )
        
        # 2. Analizează textul cu AI
        issues = ai_analyze(article["text_articol"])
        
        # 3. Link-uiește issues descoperite
        for issue in issues:
            requests.post(
                "https://legislatie.issuemonitoring.ro/api/v1/issues/link",
                headers={"X-API-Key": API_KEY},
                json={
                    "articol_id": article["id"],
                    "domeniu_id": act["domenii"][0]["id"],
                    "issue_text": issue
                }
            )
        
        # 4. Marchează articolul ca procesat
        requests.post(
            f"https://legislatie.issuemonitoring.ro/api/v1/ai/articole/{article['id']}/mark-processed",
            headers={"X-API-Key": API_KEY}
        )
```

---

## 2️⃣ Status Management

### 🆕 POST `/ai/articles/update-status` **(RECOMMENDED)**

**Scop:** Endpoint unificat pentru actualizarea statusului AI al unui articol. **Acest endpoint înlocuiește cele 3 endpoint-uri deprecate.**

**Request Body:**
```json
{
  "article_id": 1234,
  "status": 2,
  "explanation": "Optional explanation for the status change"
}
```

**Supported Status Values:**
- `0` = **pending** - Resetează articolul la stare neprocesată
- `1` = **processing** - Articolul este în curs de analiză
- `2` = **completed** - Procesat cu succes
- `3` = **error** - Procesare eșuată
- `9` = **skipped** - Articol omis intenționat

**Response:** `200 OK`
```json
{
  "success": true,
  "article_id": 1234,
  "previous_status": 1,
  "new_status": 2,
  "updated_at": "2025-11-26T12:34:56.789Z"
}
```

**Examples:**

```python
import requests

API_BASE = "https://legislatie.issuemonitoring.ro/api/v1"
API_KEY = "your-api-key"

# 1. Mark as processing (before starting AI analysis)
response = requests.post(
    f"{API_BASE}/ai/articles/update-status",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={"article_id": 1234, "status": 1}
)

# 2. Mark as completed (after successful processing)
response = requests.post(
    f"{API_BASE}/ai/articles/update-status",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={"article_id": 1234, "status": 2}
)

# 3. Mark as error with explanation
response = requests.post(
    f"{API_BASE}/ai/articles/update-status",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={
        "article_id": 1234,
        "status": 3,
        "explanation": "API timeout after 30 seconds"
    }
)

# 4. Reset to pending
response = requests.post(
    f"{API_BASE}/ai/articles/update-status",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={"article_id": 1234, "status": 0}
)

# 5. Mark as skipped (optional)
response = requests.post(
    f"{API_BASE}/ai/articles/update-status",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={
        "article_id": 1234,
        "status": 9,
        "explanation": "Article too short for meaningful analysis"
    }
)
```

---

### ⚠️ DEPRECATED ENDPOINTS

**The following endpoints are deprecated and will be removed in a future version. Please migrate to `/ai/articles/update-status`.**

<details>
<summary>POST `/ai/articole/{articol_id}/mark-processing` (DEPRECATED)</summary>

**Scop:** Marchează un articol ca fiind în curs de procesare pentru a preveni procesarea duplicată.

**Migration:** Use `POST /ai/articles/update-status` with `{"article_id": ID, "status": 1}`

**Path Parameters:**
- `articol_id` (integer) - ID-ul articolului

**Response:** `204 No Content` (succes)

**Use Case:**
```python
# OLD (deprecated)
response = requests.post(
    f"https://legislatie.issuemonitoring.ro/api/v1/ai/articole/{article_id}/mark-processing",
    headers={"X-API-Key": API_KEY}
)

# NEW (recommended)
response = requests.post(
    f"https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={"article_id": article_id, "status": 1}
)
```

</details>

<details>
<summary>POST `/ai/articole/{articol_id}/mark-processed` (DEPRECATED)</summary>

**Scop:** Marchează un articol ca fiind procesat cu succes și înregistrează timestamp-ul.

**Migration:** Use `POST /ai/articles/update-status` with `{"article_id": ID, "status": 2}`

**Path Parameters:**
- `articol_id` (integer) - ID-ul articolului

**Response:** `204 No Content` (succes)

**Use Case:**
```python
# OLD (deprecated)
response = requests.post(
    f"https://legislatie.issuemonitoring.ro/api/v1/ai/articole/{article_id}/mark-processed",
    headers={"X-API-Key": API_KEY}
)

# NEW (recommended)
response = requests.post(
    f"https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={"article_id": article_id, "status": 2}
)
```

</details>

<details>
<summary>POST `/ai/articole/{articol_id}/mark-error` (DEPRECATED)</summary>

**Scop:** Marchează un articol ca având eroare în procesare și salvează mesajul de eroare.

**Migration:** Use `POST /ai/articles/update-status` with `{"article_id": ID, "status": 3, "explanation": "error message"}`

**Path Parameters:**
- `articol_id` (integer) - ID-ul articolului

**Query Parameters:**
- `error_message` (string, required) - Descrierea erorii

**Response:** `200 OK`

**Use Case:**
```python
# OLD (deprecated)
try:
    issues = ai_analyze(article_text)
except Exception as e:
    requests.post(
        f"https://legislatie.issuemonitoring.ro/api/v1/ai/articole/{article_id}/mark-error",
        headers={"X-API-Key": API_KEY},
        params={"error_message": str(e)}
    )

# NEW (recommended)
try:
    issues = ai_analyze(article_text)
except Exception as e:
    requests.post(
        f"https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status",
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json={"article_id": article_id, "status": 3, "explanation": str(e)}
    )
```

</details>

---

### POST `/ai/reset/{article_id}`

**Scop:** Resetează statusul unui articol la `pending` fără a-l reprocessa imediat.

**Path Parameters:**
- `article_id` (integer) - ID-ul articolului

**Response:** `204 No Content` (succes)

**Use Case:**
```python
# Folosește pentru a pune articolul înapoi în coadă
response = requests.post(
    f"https://legislatie.issuemonitoring.ro/api/v1/ai/reset/{article_id}",
    headers={"X-API-Key": API_KEY}
)
```

---

## 3️⃣ Processing Control

### POST `/ai/process`

**Scop:** Declanșează procesarea AI în background pentru articole pending.

**Request Body:**
```json
{
  "limit": 10,
  "batch_delay": 1.0
}
```

**Fields:**
- `limit` (integer, 1-100, default: 10) - Număr maxim de articole de procesat
- `batch_delay` (float, 0.1-10.0, default: 1.0) - Delay între batch-uri (secunde)

**Response:** `202 Accepted`
```json
{
  "message": "AI processing started for up to 10 articles",
  "job_id": null,
  "processing_in_background": true
}
```

**Use Case:**
```python
# Declanșează procesare asincronă
response = requests.post(
    "https://legislatie.issuemonitoring.ro/api/v1/ai/process",
    headers={"X-API-Key": API_KEY},
    json={"limit": 50, "batch_delay": 2.0}
)
# Returnează imediat, procesarea rulează în background
```

---

### GET `/ai/process/sync`

**Scop:** Declanșează procesarea AI sincron (blochează până la finalizare).

⚠️ **Atenție:** Endpoint-ul blochează până când procesarea se termină. Folosește `/ai/process` pentru procesare asincronă.

**Query Parameters:**
- `limit` (integer, default: 10) - Număr maxim de articole
- `batch_delay` (float, default: 1.0) - Delay între batch-uri

**Response:** `200 OK`
```json
{
  "success": 8,
  "error": 2,
  "skipped": 0,
  "total": 10
}
```

**Use Case:**
```python
# Folosește doar pentru teste sau batch-uri mici
response = requests.get(
    "https://legislatie.issuemonitoring.ro/api/v1/ai/process/sync",
    headers={"X-API-Key": API_KEY},
    params={"limit": 5}
)
stats = response.json()
print(f"Processed: {stats['success']}, Failed: {stats['error']}")
```

---

## 4️⃣ Query & Monitoring

### GET `/ai/status`

**Scop:** Obține statistici despre statusul curent al procesării AI.

**Response:** `200 OK`
```json
{
  "pending_count": 150,
  "processing_count": 5,
  "completed_count": 1234,
  "error_count": 12,
  "total_count": 1401
}
```

**Use Case:**
```python
# Monitorizează progresul procesării
status = requests.get(
    "https://legislatie.issuemonitoring.ro/api/v1/ai/status",
    headers={"X-API-Key": API_KEY}
).json()

print(f"Progress: {status['completed_count']}/{status['total_count']}")
print(f"Pending: {status['pending_count']}")
print(f"Errors: {status['error_count']}")
```

---

### GET `/ai/pending`

**Scop:** Lista articolelor care așteaptă procesare AI.

**Query Parameters:**
- `limit` (integer, default: 50) - Număr maxim de rezultate

**Response:** `200 OK`
```json
[
  {
    "id": 1628,
    "numar_articol": "9",
    "ai_status": "pending",
    "ai_processed_at": null,
    "ai_error": null,
    "has_metadata": false,
    "issues_count": 0
  }
]
```

**Use Case:**
```python
# Obține lista articolelor pending
pending = requests.get(
    "https://legislatie.issuemonitoring.ro/api/v1/ai/pending",
    headers={"X-API-Key": API_KEY},
    params={"limit": 100}
).json()

print(f"Found {len(pending)} pending articles")
```

---

### GET `/ai/errors`

**Scop:** Lista articolelor care au eșuat la procesare.

**Query Parameters:**
- `limit` (integer, default: 50) - Număr maxim de rezultate

**Response:** `200 OK`
```json
[
  {
    "id": 333,
    "numar_articol": "15",
    "ai_status": "error",
    "ai_processed_at": "2024-11-24T10:30:00",
    "ai_error": "OpenAI API timeout",
    "has_metadata": false,
    "issues_count": 0
  }
]
```

**Use Case:**
```python
# Verifică articolele care au eșuat
errors = requests.get(
    "https://legislatie.issuemonitoring.ro/api/v1/ai/errors",
    headers={"X-API-Key": API_KEY}
).json()

for article in errors:
    print(f"Article {article['id']}: {article['ai_error']}")
```

---

### POST `/ai/retry/{article_id}`

**Scop:** Reîncearcă procesarea AI pentru un articol specific (procesează IMEDIAT).

⚠️ **Notă:** Acest endpoint procesează imediat articolul, nu doar resetează statusul. Folosește `/ai/reset/{article_id}` pentru a reseta fără procesare.

**Path Parameters:**
- `article_id` (integer) - ID-ul articolului

**Response:** `200 OK` (sau `500` dacă AIService nu este configurat corect)
```json
{
  "id": 333,
  "numar_articol": "15",
  "ai_status": "completed",
  "ai_processed_at": "2024-11-25T12:45:00",
  "ai_error": null,
  "has_metadata": true,
  "issues_count": 3
}
```

**Use Case:**
```python
# Reprocessează un articol care a eșuat
response = requests.post(
    f"https://legislatie.issuemonitoring.ro/api/v1/ai/retry/{article_id}",
    headers={"X-API-Key": API_KEY}
)
result = response.json()
```

---

## 📊 AI Status Values

Articolele au status de tip **INTEGER** în baza de date, dar API-ul returnează **STRING**:

| Integer | String | Descriere |
|---------|--------|-----------|
| 0 | `"pending"` | Așteaptă procesare |
| 1 | `"processing"` | În curs de procesare |
| 2 | `"completed"` | Procesat cu succes |
| 3 | `"error"` | Eroare la procesare |

Actele legislative folosesc direct **STRING** în baza de date.

---

## 🔄 Workflow Recomandat

### Procesare Batch Standard

```python
import requests

API_BASE = "https://legislatie.issuemonitoring.ro/api/v1"
API_KEY = "your-api-key"

def process_pending_acts():
    # 1. Obține acte pending
    acts = requests.get(
        f"{API_BASE}/ai/acte/pending",
        headers={"X-API-Key": API_KEY},
        params={"ai_status": "pending", "limit": 10}
    ).json()
    
    for act in acts:
        # 2. Obține structura completă
        full_act = requests.get(
            f"{API_BASE}/ai/acte/{act['id']}",
            headers={"X-API-Key": API_KEY}
        ).json()
        
        # 3. Procesează fiecare articol
        for article in full_act["articole"]:
            if article["ai_status"] != "pending":
                continue
                
            try:
                # 3a. Marchează ca în procesare (NEW API)
                requests.post(
                    f"{API_BASE}/ai/articles/update-status",
                    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                    json={"article_id": article["id"], "status": 1}
                )
                
                # 3b. Analizează cu AI
                issues = analyze_with_ai(article["text_articol"])
                
                # 3c. Salvează issues
                for issue in issues:
                    requests.post(
                        f"{API_BASE}/issues/link",
                        headers={"X-API-Key": API_KEY},
                        json={
                            "articol_id": article["id"],
                            "domeniu_id": full_act["domenii"][0]["id"],
                            "issue_text": issue
                        }
                    )
                
                # 3d. Marchează ca procesat (NEW API)
                requests.post(
                    f"{API_BASE}/ai/articles/update-status",
                    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                    json={"article_id": article["id"], "status": 2}
                )
                
            except Exception as e:
                # 3e. Marchează eroarea (NEW API)
                requests.post(
                    f"{API_BASE}/ai/articles/update-status",
                    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                    json={
                        "article_id": article["id"],
                        "status": 3,
                        "explanation": str(e)
                    }
                )

def analyze_with_ai(text):
    # Implementează logica ta de analiză AI
    pass
```

---

## 🧪 Testing Endpoints

### Verificare Rapidă

```bash
# 1. Verifică status general
curl -H "X-API-Key: YOUR_KEY" \
  https://legislatie.issuemonitoring.ro/api/v1/ai/status

# 2. Lista acte pending
curl -H "X-API-Key: YOUR_KEY" \
  "https://legislatie.issuemonitoring.ro/api/v1/ai/acte/pending?limit=5"

# 3. Obține act complet
curl -H "X-API-Key: YOUR_KEY" \
  https://legislatie.issuemonitoring.ro/api/v1/ai/acte/1

# 4. Lista articole pending
curl -H "X-API-Key: YOUR_KEY" \
  "https://legislatie.issuemonitoring.ro/api/v1/ai/pending?limit=10"

# 5. Actualizează status articol (NEW API)
curl -X POST \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"article_id": 1234, "status": 2}' \
  https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status
curl -X POST -H "X-API-Key: YOUR_KEY" \
  https://legislatie.issuemonitoring.ro/api/v1/ai/articole/1628/mark-processing

# 6. Marchează articol ca procesat
curl -X POST -H "X-API-Key: YOUR_KEY" \
  https://legislatie.issuemonitoring.ro/api/v1/ai/articole/1628/mark-processed

# 7. Marchează eroare
curl -X POST -H "X-API-Key: YOUR_KEY" \
  "https://legislatie.issuemonitoring.ro/api/v1/ai/articole/1628/mark-error?error_message=Test+error"

# 8. Reset status
curl -X POST -H "X-API-Key: YOUR_KEY" \
  https://legislatie.issuemonitoring.ro/api/v1/ai/reset/1628
```

---

## 🔄 Migration Guide

### Migrating from Old API to New Unified API

**Timeline:**
- **Phase 1 (Current):** Both old and new APIs are available
- **Phase 2 (2 weeks):** Deprecation warnings added to old endpoints
- **Phase 3 (1 month):** Old endpoints removed

**Quick Migration:**

| Old Endpoint | New Unified Endpoint |
|-------------|---------------------|
| `POST /articole/{id}/mark-processing` | `POST /articles/update-status` with `status: 1` |
| `POST /articole/{id}/mark-processed` | `POST /articles/update-status` with `status: 2` |
| `POST /articole/{id}/mark-error` | `POST /articles/update-status` with `status: 3` + `explanation` |

**Code Migration Examples:**

```python
# ❌ OLD WAY (deprecated)
def mark_processing_old(article_id):
    requests.post(
        f"{API_BASE}/ai/articole/{article_id}/mark-processing",
        headers={"X-API-Key": API_KEY}
    )

# ✅ NEW WAY (recommended)
def mark_processing_new(article_id):
    requests.post(
        f"{API_BASE}/ai/articles/update-status",
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json={"article_id": article_id, "status": 1}
    )
```

```python
# ❌ OLD WAY (deprecated)
def mark_error_old(article_id, error_msg):
    requests.post(
        f"{API_BASE}/ai/articole/{article_id}/mark-error",
        headers={"X-API-Key": API_KEY},
        params={"error_message": error_msg}
    )

# ✅ NEW WAY (recommended)
def mark_error_new(article_id, error_msg):
    requests.post(
        f"{API_BASE}/ai/articles/update-status",
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json={
            "article_id": article_id,
            "status": 3,
            "explanation": error_msg
        }
    )
```

**Benefits of New API:**
- Single endpoint for all status updates
- More flexible (can reset to pending, skip articles, etc.)
- Better error handling and response data
- Consistent JSON request/response format
- Optional explanations for all statuses (not just errors)

---

## ⚠️ Note Importante

1. **Autentificare:** Majoritatea endpoint-urilor necesită API Key în header `X-API-Key`

2. **Rate Limiting:** Folosește `batch_delay` pentru a evita supraîncărcarea sistemului

3. **Status Management:** ÎNTOTDEAUNA marchează articolul ca `processing` înainte de analiză pentru a preveni procesarea duplicată

4. **Error Handling:** Marchează articolele care eșuează cu mesaj de eroare detaliat pentru debugging

5. **Retry vs Reset:**
   - `POST /ai/retry/{id}` - Procesează IMEDIAT articolul
   - `POST /ai/reset/{id}` - Doar resetează statusul la pending

6. **Sync vs Async:**
   - `POST /ai/process` - Asincron, returnează imediat (recomandat)
   - `GET /ai/process/sync` - Sincron, blochează (doar pentru teste)

7. **Migration to New API:** Use `/articles/update-status` instead of individual mark-* endpoints
   - ❌ `/ai/articles/pending` - NU există
   - ✅ `/ai/pending` - Folosește acesta în schimb

---

## 📞 Support

Pentru probleme sau întrebări despre API, contactează echipa de dezvoltare sau creează un issue în repository.

**Ultima actualizare:** 25 Noiembrie 2024
