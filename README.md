# Parser pentru Acte Legislative Românești

Parser robust pentru extragerea structurată a actelor legislative de pe [legislatie.just.ro](https://legislatie.just.ro).

## 🎯 Caracteristici

- ✅ **Parsare HTML cu CSS** - Folosește clasele CSS specifice pentru extragere precisă
- ✅ **Metadata completă** - Extrage tip act, număr, dată, MOF, denumire
- ✅ **Structură ierarhică** - Identifică Titluri, Capitole, Secțiuni, Articole
- ✅ **Quality Checking** - Validare structură și formatare Markdown
- ✅ **Deduplicare** - Elimină intrările duplicate automat
- ✅ **Multiple formate** - Salvează în CSV și Markdown
- ✅ **Batch processing** - Procesează multiple documente din listă
- ✅ **Scheduler automat** - Scraping periodic Luni-Joi 14:00
- ✅ **Database API** - FastAPI cu PostgreSQL pentru stocare
- ✅ **Web Interface** - UI pentru management linkuri și vizualizare acte
- ✅ **Manual Scraping** - Buton "⚙️ Procesează" pentru scraping ad-hoc
- ✅ **Change tracking** - Detectează modificări între versiuni

## 📂 Structura Proiectului

```
parser-law/
│
├── scraper_legislatie.py    # Script principal scraping
├── hybrid_parser.py          # Parser HTML optimizat
├── quality_checker.py        # Validare calitate și formatare
├── scheduler.py              # Scraping automat periodic
├── cleanup_files.py          # Curățare fișiere vechi
│
├── db_service/               # API Database Service
│   ├── docker-compose.yml    # PostgreSQL + FastAPI
│   ├── Dockerfile            # Container API
│   ├── create_tables.sql     # Schema database
│   └── app/
│       ├── main.py           # FastAPI endpoints
│       ├── models/           # SQLAlchemy models
│       ├── schemas/          # Pydantic schemas
│       ├── services/         # Business logic
│       └── static/           # Web Interface
│           └── index.html    # UI pentru management acte
│
├── docker-compose.scheduler.yml  # Scheduler container
├── Dockerfile.scheduler           # Container scheduler
├── linkuri_legislatie.txt    # Lista URL-uri de procesat
├── rezultate/                # Output scraping (CSV + MD)
│
└── scripts/
    ├── setup-vps.sh          # Setup automat VPS
    └── deploy-vps.sh         # Deployment script
```

## 🚀 Quick Start

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/octavianissuemonitoring/parser-law.git
cd parser-law

# 2. Install dependencies
pip install -r requirements-scheduler.txt

# 3. Adaugă URL-uri în linkuri_legislatie.txt
echo "https://legislatie.just.ro/Public/DetaliiDocument/282518" >> linkuri_legislatie.txt

# 4. Rulează scraper
python scraper_legislatie.py

# 5. Vezi rezultatele
ls -lh rezultate/
```

### Production Deployment (VPS)

**📖 Vezi ghidul complet:** [DEPLOYMENT_VPS.md](./DEPLOYMENT_VPS.md)

```bash
# Setup rapid cu script automat
curl -fsSL https://raw.githubusercontent.com/octavianissuemonitoring/parser-law/master/scripts/setup-vps.sh | bash

# Sau manual
cd /opt
git clone https://github.com/octavianissuemonitoring/parser-law.git
cd parser-law/db_service
docker compose up -d
```

**🌐 Live Instance:** https://legislatie.issuemonitoring.ro/docs

## �️ Web Interface

Interfață completă pentru management acte legislative disponibilă la:  
**https://legislatie.issuemonitoring.ro/static/index.html**

### Funcționalități

**1. Tab Linkuri:**
- Adaugă URL-uri de legislație
- Vezi lista completă linkuri procesate
- Buton "⚙️ Procesează" pentru scraping manual ad-hoc
- Automat import în database după scraping

**2. Tab Acte:**
- Lista completă acte normative din database
- Filtrare și sortare
- Detalii metadata (tip act, număr, dată, MOF)

**3. Tab Index Sistematizat:**
- Vizualizare ierarhică articole
- Grupare pe Titluri și Capitole
- 500 articole per act (limitare API)

**4. Tab Statistici:**
- Total acte în database
- Total articole
- Distribuție pe tipuri acte

### Arhitectură Web Interface

```
┌─────────────────────────────────────────────────────────┐
│                  Web Browser (Client)                    │
│  https://legislatie.issuemonitoring.ro/static/index.html │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS (Nginx)
                        ▼
┌─────────────────────────────────────────────────────────┐
│            FastAPI (legislatie_api:8000)                 │
│  - /static/index.html    (Web UI)                        │
│  - GET /api/v1/links     (Lista linkuri)                 │
│  - POST /api/v1/links    (Adaugă link nou)               │
│  - POST /api/v1/links/process?url=...  (Scraping manual) │
│  - GET /api/v1/acte      (Lista acte)                    │
│  - GET /api/v1/articole  (Articole act)                  │
│  - POST /api/v1/acte/import  (Import CSV → DB)           │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┴────────────────┐
        ▼                                ▼
┌──────────────────┐          ┌──────────────────┐
│   PostgreSQL     │          │   Scheduler      │
│ legislatie_postgres        │ legislatie_scheduler
│ Port: 5432       │          │ Cron: Mon-Thu 14:00
└──────────────────┘          └──────────────────┘
                                      │
                              ┌───────▼────────┐
                              │  Shared Volume │
                              │ /app/rezultate │
                              │  (CSV files)   │
                              └────────────────┘
```

### Procesare Link Manual (UI Button)

Când apeși butonul "⚙️ Procesează" din Web Interface:

1. **Frontend:** `POST /api/v1/links/process?url=...`
2. **Backend:** Rulează `scraper_legislatie.py --url <URL>` în background
3. **Scraper:** Salvează CSV în `/app/rezultate/`
4. **Frontend:** După 30 secunde, trigger automat `POST /api/v1/acte/import`
5. **Backend:** Importă CSV-uri noi în PostgreSQL
6. **Result:** Acte disponibile imediat în UI (refresh tab Acte)

**Timeout scraper:** 10 minute  
**Auto-import delay:** 30 secunde

##  API Database Service

FastAPI backend cu PostgreSQL pentru management acte legislative:

- **Swagger UI:** https://legislatie.issuemonitoring.ro/docs
- **Web Interface:** https://legislatie.issuemonitoring.ro/static/index.html
- **Health Check:** https://legislatie.issuemonitoring.ro/health

### Endpoints Principale

**Linkuri:**
- `GET /api/v1/links` - Lista toate linkurile
- `POST /api/v1/links` - Adaugă link nou
- `POST /api/v1/links/process?url=<URL>` - Scraping manual (background task)

**Acte:**
- `GET /api/v1/acte` - Lista acte (filtrare: skip, limit, search)
- `GET /api/v1/acte/{id}` - Detalii act specific
- `POST /api/v1/acte/import?rezultate_dir=/app/rezultate` - Import CSV în DB

**Articole:**
- `GET /api/v1/articole?act_id={id}&limit=500` - Articole pentru un act (max 500)

Vezi documentația completă: [db_service/README.md](./db_service/README.md)

## ⏰ Scheduler Automat

Containerul `legislatie_scheduler` rulează scraping periodic:

- **Schedule:** Luni - Joi la 14:00
- **Source:** `linkuri_legislatie.txt` (toate URL-urile)
- **Output:** `/app/rezultate/*.csv` (shared volume cu API)
- **Auto-import:** DA (trigger POST `/api/v1/acte/import` după scraping)
- **Auto-cleanup:** DA (șterge fișiere > 7 zile)

### Environment Variables Scheduler

```bash
SCRAPER_SCHEDULE=0 14 * * 1-4  # Mon-Thu 14:00 (cron format)
SCRAPER_AUTO_IMPORT=true       # Auto-import după scraping
SCRAPER_API_URL=http://legislatie_api:8000
SCRAPER_OUTPUT_DIR=/app/rezultate
SCRAPER_CLEANUP_DAYS=7         # Cleanup fișiere > 7 zile
```

### Monitorizare Scheduler

```bash
# Check logs
docker logs legislatie_scheduler --tail 100 --follow

# Check status
docker ps --filter name=legislatie_scheduler

# Manual trigger (pentru testing)
docker exec legislatie_scheduler python scheduler.py --run-now
```

Vezi ghid complet: [SCHEDULER_README.md](./SCHEDULER_README.md)

## 📝 Exemple

### Structură Output CSV

```csv
tip_act,nr_act,data_an,denumire,Art.1,Articol_Label,Text_Articol
LEGE,121,30/04/2024,privind energia eoliană offshore,1,Articolul 1,(1) Prezenta lege...
LEGE,121,30/04/2024,privind energia eoliană offshore,2,Articolul 2,În sensul prezentei legi...
```

### Exemplu Markdown Output

```markdown
# LEGE nr. 121 din 30 aprilie 2024

**Denumire:** privind energia eoliană offshore  
**Publicat:** Monitorul Oficial nr. 450 din 15 mai 2024

## TITLUL I - Dispoziții generale

### **Articolul 1** - Obiectul legii

**(1)** Prezenta lege stabilește cadrul juridic...

### **Articolul 2** - Definiții

În sensul prezentei legi, termenii și expresiile...
```

## 📈 Performanță

- ⚡ **~3-5 secunde/document** (download + parsing)
- ✅ **90%+ success rate** pe documente standard
- 🔄 **Scraping automat** cu scheduler (cron: `0 2 * * *`)
- 🧹 **Auto-cleanup** fișiere vechi (> 30 zile)

## 🔧 Configurare Avansată

### Environment Variables

```bash
# .env.scheduler
SCRAPER_SCHEDULE=0 2 * * *      # Daily at 2 AM
CLEANUP_SCHEDULE=0 3 * * 0      # Weekly Sunday 3 AM
QUALITY_CHECK=true              # Enable quality validation
LOG_LEVEL=INFO
```

### Database Configuration

```bash
# db_service/.env
DATABASE_URL=postgresql://user:pass@postgres:5432/monitoring_platform
DB_SCHEMA=legislatie
API_PORT=8000
```

## 📚 Documentație

- **[DEPLOYMENT_VPS.md](./DEPLOYMENT_VPS.md)** - Ghid complet deployment pe VPS
- **[SCHEDULER_README.md](./SCHEDULER_README.md)** - Configurare scheduler automat
- **[QUALITY_RULES.md](./QUALITY_RULES.md)** - Reguli validare calitate
- **[db_service/README.md](./db_service/README.md)** - API Database service
- **[FORMAT_MARKDOWN.md](./FORMAT_MARKDOWN.md)** - Format Markdown output

## 🐛 Troubleshooting

### Eroare: "no configuration file provided"
```bash
# Cauză: docker-compose.yml nu este în root
# Soluție: Intră în subdirectorul corect
cd db_service
docker compose up -d
```

### API Container "unhealthy"
```bash
# Cauză: Flag --reload în Dockerfile (production)
# Soluție: Elimină --reload din CMD și rebuild
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Articolele nu apar în Web Interface
```bash
# Verifică:
# 1. API limit (max 500 articole per request)
curl "https://legislatie.issuemonitoring.ro/api/v1/articole?act_id=1&limit=500"

# 2. Column names în database (trebuie: articol_nr, articol_label, capitol_denumire)
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform \
  -c "SELECT column_name FROM information_schema.columns WHERE table_name='articole'"

# 3. Frontend JS console pentru erori
# Deschide Developer Tools (F12) → Console
```

### Import CSV eșuează - Permission Denied
```bash
# Cauză: Volume mount /app/rezultate nu are permisiuni write
# Soluție: Fix permisiuni pe host
ssh root@VPS_IP
chmod 777 /opt/parser-law/rezultate
touch /opt/parser-law/rezultate/.keep  # Asigură că directorul persistă

# Verifică mount-urile sunt consistente
docker exec legislatie_scheduler ls -la /app/rezultate
docker exec legislatie_api ls -la /app/rezultate
# Ambele trebuie să arate același conținut
```

### Scheduler nu importă automat în database
```bash
# Verifică config auto_import
docker exec legislatie_scheduler env | grep SCRAPER_AUTO_IMPORT
# Trebuie: SCRAPER_AUTO_IMPORT=true

# Check volume mounts match
docker inspect legislatie_scheduler | grep -A 5 Mounts
docker inspect legislatie_api | grep -A 5 Mounts
# Ambele trebuie să monteze același director: /app/rezultate

# Test manual import
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/acte/import?rezultate_dir=/app/rezultate"
```

### Deployment - Git Pull & Restart
```bash
# Standard deployment workflow
ssh root@VPS_IP
cd /opt/parser-law
git pull origin master

# Restart doar API (fără rebuild)
cd db_service && docker compose restart api

# Restart scheduler
docker restart legislatie_scheduler

# Verify containers healthy
docker ps --filter name=legislatie
```

### Mai multe soluții în: [DEPLOYMENT_VPS.md](./DEPLOYMENT_VPS.md#-troubleshooting)

## 🎯 Roadmap

- [ ] Support pentru mai multe surse legislative
- [ ] Export PDF cu formatare
- [ ] API pentru diff între versiuni
- [ ] Frontend pentru vizualizare
- [ ] Notificări email pentru modificări

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) first.

## 📄 Licență

MIT License - Vezi [LICENSE](./LICENSE) pentru detalii.

---

**Live Deployment:** https://legislatie.issuemonitoring.ro  
**Web Interface:** https://legislatie.issuemonitoring.ro/static/index.html  
**Repository:** https://github.com/octavianissuemonitoring/parser-law  
**Ultima actualizare:** 10 noiembrie 2024  
**Versiune:** 2.1.0 - Web Interface & Manual Scraping
