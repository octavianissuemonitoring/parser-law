# 📚 Documentație API - Legislație Monitoring

**Base URL:** `http://legislatie.issuemonitoring.ro/api/v1`

**Documentație Interactivă:**
- Swagger UI: http://legislatie.issuemonitoring.ro/docs
- ReDoc: http://legislatie.issuemonitoring.ro/redoc

---

## 📋 Cuprins
- [Linkuri Legislație](#-linkuri-legislație)
- [Acte Legislative](#-acte-legislative)
- [Articole](#-articole)
- [Export](#-export)
- [Procesare AI](#-procesare-ai)

---

## 🔗 Linkuri Legislație

### GET /links/
Obține lista de linkuri către acte legislative.

**Query Parameters:**
- `limit` (int, default: 100) - Numărul maxim de rezultate
- `offset` (int, default: 0) - Offset pentru paginare

**Response:**
```json
{
  "total": 10,
  "items": [
    {
      "id": 1,
      "url": "https://legislatie.just.ro/...",
      "status": "completed",
      "acte_count": 3,
      "error_message": null,
      "created_at": "2025-11-10T20:00:00",
      "updated_at": "2025-11-10T20:05:00"
    }
  ]
}
```

**Status-uri posibile:**
- `pending_scraping` - În așteptare
- `processing` - În procesare
- `completed` - Completat cu succes
- `failed` - Eșuat (vezi `error_message`)

---

### POST /links/
Adaugă un link nou pentru procesare.

**Request Body:**
```json
{
  "url": "https://legislatie.just.ro/Public/FormaPrintabila/..."
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "url": "https://legislatie.just.ro/...",
  "status": "pending_scraping",
  "acte_count": 0,
  "error_message": null,
  "created_at": "2025-11-10T20:00:00",
  "updated_at": "2025-11-10T20:00:00"
}
```

---

### POST /links/process
Procesează un link (scraping + import).

**Query Parameters:**
- `url` (string, required) - URL-ul către actul legislativ

**Response:** `202 Accepted`
```json
{
  "message": "Processing started for link ID 1",
  "link_id": 1,
  "status": "processing"
}
```

**Notă:** Procesarea se face în background. Verifică status-ul cu GET /links/

---

### DELETE /links/{link_id}
Șterge un link (și toate actele asociate).

**Path Parameters:**
- `link_id` (int) - ID-ul linkului

**Response:** `200 OK`
```json
{
  "message": "Link and associated acts deleted successfully",
  "deleted_acts": 3
}
```

---

## 📜 Acte Legislative

### GET /acte
Obține lista de acte legislative.

**Query Parameters:**
- `limit` (int, default: 50) - Numărul maxim de rezultate
- `offset` (int, default: 0) - Offset pentru paginare
- `tip_act` (string, optional) - Filtrare după tip (LEGE, ORDONANTA, etc.)
- `search` (string, optional) - Căutare în titlu/număr/an

**Response:**
```json
{
  "total": 100,
  "items": [
    {
      "id": 1,
      "tip_act": "LEGE",
      "nr_act": "123",
      "an_act": 2012,
      "titlu_act": "energiei electrice și a gazelor naturale",
      "data_publicare": "2012-07-10",
      "url_sursa": "https://legislatie.just.ro/...",
      "created_at": "2025-11-10T20:00:00",
      "updated_at": "2025-11-10T20:00:00"
    }
  ]
}
```

---

### GET /acte/{act_id}
Obține detalii despre un act legislativ.

**Path Parameters:**
- `act_id` (int) - ID-ul actului

**Response:**
```json
{
  "id": 1,
  "tip_act": "LEGE",
  "nr_act": "123",
  "an_act": 2012,
  "titlu_act": "energiei electrice și a gazelor naturale",
  "data_publicare": "2012-07-10",
  "emitent": "PARLAMENTUL ROMÂNIEI",
  "nr_articole": 285,
  "url_sursa": "https://legislatie.just.ro/...",
  "status_procesare": "completed",
  "created_at": "2025-11-10T20:00:00",
  "updated_at": "2025-11-10T20:00:00"
}
```

---

### GET /acte/{act_id}/changes
Obține istoricul modificărilor pentru un act.

**Path Parameters:**
- `act_id` (int) - ID-ul actului

**Response:**
```json
{
  "total": 5,
  "items": [
    {
      "id": 1,
      "act_id": 1,
      "version_number": 2,
      "change_date": "2024-01-15",
      "change_description": "Modificat prin LEGE 45/2024",
      "diff_summary": "3 articole modificate, 2 adăugate",
      "created_at": "2024-01-15T10:00:00"
    }
  ]
}
```

---

### DELETE /acte/{act_id}
Șterge un act legislativ (și toate articolele asociate).

**Path Parameters:**
- `act_id` (int) - ID-ul actului

**Response:** `200 OK`
```json
{
  "message": "Act legislativ deleted successfully",
  "deleted_articles": 285
}
```

---

### POST /acte/import
Importă acte legislative din fișiere CSV.

**Query Parameters:**
- `rezultate_dir` (string, default: "/app/rezultate") - Director cu CSV-uri

**Response:**
```json
{
  "success": true,
  "total_files": 3,
  "imported_acts": 3,
  "updated_acts": 0,
  "imported_articles": 450,
  "skipped_acts": 0,
  "errors": []
}
```

**Notă:** Acest endpoint este folosit intern de procesul de scraping.

---

## 📝 Articole

### GET /articole
Obține lista de articole.

**Query Parameters:**
- `limit` (int, default: 50) - Numărul maxim de rezultate
- `offset` (int, default: 0) - Offset pentru paginare
- `act_id` (int, optional) - Filtrare după actul legislativ
- `search` (string, optional) - Căutare în conținut

**Response:**
```json
{
  "total": 285,
  "items": [
    {
      "id": 1,
      "act_id": 1,
      "tip_articol": "Articol",
      "numar_articol": "1",
      "continut": "Prezenta lege reglementează...",
      "indent_level": 0,
      "created_at": "2025-11-10T20:00:00"
    }
  ]
}
```

---

### GET /articole/{articol_id}
Obține detalii despre un articol.

**Path Parameters:**
- `articol_id` (int) - ID-ul articolului

**Response:**
```json
{
  "id": 1,
  "act_id": 1,
  "tip_articol": "Articol",
  "numar_articol": "1",
  "continut": "Prezenta lege reglementează...",
  "indent_level": 0,
  "ai_summary": "Acest articol stabilește...",
  "ai_analysis_date": "2025-11-10T20:00:00",
  "created_at": "2025-11-10T20:00:00",
  "updated_at": "2025-11-10T20:00:00"
}
```

---

### GET /articole/{articol_id}/changes
Obține istoricul modificărilor pentru un articol.

**Path Parameters:**
- `articol_id` (int) - ID-ul articolului

**Response:**
```json
{
  "total": 2,
  "items": [
    {
      "id": 1,
      "articol_id": 1,
      "version_number": 2,
      "change_date": "2024-01-15",
      "old_content": "Text vechi...",
      "new_content": "Text nou...",
      "change_type": "modified",
      "created_at": "2024-01-15T10:00:00"
    }
  ]
}
```

---

## 📤 Export

### POST /export/acts
Exportă acte legislative în format JSON/CSV/Excel.

**Request Body:**
```json
{
  "format": "json",
  "act_ids": [1, 2, 3],
  "include_articles": true,
  "include_history": false
}
```

**Query Parameters:**
- `format` (string) - Format export: `json`, `csv`, `excel`

**Response:** Fișier descărcat cu datele exportate

---

## 🤖 Procesare AI

### POST /ai/analyze-article
Analizează un articol cu AI (sumarizare, extragere entități).

**Request Body:**
```json
{
  "articol_id": 1,
  "analysis_type": "summary"
}
```

**Analysis Types:**
- `summary` - Sumarizare text
- `entities` - Extragere entități (persoane, organizații, date)
- `keywords` - Extragere cuvinte cheie
- `sentiment` - Analiză sentiment

**Response:**
```json
{
  "articol_id": 1,
  "analysis_type": "summary",
  "result": {
    "summary": "Acest articol stabilește...",
    "confidence": 0.95
  },
  "processing_time": 1.23
}
```

---

## 🔍 Statistici și Metrici

### GET /stats
Obține statistici generale despre sistem.

**Response:**
```json
{
  "total_acts": 150,
  "total_articles": 12500,
  "total_links": 200,
  "pending_links": 10,
  "processing_links": 3,
  "completed_links": 180,
  "failed_links": 7,
  "acts_by_type": {
    "LEGE": 80,
    "ORDONANTA": 40,
    "HOTARARE": 30
  },
  "last_import": "2025-11-10T20:00:00"
}
```

---

## 🔐 Autentificare

**Notă:** Momentan API-ul nu necesită autentificare. Pentru producție, se recomandă:
- API Keys
- OAuth2 / JWT tokens
- Rate limiting

---

## 📊 Coduri de Status HTTP

- `200 OK` - Cerere procesată cu succes
- `201 Created` - Resursă creată cu succes
- `202 Accepted` - Cerere acceptată, procesare în background
- `400 Bad Request` - Date invalide în cerere
- `404 Not Found` - Resursa nu există
- `405 Method Not Allowed` - Metodă HTTP nepermisă
- `422 Unprocessable Entity` - Eroare de validare date
- `500 Internal Server Error` - Eroare server

---

## 📝 Exemple de Utilizare

### Exemplu 1: Adăugare și Procesare Link

```bash
# 1. Adaugă link
curl -X POST "http://legislatie.issuemonitoring.ro/api/v1/links/" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://legislatie.just.ro/Public/FormaPrintabila/00000G1656LBGXZIRQU152DYXZD7MLAE"}'

# Răspuns: {"id": 1, "status": "pending_scraping", ...}

# 2. Procesează link
curl -X POST "http://legislatie.issuemonitoring.ro/api/v1/links/process?url=https%3A%2F%2Flegislatie.just.ro%2FPublic%2FFormaPrintabila%2F00000G1656LBGXZIRQU152DYXZD7MLAE"

# 3. Verifică status
curl "http://legislatie.issuemonitoring.ro/api/v1/links/"
```

### Exemplu 2: Căutare Acte

```bash
# Caută toate legile din 2012
curl "http://legislatie.issuemonitoring.ro/api/v1/acte?tip_act=LEGE&search=2012"

# Obține detalii act specific
curl "http://legislatie.issuemonitoring.ro/api/v1/acte/1"

# Obține articolele unui act
curl "http://legislatie.issuemonitoring.ro/api/v1/articole?act_id=1&limit=500"
```

### Exemplu 3: PowerShell

```powershell
# Adaugă link
$body = @{ url = "https://legislatie.just.ro/Public/FormaPrintabila/..." } | ConvertTo-Json
Invoke-RestMethod -Uri "http://legislatie.issuemonitoring.ro/api/v1/links/" `
  -Method Post -Body $body -ContentType "application/json"

# Obține toate actele
$acte = Invoke-RestMethod -Uri "http://legislatie.issuemonitoring.ro/api/v1/acte?limit=100"
$acte.items | Format-Table id, tip_act, nr_act, an_act, titlu_act
```

### Exemplu 4: Python

```python
import requests

# Adaugă link
response = requests.post(
    "http://legislatie.issuemonitoring.ro/api/v1/links/",
    json={"url": "https://legislatie.just.ro/Public/FormaPrintabila/..."}
)
link = response.json()
print(f"Link ID: {link['id']}, Status: {link['status']}")

# Procesează link
requests.post(
    f"http://legislatie.issuemonitoring.ro/api/v1/links/process",
    params={"url": link['url']}
)

# Obține acte
acte = requests.get(
    "http://legislatie.issuemonitoring.ro/api/v1/acte",
    params={"limit": 50}
).json()

for act in acte['items']:
    print(f"{act['tip_act']} {act['nr_act']}/{act['an_act']}: {act['titlu_act']}")
```

---

## 🐛 Debugging și Troubleshooting

### Verificare Status API
```bash
curl http://legislatie.issuemonitoring.ro/health
```

### Verificare Log-uri
```bash
ssh root@77.237.235.158
docker logs legislatie_api --tail 100 -f
```

### Verificare Bază de Date
```bash
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform
```

---

## 📞 Suport

Pentru probleme sau întrebări:
- **Email:** support@issuemonitoring.ro
- **GitHub Issues:** https://github.com/octavianissuemonitoring/parser-law/issues

---

**Versiune:** 1.0.0  
**Data ultimei actualizări:** 10 Noiembrie 2025
