# 🤖 AI Processing & Export Strategy

## Arhitectură Completă

```
┌────────────────────────────────────────────────────────────┐
│                      PARSER-LAW                            │
│                 (Orchestrator Complet)                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │   SCRAPING   │ → │ AI PROCESSING│ → │   EXPORT   │  │
│  └──────────────┘    └──────────────┘    └────────────┘  │
│         ↓                   ↓                    ↓        │
│  Legislație brută    Issues+Metadate    Către Issue     │
│                                           Monitoring      │
└────────────────────────────────────────────────────────────┘
```

## 🔄 Workflow Complet

### **Faza 1: Scraping & Detectare Noutăți**
```python
# scraper_legislatie.py
1. Scraping legislatie.gov.ro
2. Parsare HTML → Acte + Articole + Anexe
3. Detectare noutăți:
   - Acte complet noi
   - Articole noi în acte existente
   - Modificări articole existente
4. Stocare în BD cu status:
   - ai_status = 'pending'
   - export_status = 'pending'
```

### **Faza 2: Procesare AI**
```python
# Nou serviciu: ai_processor.py
1. SELECT * FROM v_pending_ai_processing LIMIT 10
2. Pentru fiecare element (act/articol/anexă):
   
   a) Trimitere la AI (OpenAI/Claude):
      - Prompt: "Extrage issues din acest text legislativ"
      - Prompt: "Generează sumarizare/metadate"
   
   b) Primire răspuns AI:
      - issues: [{"denumire": "...", "descriere": "...", "confidence": 0.95}]
      - metadate: "Sumarizare text..."
   
   c) Stocare în BD:
      - INSERT INTO issues (denumire, descriere, source='ai', confidence_score)
      - INSERT INTO articole_issues (articol_id, issue_id, adaugat_de='ai')
      - UPDATE articole SET metadate='...', ai_status='completed'
   
   d) Logging & Error Handling:
      - Dacă AI fail → ai_status='error', ai_error='...'
```

### **Faza 3: Export către Issue Monitoring**
```python
# Nou serviciu: export_service.py
1. SELECT * FROM v_pending_export LIMIT 5
2. Pentru fiecare act complet:
   
   a) Construire pachet complet:
      {
        "act": {...},
        "articole": [
          {
            "id": 1,
            "text": "...",
            "metadate": "...",
            "issues": [{"denumire": "...", "descriere": "..."}]
          }
        ],
        "anexe": [...],
        "act_issues": [...]
      }
   
   b) POST https://issue-monitoring.ro/api/import/legislation
      Headers: {"Authorization": "Bearer TOKEN"}
      Body: JSON complet
   
   c) Primire răspuns:
      {
        "success": true,
        "act_id": 12345,  # ID în BD Issue Monitoring
        "articole_ids": [67, 68, 69],
        "issues_ids": [101, 102]
      }
   
   d) Update local:
      - UPDATE acte_legislative SET 
          export_status='exported',
          issue_monitoring_id=12345,
          export_at=NOW()
      - UPDATE articole SET issue_monitoring_id=... WHERE id IN (...)
      - UPDATE issues SET issue_monitoring_id=... WHERE id IN (...)
```

---

## 📊 Schema Bază de Date

### **Tabele Principale**
```sql
-- Acte cu tracking AI & Export
acte_legislative:
  - ai_status: pending → processing → completed/error
  - ai_processed_at, ai_error
  - metadate: TEXT (sumarizare generată de AI)
  - export_status: pending → exported/error
  - export_at, export_error
  - issue_monitoring_id: INTEGER (ID în BD Issue Monitoring)

-- Articole cu tracking AI
articole:
  - ai_status, ai_processed_at, ai_error
  - metadate: TEXT (explicație generată de AI)
  - issue_monitoring_id: INTEGER

-- Issues extrase de AI
issues:
  - denumire, descriere
  - source: 'ai' | 'manual'
  - confidence_score: DECIMAL(3,2)  # 0.95 = 95% confidence
  - issue_monitoring_id: INTEGER

-- Anexe cu tracking AI
anexe:
  - continut, metadate
  - ai_status, ai_processed_at, ai_error
  - issue_monitoring_id: INTEGER

-- Relații many-to-many
articole_issues, acte_issues, anexe_issues:
  - adaugat_de: 'ai' | 'manual'
```

### **Views pentru Monitorizare**
```sql
-- Elemente care așteaptă AI
v_pending_ai_processing:
  - tip (act/articol/anexă)
  - identificator
  - ai_status, ai_error

-- Acte gata de export
v_pending_export:
  - act_id, tip_act, numar
  - nr_articole, nr_anexe, nr_issues
  - ai_status='completed', export_status='pending'

-- Pachet complet pentru export
v_export_package:
  - act complet
  - articole cu metadate și issues (JSON)
  - anexe cu metadate și issues (JSON)
  - issues la nivel de act (JSON)
```

---

## 🚀 Implementare Pas cu Pas

### **Pasul 1: Migrare BD** ✅
```bash
# Rulează pe producție
psql -h localhost -U legislatie_user -d legislatie_db \
  -f db_service/migrations/add_ai_processing.sql
```

### **Pasul 2: Serviciu AI Processing**
```python
# db_service/app/services/ai_service.py
class AIService:
    async def process_pending_items(self, limit=10):
        """Procesează elemente pending cu AI"""
        
    async def extract_issues(self, text: str) -> List[Issue]:
        """Extrage issues din text cu OpenAI/Claude"""
        
    async def generate_metadata(self, text: str) -> str:
        """Generează sumarizare/metadate"""
```

