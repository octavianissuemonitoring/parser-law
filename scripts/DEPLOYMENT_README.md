# Deployment Guide

Ghid complet pentru deployment cu backup și rollback automat.

## 🚀 Quick Start

### 1. Setup PowerShell Helpers (Local - Windows)

```powershell
# Adaugă helper functions în PowerShell profile
notepad $PROFILE

# Adaugă la final:
. "C:\Users\octavian\scraper\parser_law\parser-law\scripts\deploy-helpers.ps1"

# Reload profile
. $PROFILE
```

### 2. Setup Scripts pe VPS (Prima dată)

```bash
# Conectează la VPS
ssh root@77.237.235.158

# Pull ultimele modificări (include scripturile noi)
cd /opt/parser-law
git pull origin master

# Fă scripturile executabile
chmod +x scripts/*.sh

# Test
./scripts/deploy.sh
```

## 📝 Comenzi Disponibile

### Deploy (Local → GitHub → VPS)

```powershell
# Commit, push și deploy automat
deploy

# Sau cu mesaj custom
Deploy-ParserLaw -Message "Add new feature"
```

**Ce face:**
1. ✅ Verifică uncommitted changes
2. ✅ Commit și push la GitHub
3. ✅ Conectează la VPS
4. ✅ Creează backup automat
5. ✅ Pull ultimele modificări
6. ✅ Restart servicii (rebuild dacă e nevoie)
7. ✅ Health check automat
8. ✅ Rollback automat dacă health check fails

### Rollback

```powershell
# Rollback la ultimul backup
rollback

# Rollback la un backup specific
Rollback-ParserLaw -BackupPath /opt/parser-law-backups/backup_20251108_143022
```

### Vezi Backups Disponibile

```powershell
backups
```

Output:
```
📦 Available backups:
1. backup_20251108_153045 (commit: a1b2c3d4)
2. backup_20251108_143022 (commit: 9f8e7d6c)
3. backup_20251108_120015 (commit: 5a4b3c2d)
```

### Check Status

```powershell
status
```

Output:
```
📊 Service Status on VPS:
NAME                    STATUS          HEALTH
legislatie_postgres     Up 2 hours      healthy
legislatie_api          Up 2 hours      healthy

🌐 Live URLs:
  Health: https://legislatie.issuemonitoring.ro/health
  Docs:   https://legislatie.issuemonitoring.ro/docs
```

### Vezi Logs

```powershell
# Logs API
logs api

# Logs PostgreSQL
logs postgres

# Logs Scheduler
logs scheduler

# Toate logs
logs all

# Ultimele 100 de linii
Get-ParserLawLogs -Service api -Lines 100
```

## 🔄 Workflow Complet

### Dezvoltare Locală

```powershell
# 1. Fă modificări în cod
code .

# 2. Testează local
python scraper_legislatie.py

# 3. Deploy când ești gata
deploy
```

### Dacă Ceva Nu Merge

```powershell
# Rollback imediat
rollback

# Sau vezi backups și alege unul
backups
Rollback-ParserLaw -BackupPath /opt/parser-law-backups/backup_20251108_120015
```

## 📊 Structura Backups

```
/opt/parser-law-backups/
├── backup_20251108_153045/
│   ├── commit_hash.txt       # Git commit hash
│   ├── scraper_legislatie.py
│   ├── hybrid_parser.py
│   ├── db_service/
│   └── ... (toate fișierele)
├── backup_20251108_143022/
└── backup_20251108_120015/
```

- **Păstrează:** Ultimele 5 backups automat
- **Include:** Git commit hash pentru tracking
- **Exclude:** .git directory (păstrăm doar codul)

## 🛡️ Safety Features

### Automatic Backup
- ✅ Backup înainte de fiecare deployment
- ✅ Include git commit hash
- ✅ Cleanup automat (păstrează doar ultimele 5)

### Health Check
- ✅ Verifică `/health` endpoint după deployment
- ✅ Rollback automat dacă fail
- ✅ Exit code correct pentru CI/CD

### Smart Restart
- ✅ **Full rebuild** dacă Dockerfile se schimbă
- ✅ **Simple restart** pentru Python code changes
- ✅ Mai rapid și mai sigur

## 🔧 Troubleshooting

### Deploy Failed

```powershell
# Verifică logs
logs api

# Rollback
rollback

# Check status
status
```

### Manual Deployment (pe VPS direct)

```bash
ssh root@77.237.235.158
cd /opt/parser-law
./scripts/deploy.sh
```

### Manual Rollback (pe VPS direct)

```bash
ssh root@77.237.235.158
cd /opt/parser-law

# List backups
./scripts/rollback.sh

# Rollback
./scripts/rollback.sh last
```

### Clean Old Backups

```bash
# Pe VPS
cd /opt/parser-law-backups

# Șterge backups mai vechi de 7 zile
find . -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;
```

## 📚 Comenzi Avansate

### Deploy Fără Restart

```bash
# Pe VPS - doar pull code fără restart
ssh root@77.237.235.158 'cd /opt/parser-law && git pull origin master'
```

### Check Git Status

```bash
# Local
git status

# VPS
ssh root@77.237.235.158 'cd /opt/parser-law && git status && git log -1'
```

### Force Rebuild

```bash
# Pe VPS
ssh root@77.237.235.158 'cd /opt/parser-law/db_service && docker compose down && docker compose build --no-cache && docker compose up -d'
```

## 🎯 Best Practices

1. **Întotdeauna testează local** înainte de deploy
2. **Commit messages clare** pentru tracking
3. **Deploy frecvent** în small batches
4. **Verifică status** după fiecare deploy
5. **Păstrează backups** (scriptul face asta automat)

## 📊 Monitoring

### Health Check URLs

- **Health:** https://legislatie.issuemonitoring.ro/health
- **Docs:** https://legislatie.issuemonitoring.ro/docs
- **API:** https://legislatie.issuemonitoring.ro/api/v1/acte

### Docker Stats

```bash
ssh root@77.237.235.158 'docker stats --no-stream'
```

### Disk Usage

```bash
ssh root@77.237.235.158 'df -h && du -sh /opt/parser-law-backups/*'
```

---

**Last Updated:** 8 noiembrie 2025  
**Version:** 2.0.0
