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
- ✅ **Scheduler automat** - Scraping periodic cu cron jobs
- ✅ **Database API** - FastAPI cu PostgreSQL pentru stocare
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
│       └── services/         # Business logic
│
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

## 📊 API Database Service

FastAPI backend cu PostgreSQL pentru management acte legislative:

- **Swagger UI:** https://legislatie.issuemonitoring.ro/docs
- **Health Check:** https://legislatie.issuemonitoring.ro/health
- **Import API:** POST `/api/v1/acte/import`
- **Query API:** GET `/api/v1/acte`

Vezi documentația completă: [db_service/README.md](./db_service/README.md)

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
**Repository:** https://github.com/octavianissuemonitoring/parser-law  
**Ultima actualizare:** 8 noiembrie 2025  
**Versiune:** 2.0.0
