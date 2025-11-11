# Rollback Instructions - v1.0-stable

**Versiune stabilă salvată:** v1.0-stable  
**Commit:** 7573885  
**Data backup:** 11 Noiembrie 2025

---

## 📦 Ce Am Salvat

### 1. Code Backup
- ✅ **GitHub Repository:** Tag `v1.0-stable` pushed
- ✅ **VPS Code:** `/opt/parser-law` updated la commit 7573885
- ✅ **Local Code:** Toate modificările committed și pushed

### 2. Database Backup
- ✅ **Local:** `legislatie_db_dump_20251111_190951.sql` (4.8MB)
- ✅ **VPS:** `/opt/parser-law/backups/v1.0-stable/database_backup_20251111.sql`
- ✅ **CSV Exports:** Toate tabelele în `export_csv/`

### 3. Documentation Backup
- ✅ `DATABASE_DOCUMENTATION.md` - Schema completă
- ✅ `CODE_REVIEW_AND_REFACTORING.md` - Review + plan refactoring
- ✅ `ARCHITECTURE_COMPARISON.md` - Before/After comparison
- ✅ `metadata_extractor.py` - Preview Faza 1

---

## 🔄 Cum Revin la Versiunea Stabilă

### Scenario 1: Refactoring-ul nu merge, vreau să revin

#### Pe Local (Windows)

```powershell
# Navigheză la repo
cd C:\Users\octavian\scraper\parser_law\parser-law

# Verifică ce modificări ai
git status

# Dacă ai modificări nesalvate, salvează-le
git stash

# Revin la versiunea stabilă
git checkout v1.0-stable

# Sau resetează master la versiunea stabilă
git checkout master
git reset --hard v1.0-stable
git push origin master --force
```

#### Pe VPS (Production)

```bash
# SSH în VPS
ssh root@77.237.235.158

# Navigheză la repo
cd /opt/parser-law

# Revin la versiunea stabilă
git fetch --all
git checkout v1.0-stable

# Restart API cu versiunea stabilă
cd db_service
docker-compose restart legislatie_api

# Verifică că funcționează
curl http://localhost:8000/health
```

---

### Scenario 2: Database-ul e corupt, vreau să restaurez

#### Restore Database pe VPS

**Opțiunea 1: Script Automat**

```bash
ssh root@77.237.235.158
cd /opt/parser-law/backups/v1.0-stable
bash restore.sh
```

**Opțiunea 2: Manual**

```bash
ssh root@77.237.235.158

# Stop API
cd /opt/parser-law/db_service
docker-compose down legislatie_api

# Restore database
docker exec -i legislatie_postgres psql -U legislatie_user -d monitoring_platform < /opt/parser-law/backups/v1.0-stable/database_backup_20251111.sql

# Start API
docker-compose up -d legislatie_api

# Verifică
curl http://localhost:8000/health
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "SELECT COUNT(*) FROM legislatie.acte_legislative"
# Expected: 12 acte (sau 5 din backup original)
```

#### Restore Database Local (dacă ai PostgreSQL local)

```powershell
# Restaurează din dump local
psql -U your_user -d your_database < legislatie_db_dump_20251111_190951.sql
```

---

### Scenario 3: Vreau să compar cod Before/After

```bash
# Verifică diferențele între master și v1.0-stable
git diff v1.0-stable master

# Verifică ce fișiere s-au schimbat
git diff --name-status v1.0-stable master

# Verifică modificări pentru un fișier specific
git diff v1.0-stable master -- html_parser.py
```

---

## ✅ Verificări Post-Restore

După ce faci rollback, verifică că totul funcționează:

### 1. API Health Check

```bash
curl http://legislatie.issuemonitoring.ro/health
# Expected: {"status": "healthy", ...}
```

### 2. Database Connection

```bash
ssh root@77.237.235.158
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "SELECT version()"
```

### 3. Test Endpoint Principal

```bash
# Test GET acte
curl http://legislatie.issuemonitoring.ro/api/v1/acte | python3 -m json.tool | head -20

# Test export endpoint
curl http://legislatie.issuemonitoring.ro/api/v1/acte/68/export-for-analysis | python3 -m json.tool | head -30
```

### 4. Test Categories

```bash
# Test categories list
curl http://legislatie.issuemonitoring.ro/api/v1/categories | python3 -m json.tool
```

### 5. Web UI

Deschide în browser:
- http://legislatie.issuemonitoring.ro
- Verifică că se încarcă lista de acte
- Verifică că butonul "Manage Categories" funcționează

---

## 📊 Stats Versiune v1.0-stable

### Code Stats
- **Total linii cod:** ~15,000
- **Fișiere Python:** ~50
- **API endpoints:** 48
- **Services:** 5
- **Models:** 10

### Database Stats
- **Acte legislative:** 12 (pe VPS) / 5 (în backup original)
- **Articole:** ~2,000+
- **Categories:** 1 (default: "Necategorizat")
- **Issues:** 0

### Features Funcționale
- ✅ Scraping + Parsing (hybrid_parser.py)
- ✅ Import CSV + Markdown
- ✅ Categories system (sync cu Issue Monitoring)
- ✅ Export for analysis (pentru AI labeling)
- ✅ Web UI cu category management
- ✅ 6 category endpoints
- ✅ Full CRUD pentru acte și articole

---

## 🚨 Important: Înainte de Refactoring

### Checklist Pre-Refactoring

- [x] ✅ Code backed up pe GitHub (v1.0-stable tag)
- [x] ✅ Code backed up pe VPS (/opt/parser-law)
- [x] ✅ Database backed up local (SQL dump)
- [x] ✅ Database backed up pe VPS (backups/v1.0-stable/)
- [x] ✅ CSV exports salvate (toate tabelele)
- [x] ✅ Documentation completă (3 documente MD)
- [x] ✅ Restore script testat
- [x] ✅ API funcțional verificat

### Plan Refactoring (Faza 1)

Următorii pași:
1. **Metadata Extractor** - Consolidare (2-3 ore)
2. **Query Builder** - Centralizare queries (3-4 ore)
3. **Endpoint Consolidation** - Merge endpoints (2-3 ore)

**Estimat:** 1-2 zile pentru Faza 1

---

## 📞 Contact în Caz de Probleme

Dacă ceva nu merge după rollback:

1. **Verifică logs:**
   ```bash
   ssh root@77.237.235.158
   cd /opt/parser-law/db_service
   docker-compose logs -f legislatie_api --tail=100
   ```

2. **Verifică database:**
   ```bash
   docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\dt legislatie.*"
   ```

3. **Restart complet:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

**Document creat:** 11 Noiembrie 2025  
**Ultima verificare:** Sistemul funcțional 100%  
**Status:** ✅ SAFE TO PROCEED with refactoring