### **Pasul 3: Serviciu Export**
```python
# db_service/app/services/export_service.py
class ExportService:
    async def export_to_issue_monitoring(self, act_id: int):
        """Exportă act complet către Issue Monitoring"""
        
    async def build_export_package(self, act_id: int) -> dict:
        """Construiește pachet JSON complet"""
```

### **Pasul 4: Endpoint-uri Noi**
```python
# db_service/app/api/routes/ai_processing.py
POST /api/v1/ai/process          # Trigger procesare AI
GET  /api/v1/ai/status           # Status procesare
POST /api/v1/ai/retry/{id}       # Retry element cu eroare

# db_service/app/api/routes/export.py
POST /api/v1/export/to-im        # Export către Issue Monitoring
GET  /api/v1/export/pending      # Liste acte gata de export
GET  /api/v1/export/status       # Status export
```

### **Pasul 5: Scheduler**
```python
# scheduler.py - adaugă task-uri noi
@scheduler.scheduled_job('interval', minutes=30)
def process_ai_pending():
    """Procesează automat elemente pending cu AI"""
    
@scheduler.scheduled_job('interval', hours=1)
def export_to_issue_monitoring():
    """Exportă automat acte procesate către Issue Monitoring"""
```

---

## 🔧 Configurare

### **Environment Variables**
```bash
# .env
# AI Configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AI_PROVIDER=openai  # sau 'anthropic'
AI_MODEL=gpt-4o  # sau 'claude-3-5-sonnet-20241022'
AI_MAX_RETRIES=3
AI_TIMEOUT=60

# Issue Monitoring Integration
ISSUE_MONITORING_API_URL=https://issue-monitoring.ro/api
ISSUE_MONITORING_API_KEY=secret_token_here
EXPORT_BATCH_SIZE=5
```

---

## 📈 Monitorizare & Logging

### **Metrics**
```python
# Tracked în scheduler
- ai_processing_rate: elemente/oră
- ai_success_rate: %
- ai_error_rate: %
- export_rate: acte/zi
- export_success_rate: %
```

### **Logging**
```python
# Log structure
{
  "timestamp": "2025-11-08T10:30:00",
  "service": "ai_processor",
  "action": "extract_issues",
  "articol_id": 12345,
  "status": "success",
  "issues_found": 3,
  "confidence_avg": 0.92,
  "processing_time_ms": 1234
}
```

---

## 🎯 Issue Monitoring Integration

### **API Contract**

#### **Endpoint Issue Monitoring:**
```
POST https://issue-monitoring.ro/api/import/legislation
Authorization: Bearer {API_KEY}
Content-Type: application/json

Request Body:
{
  "act": {
    "tip_act": "Legea",
    "numar": "123",
    "data_an": 2025,
    "denumire": "...",
    "metadate": "Sumarizare act..."
  },
  "articole": [
    {
      "articol_nr": "Art. 1",
      "ordine": 1,
      "text_articol": "...",
      "metadate": "Explicație art. 1...",
      "issues": [
        {
          "denumire": "Taxare electronică",
          "descriere": "...",
          "confidence_score": 0.95
        }
      ]
    }
  ],
  "anexe": [...],
  "act_issues": [...]
}

Response:
{
  "success": true,
  "act_id": 12345,
  "articole_mapping": [
    {"parser_law_id": 1, "issue_monitoring_id": 67},
    {"parser_law_id": 2, "issue_monitoring_id": 68}
  ],
  "issues_mapping": [
    {"parser_law_id": 10, "issue_monitoring_id": 101}
  ]
}
```

### **Sincronizare Bidirectională**
```python
# Issue Monitoring poate returna modificări manuale
GET https://issue-monitoring.ro/api/sync/changes?since={timestamp}

Response:
{
  "articole_updates": [
    {
      "issue_monitoring_id": 67,
      "metadate": "Modificare manuală...",
      "issues": [...]
    }
  ]
}

# Parser-Law aplică modificările
UPDATE articole 
SET metadate = 'Modificare manuală...'
WHERE issue_monitoring_id = 67
```

---

## ✅ Checklist Implementare

- [ ] Rulează migrare BD (`add_ai_processing.sql`)
- [ ] Adaugă dependențe: `openai`, `anthropic` în `requirements.txt`
- [ ] Implementează `AIService` cu extractie issues + metadate
- [ ] Implementează `ExportService` cu construire pachet JSON
- [ ] Adaugă endpoint-uri `/api/v1/ai/*` și `/api/v1/export/*`
- [ ] Configurează variabile environment (API keys)
- [ ] Adaugă task-uri în `scheduler.py`
- [ ] Testează pe date mock
- [ ] Deploy pe producție
- [ ] Monitorizare & logging

---

## 📝 Note Tehnice

### **Rate Limiting AI**
```python
# Protecție împotriva cost overflow
MAX_TOKENS_PER_REQUEST = 4000
MAX_REQUESTS_PER_MINUTE = 50
COST_THRESHOLD_DAILY = 100.00  # USD
```

### **Retry Strategy**
```python
# Exponential backoff pentru AI errors
RETRY_DELAYS = [5, 30, 300]  # secunde
MAX_RETRIES = 3
```

### **Cache AI Responses**
```python
# Evită reprocessare pentru articole identice
# Hash text_articol → Cache metadate/issues 24h
```

---

**Următorul Pas:** Vrei să încep cu implementarea `AIService` și `ExportService`?
