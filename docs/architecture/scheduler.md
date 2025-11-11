# 🕐 Scheduler pentru Scraping Automat

## 📋 Overview

Sistem flexibil de scheduling pentru scraping automat al actelor legislative de pe legislatie.just.ro, cu:
- **3 tipuri de schedule**: Daily (Luni-Joi), Weekly, Custom
- **Auto-import** în baza de date
- **Management facil** prin PowerShell scripts
- **Docker support** pentru deployment

## 🚀 Quick Start

### Windows (PowerShell)

```powershell
# Install dependencies
pip install -r requirements-scheduler.txt

# Start scheduler (Luni-Joi la 14:00)
.\manage-scheduler.ps1 start

# Test imediat
.\manage-scheduler.ps1 test -Now

# Vezi status
.\manage-scheduler.ps1 status

# Vezi logs
.\manage-scheduler.ps1 logs
```

### Linux/Docker

```bash
# Build și start cu Docker Compose
docker-compose -f docker-compose.scheduler.yml up -d

# Vezi logs
docker-compose -f docker-compose.scheduler.yml logs -f scheduler

# Stop
docker-compose -f docker-compose.scheduler.yml down
```

## ⚙️ Configurare

### Opțiuni de Schedule

#### 1. **Daily Weekdays** (Recomandat)
Rulează la aceeași oră, Luni-Joi (sau alte zile):

```env
SCRAPER_SCHEDULE_TYPE=daily_weekdays
SCRAPER_HOUR=14              # 14:00 (2 PM)
SCRAPER_DAYS=1-4             # Luni-Joi
```

**Exemple de zile:**
- `1-4` = Luni până Joi
- `1-5` = Luni până Vineri
- `1,3,5` = Luni, Miercuri, Vineri
- `2,4` = Marți, Joi

#### 2. **Weekly** (O dată pe săptămână)
Rulează o singură dată pe săptămână:

```env
SCRAPER_SCHEDULE_TYPE=weekly
SCRAPER_WEEKLY_DAY=1         # 1=Luni, 2=Marți, ..., 7=Duminică
SCRAPER_WEEKLY_HOUR=10       # 10:00 (10 AM)
```

#### 3. **Custom** (Expresie Cron avansată)
Control total prin cron expression:

```env
SCRAPER_SCHEDULE_TYPE=custom
SCRAPER_CRON_EXPRESSION="0 14 * * 1-4"
```

**Exemple de expresii cron:**
```
"0 14 * * 1-4"        # 14:00 Luni-Joi
"0 10 * * 1"          # 10:00 în fiecare Luni
"0 8,14,20 * * *"     # 8 AM, 2 PM, 8 PM zilnic
"0 */6 * * *"         # La fiecare 6 ore
"30 9 * * 1-5"        # 9:30 AM Luni-Vineri
"0 0 * * 0"           # Miezul nopții în fiecare Duminică
```

**Format Cron:** `minute hour day_of_month month day_of_week`
- minute: 0-59
- hour: 0-23
- day_of_month: 1-31
- month: 1-12
- day_of_week: 0-7 (0 și 7 = Duminică, 1=Luni, ..., 6=Sâmbătă)

### Configurare Completă (.env.scheduler)

```env
# Enable/disable
SCRAPER_ENABLED=true

# Schedule
SCRAPER_SCHEDULE_TYPE=daily_weekdays
SCRAPER_HOUR=14
SCRAPER_DAYS=1-4

# Scraper settings
SCRAPER_DELAY=2.0                           # Delay între requests (secunde)
SCRAPER_LINKS_FILE=linkuri_legislatie.txt   # Fișier cu linkuri
SCRAPER_OUTPUT_DIR=rezultate                # Director output

# Auto-import în DB
SCRAPER_AUTO_IMPORT=true
SCRAPER_API_URL=http://localhost:8000

# AI Processing (NEW)
AI_PROCESSING_ENABLED=true
AI_PROCESSING_SCHEDULE=*/30 * * * *   # Every 30 minutes
AI_PROCESSING_BATCH_SIZE=10           # Articles per batch
AI_PROCESSING_DELAY=1.0               # Delay between API calls

# Export to Issue Monitoring (NEW)
EXPORT_ENABLED=true
EXPORT_SCHEDULE=0 * * * *             # Every hour
EXPORT_BATCH_SIZE=10                  # Acts per batch
EXPORT_SYNC_ENABLED=true              # Enable incremental sync
EXPORT_SYNC_SCHEDULE=30 * * * *       # Every hour at :30
```

## 🤖 AI Processing & Export (NEW)

### Workflow Complet

```
1. Scraper (Luni-Joi 14:00)
   ↓ Extrage legislație
   ↓ Salvează în DB
   
2. AI Processing (Every 30 min)
   ↓ Procesează articole pending
   ↓ Extrage issues/probleme
   ↓ Generează metadate
   
3. Export (Every hour)
   ↓ Trimite la Issue Monitoring
   ↓ Marchează ca exportat
   
4. Export Sync (Every hour at :30)
   ↓ Sincronizează updates
   ↓ Trimite articole/anexe noi
```

### Configurare AI

```env
# In db_service/.env
OPENAI_API_KEY=sk-proj-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
AI_PROVIDER=openai
AI_MODEL=gpt-4o

ISSUE_MONITORING_API_URL=https://api.issuemonitoring.ro/v1
ISSUE_MONITORING_API_KEY=your_key_here
```

### Schedule-uri Recomandate

**Development/Testing:**
```env
AI_PROCESSING_SCHEDULE=*/5 * * * *    # Every 5 minutes
EXPORT_SCHEDULE=*/10 * * * *          # Every 10 minutes
```

**Production:**
```env
AI_PROCESSING_SCHEDULE=*/30 * * * *   # Every 30 minutes
EXPORT_SCHEDULE=0 * * * *             # Every hour (on the hour)
EXPORT_SYNC_SCHEDULE=30 * * * *       # Every hour (at :30)
```

**Low Volume:**
```env
AI_PROCESSING_SCHEDULE=0 */2 * * *    # Every 2 hours
EXPORT_SCHEDULE=0 */4 * * *           # Every 4 hours
```

## 📖 Utilizare

### Command Line Interface

```bash
# Start scheduler
python scheduler.py

# Run imediat (test)
python scheduler.py --now

# Show config
python scheduler.py --show-config

# Test cron expression
python scheduler.py --test-cron "0 14 * * 1-4"
```

### PowerShell Management Script

```powershell
# Start cu setări default (Luni-Joi 14:00)
.\manage-scheduler.ps1 start

# Start cu setări custom
.\manage-scheduler.ps1 start -Schedule daily_weekdays -Hour 10 -Days "1-5"

# Stop scheduler
.\manage-scheduler.ps1 stop

# Restart
.\manage-scheduler.ps1 restart

# Status
.\manage-scheduler.ps1 status

# View logs (follow mode)
.\manage-scheduler.ps1 logs

# Test imediat
.\manage-scheduler.ps1 test -Now

# Show config
.\manage-scheduler.ps1 config

# Storage stats (NEW)
.\manage-scheduler.ps1 stats

# Cleanup old files (NEW)
.\manage-scheduler.ps1 cleanup
```

## 🧹 File Cleanup Management

### Auto-Cleanup

Scheduler-ul poate șterge automat fișierele duplicate după import.

**Configurare în `.env.scheduler`:**
```env
SCRAPER_AUTO_CLEANUP=true  # Enable auto-cleanup
```

**Comportament:**
- Rulează după fiecare import cu succes
- Păstrează doar **cel mai recent fișier** per act
- Șterge toate duplicate mai vechi (CSV + MD)
- Menține folder-ul `rezultate/` mic constant

**Exemplu log:**
```
2025-11-08 14:05:40 - INFO - ✅ Import completed: 7 acts
2025-11-08 14:05:41 - INFO - 🧹 Running auto-cleanup...
2025-11-08 14:05:42 - INFO - ✅ Deleted 14 files
```

### Manual Cleanup

**PowerShell:**
```powershell
# Vezi statistici storage
.\manage-scheduler.ps1 stats

# Cleanup manual
.\manage-scheduler.ps1 cleanup
```

**Python direct:**
```bash
# Vezi statistici (safe, nu modifică nimic)
python cleanup_files.py --stats

# Preview cleanup (dry run - arată ce ar șterge)
python cleanup_files.py

# Execută cleanup efectiv
python cleanup_files.py --execute

# Quiet mode (doar rezultat final)
python cleanup_files.py --execute --quiet
```

### Cleanup Output

**Preview (dry-run):**
```
📊 Found 7 acts with duplicates

📄 LEGE_121_2024
   ✅ KEEP:   LEGE_121_2024_20251108_000715.csv (2025-11-08 00:07:15)
   ❌ DELETE: LEGE_121_2024_20251107_211711.csv (0 days old)

🔍 DRY RUN: Would delete 14 files
   Run with --execute to actually delete
```

**Statistici:**
```
📊 Storage Statistics
Total files:    7 CSV + 7 MD = 14
Total size:     1.87 MB
Average size:   136.51 KB per file

✅ No duplicates found - optimal storage
```

### Storage Strategy

| Layer | Retention | Purpose |
|-------|-----------|---------|
| **rezultate/** | Latest only | Temporary staging, auto-cleanup |
| **PostgreSQL** | Permanent | Source of truth, versioning, diff tracking |
| **Backups** | 30 days | PostgreSQL automated backups |

**Avantaje:**
- ✅ Storage mic constant (~2 MB pentru 7 acte)
- ✅ No manual intervention needed
- ✅ Recovery din PostgreSQL database
- ✅ Export API disponibil on-demand

### Docker Deployment

```bash
# Start scheduler service
docker-compose -f docker-compose.scheduler.yml up -d

# View logs
docker-compose -f docker-compose.scheduler.yml logs -f

# Stop
docker-compose -f docker-compose.scheduler.yml down

# Rebuild
docker-compose -f docker-compose.scheduler.yml up -d --build
```

## 📊 Monitoring & Logs

### Log Files

**scraper_scheduler.log** - Log principal cu toate evenimente:
```
2025-11-07 14:00:00 - INFO - 🚀 Starting scheduled scraping job
2025-11-07 14:00:05 - INFO - 📥 Running scraper...
2025-11-07 14:05:30 - INFO - ✅ Scraping completed in 330.45 seconds
2025-11-07 14:05:35 - INFO - 📤 Auto-importing to database...
2025-11-07 14:05:40 - INFO - ✅ Import result: {'success': True, 'updated_acts': 3}
2025-11-07 14:05:40 - INFO - 🏁 Scheduled job completed
```

### Status Check

```powershell
# Windows
.\manage-scheduler.ps1 status

# Output:
# Status: RUNNING
# Processes:
#   PID: 12345
#   Memory: 45.6 MB
#   Start Time: 2025-11-07 13:00:00
# 
# Last 5 log entries:
# ...
```

### Next Run Time

```bash
python scheduler.py --show-config

# Output includes:
# ⏰ Next 5 scheduled runs:
#    1. 2025-11-11 14:00:00 Monday
#    2. 2025-11-12 14:00:00 Tuesday
#    3. 2025-11-13 14:00:00 Wednesday
#    4. 2025-11-14 14:00:00 Thursday
#    5. 2025-11-18 14:00:00 Monday
```

## 🔧 Configurări Avansate

### Misfire Grace Time

Dacă un job nu poate rula la timpul programat (ex: sistem oprit), poate rula în următoarele 60 minute:

```python
# În scheduler.py
misfire_grace_time=3600  # 1 hour
```

### Coalesce Multiple Runs

Dacă mai multe run-uri au fost missed, le combină într-unul singur:

```python
coalesce=True
```

### Max Instances

Permite doar o instanță a job-ului să ruleze simultan:

```python
max_instances=1
```

### Custom Delay

Ajustează delay-ul între requests pentru a fi respectuos cu serverul:

```env
SCRAPER_DELAY=3.0  # 3 secunde între requests
```

## 🐛 Troubleshooting

### Scheduler nu pornește

1. **Verifică dependințele:**
   ```bash
   pip install -r requirements-scheduler.txt
   ```

2. **Verifică fișierul de linkuri:**
   ```bash
   # Trebuie să existe linkuri_legislatie.txt
   ls linkuri_legislatie.txt
   ```

3. **Verifică permisiunile:**
   ```bash
   # Windows: rulează PowerShell ca Administrator
   # Linux: verifică permisiuni execute
   chmod +x scheduler.py
   ```

### Auto-import eșuează

1. **Verifică că API-ul rulează:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Verifică URL-ul API:**
   ```env
   SCRAPER_API_URL=http://localhost:8000  # Correct
   # NOT: http://localhost:8000/api/v1
   ```

3. **Verifică network (Docker):**
   ```bash
   docker network ls
   # Asigură-te că scheduler și API sunt în aceeași rețea
   ```

### Job nu rulează la timp

1. **Verifică expresia cron:**
   ```bash
   python scheduler.py --test-cron "0 14 * * 1-4"
   ```

2. **Verifică timezone:**
   ```python
   # Scheduler folosește timezone-ul local al sistemului
   # Verifică cu: python -c "import datetime; print(datetime.datetime.now())"
   ```

3. **Verifică logs pentru errors:**
   ```bash
   tail -f scraper_scheduler.log
   ```

## 📅 Exemple de Configurări

### Scenario 1: Actualizare zilnică Luni-Joi

```env
# Rulează în fiecare zi lucrătoare (Luni-Joi) la ora 14:00
SCRAPER_SCHEDULE_TYPE=daily_weekdays
SCRAPER_HOUR=14
SCRAPER_DAYS=1-4
```

### Scenario 2: Actualizare săptămânală

```env
# Rulează doar Luni dimineața la 10:00
SCRAPER_SCHEDULE_TYPE=weekly
SCRAPER_WEEKLY_DAY=1
SCRAPER_WEEKLY_HOUR=10
```

### Scenario 3: Actualizări frecvente (test/development)

```env
# Rulează la fiecare 4 ore
SCRAPER_SCHEDULE_TYPE=custom
SCRAPER_CRON_EXPRESSION="0 */4 * * *"
```

### Scenario 4: Actualizare la final de săptămână

```env
# Rulează Vineri seara la 18:00
SCRAPER_SCHEDULE_TYPE=weekly
SCRAPER_WEEKLY_DAY=5
SCRAPER_WEEKLY_HOUR=18
```

### Scenario 5: Multiple run-uri pe zi

```env
# Rulează la 8 AM, 2 PM și 8 PM, Luni-Vineri
SCRAPER_SCHEDULE_TYPE=custom
SCRAPER_CRON_EXPRESSION="0 8,14,20 * * 1-5"
```

## 🔐 Production Best Practices

### 1. Logging

Configurează log rotation:
```bash
# Linux: folosește logrotate
# /etc/logrotate.d/scraper-scheduler
/path/to/scraper_scheduler.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

### 2. Monitoring

Setup alerting pentru job failures:
```python
# Adaugă în scheduler.py
def send_alert(message):
    # Email, Slack, etc.
    pass

def _job_executed_listener(self, event):
    if event.exception:
        send_alert(f"Scraper failed: {event.exception}")
```

### 3. Resource Limits

Setează limite în Docker:
```yaml
# docker-compose.scheduler.yml
services:
  scheduler:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
```

### 4. Health Checks

Monitorizează prin health endpoint:
```bash
# Check dacă scheduler rulează
docker ps | grep legislatie_scheduler
docker inspect legislatie_scheduler --format='{{.State.Health.Status}}'
```

## 📚 Referințe

- **APScheduler Documentation**: https://apscheduler.readthedocs.io/
- **Cron Expression Guide**: https://crontab.guru/
- **Python datetime**: https://docs.python.org/3/library/datetime.html

## 🤝 Support

Pentru probleme sau întrebări:
1. Verifică `scraper_scheduler.log`
2. Rulează `python scheduler.py --show-config`
3. Testează manual cu `python scheduler.py --now`

---

**Versiune:** 1.0  
**Data:** 2025-11-07  
**Status:** ✅ Production Ready
