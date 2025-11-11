# Local Development Setup Guide

**Problem**: Testing pe VPS este slow și risky. GitHub Copilot nu are acces la VPS.

**Solution**: Local development environment identic cu production.

---

## Quick Start (5 Minute Setup)

### Step 1: Verifică Prerequisites

```powershell
# Check Docker Desktop is running
docker --version
# Expected: Docker version 24.0+

docker-compose --version
# Expected: Docker Compose version v2.20+

# Check Python
python --version
# Expected: Python 3.11+
```

---

### Step 2: Create Local Environment File

```powershell
# Copy template
cp .env.example .env

# Edit .env
notepad .env
```

**Critical changes pentru LOCAL**:
```bash
# Database - Use localhost (NOT container name!)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=monitoring_platform
POSTGRES_USER=parser_user
POSTGRES_PASSWORD=local_dev_password_123

# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=DEBUG

# Environment
ENVIRONMENT=development
DEBUG=true
```

---

### Step 3: Start Local Environment

```powershell
# Start all services (Postgres + API)
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy (30 seconds)
Start-Sleep -Seconds 30

# Check status
docker-compose -f docker-compose.dev.yml ps

# Expected output:
# NAME                   STATUS              PORTS
# parser-law-postgres    Up (healthy)        0.0.0.0:5432->5432/tcp
# parser-law-api         Up (healthy)        0.0.0.0:8000->8000/tcp
```

---

### Step 4: Verify Setup

```powershell
# Check API health
curl http://localhost:8000/health

# Expected: {"status":"healthy","version":"1.0.0"}

# Check API docs
start http://localhost:8000/docs
# Opens Swagger UI in browser

# Check database
docker exec -it parser-law-postgres psql -U parser_user -d monitoring_platform -c "\dt legislatie.*"
# Should show 12 tables
```

---

## Development Workflow

### Scenario 1: API Development (Most Common)

```powershell
# 1. Create feature branch
git checkout -b feature/new-endpoint

# 2. Edit code (e.g., db_service/app/routes/acte.py)
code db_service/app/routes/acte.py

# 3. Code is HOT-RELOADED automatically!
#    Changes visible immediately at http://localhost:8000

# 4. Test in browser or curl
curl http://localhost:8000/api/v1/acte

# 5. View logs in real-time
docker-compose -f docker-compose.dev.yml logs -f api

# 6. When done, commit
git add .
git commit -m "feat(acte): Add new endpoint"
```

**Hot Reload**: Code changes → Uvicorn reloads → Test immediately (no rebuild!)

---

### Scenario 2: Database Schema Changes

```powershell
# 1. Edit models (e.g., db_service/app/models/acte.py)
code db_service/app/models/acte.py

# 2. Create migration
docker exec -it parser-law-api alembic revision --autogenerate -m "Add new column"

# 3. Review migration
code db_service/alembic/versions/xxxx_add_new_column.py

# 4. Apply migration locally
docker exec -it parser-law-api alembic upgrade head

# 5. Test with data
docker exec -it parser-law-postgres psql -U parser_user -d monitoring_platform
# Run SQL queries to test

# 6. Commit migration
git add db_service/alembic/versions/
git commit -m "db: Add new column to acte"
```

---

### Scenario 3: Parser Development (No Docker Needed)

```powershell
# 1. Create Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Edit parser (e.g., hybrid_parser.py)
code hybrid_parser.py

# 4. Test parser directly (no Docker)
python hybrid_parser.py --test-url "https://legislatie.just.ro/..."

# 5. See results in rezultate/
ls rezultate/

# 6. Commit when ready
git add hybrid_parser.py
git commit -m "feat(parser): Improve metadata extraction"
```

---

## GitHub Copilot Integration

### Why Local Development Helps AI

**VPS (Current)**:
```
❌ Copilot can't see VPS files
❌ Copilot can't run tests
❌ Manual context copying
❌ No real-time feedback
```

**Local (New)**:
```
✅ Copilot sees all files
✅ Copilot can run tests
✅ Full workspace context
✅ Real-time suggestions
✅ Can execute terminal commands
```

### Example: AI-Assisted Development

```powershell
# 1. Start local env
docker-compose -f docker-compose.dev.yml up -d

# 2. Open VS Code
code .

# 3. Ask Copilot: "Add endpoint to search acte by category"
# Copilot can:
#   - Read existing routes
#   - See database schema
#   - Generate code
#   - Run tests
#   - Fix errors

# 4. Test immediately
curl http://localhost:8000/api/v1/acte?category=lege

# 5. Iterate with Copilot until perfect

# 6. Commit
git add .
git commit -m "feat(acte): Add category search"
```

---

## Local vs VPS Comparison

| Aspect | Local Dev | VPS Production |
|--------|-----------|----------------|
| **Speed** | Instant (local files) | 2-3 sec SSH lag |
| **Hot Reload** | ✅ Yes (code changes → reload) | ❌ No (need rebuild) |
| **AI Access** | ✅ Full workspace | ❌ No access |
| **Risk** | ✅ Safe (isolated) | ❌ Testing în production |
| **Database** | ✅ Can wipe/recreate | ❌ Production data |
| **Debugging** | ✅ VS Code debugger | ❌ Print statements only |
| **Cost** | Free (local resources) | $$ (VPS resources) |

---

## Common Commands Cheat Sheet

### Starting/Stopping

```powershell
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Start specific service
docker-compose -f docker-compose.dev.yml up -d postgres

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (WIPE database)
docker-compose -f docker-compose.dev.yml down -v
```

### Logs & Debugging

```powershell
# View all logs
docker-compose -f docker-compose.dev.yml logs -f

# View API logs only
docker-compose -f docker-compose.dev.yml logs -f api

# View last 50 lines
docker-compose -f docker-compose.dev.yml logs --tail=50 api

# Check container status
docker-compose -f docker-compose.dev.yml ps
```

### Database Access

```powershell
# Connect to PostgreSQL
docker exec -it parser-law-postgres psql -U parser_user -d monitoring_platform

# Run SQL query directly
docker exec -it parser-law-postgres psql -U parser_user -d monitoring_platform -c "SELECT COUNT(*) FROM legislatie.acte_legislative;"

# Backup local database
docker exec parser-law-postgres pg_dump -U parser_user monitoring_platform > local_backup.sql

# Restore from backup
cat local_backup.sql | docker exec -i parser-law-postgres psql -U parser_user -d monitoring_platform
```

### API Testing

```powershell
# Health check
curl http://localhost:8000/health

# API docs (Swagger)
start http://localhost:8000/docs

# Test endpoint
curl http://localhost:8000/api/v1/acte

# Test with JSON body
curl -X POST http://localhost:8000/api/v1/acte `
  -H "Content-Type: application/json" `
  -d '{"titlu":"Test","tip_act":"LEGE"}'
```

---

## Troubleshooting

### Issue: Port 5432 already in use

```powershell
# Check what's using port 5432
netstat -ano | findstr :5432

# Kill process (if safe)
taskkill /PID <PID> /F

# OR change port in docker-compose.dev.yml
ports:
  - "5433:5432"  # Use 5433 instead
```

### Issue: API not reloading on code changes

```powershell
# Check volume mount
docker inspect parser-law-api | findstr "Mounts"

# Restart API service
docker-compose -f docker-compose.dev.yml restart api

# View logs for errors
docker-compose -f docker-compose.dev.yml logs -f api
```

### Issue: Database connection refused

```powershell
# Check .env has POSTGRES_HOST=localhost (not container name!)
cat .env | findstr POSTGRES_HOST

# Check container is running
docker ps | findstr postgres

# Check container logs
docker logs parser-law-postgres
```

### Issue: Import errors after adding new dependencies

```powershell
# Rebuild API container
docker-compose -f docker-compose.dev.yml up -d --build api

# Or update requirements.txt and rebuild
pip freeze > requirements.txt
docker-compose -f docker-compose.dev.yml build api
```

---

## When to Test Locally vs VPS

### Test Locally (90% of time)

- ✅ New features
- ✅ Bug fixes
- ✅ Refactoring
- ✅ Database schema changes
- ✅ API endpoint changes
- ✅ Parser improvements

### Test on VPS (10% of time)

- ⚠️ Deployment process verification
- ⚠️ Performance with production data
- ⚠️ Network/firewall issues
- ⚠️ SSL/HTTPS configuration
- ⚠️ Scheduled jobs (cron)
- ⚠️ Production-only integrations

---

## New Development Flow

### OLD (Slow & Risky)
```
1. Edit code locally
2. Commit to Git
3. Push to GitHub
4. SSH to VPS
5. Pull from GitHub
6. Rebuild containers
7. Test on VPS
8. Find bug
9. Repeat steps 1-8
⏱️ Total: 10-15 minutes per iteration
```

### NEW (Fast & Safe)
```
1. Edit code locally
2. Test immediately (hot reload)
3. Fix bugs locally
4. Run tests locally
5. When perfect: Commit to Git
6. Push to feature branch
7. Create PR
8. Merge to develop
9. Deploy to VPS (only stable code)
⏱️ Total: 30 seconds per iteration locally
```

**Improvement**: 20-30x faster iteration!

---

## VS Code Integration

### Recommended Extensions

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",              // Python support
    "ms-python.vscode-pylance",      // Type checking
    "ms-azuretools.vscode-docker",   // Docker management
    "github.copilot",                // AI assistance
    "ms-vscode.makefile-tools",      // Makefile support
    "humao.rest-client"              // API testing
  ]
}
```

### VS Code Settings

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/Scripts/python.exe",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### Launch Configuration (Debugger)

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}/db_service/app",
          "remoteRoot": "/app/app"
        }
      ]
    }
  ]
}
```

---

## Summary

### Benefits of Local Development

1. **Speed**: 20-30x faster iteration
2. **AI Access**: GitHub Copilot sees everything
3. **Safety**: No risk to production
4. **Debugging**: VS Code debugger, breakpoints
5. **Cost**: Free (no VPS usage)
6. **Offline**: Works without internet (after initial setup)

### Setup Time

- **Initial setup**: 5 minutes
- **Daily startup**: 30 seconds
- **Iteration speed**: Instant (hot reload)

### Recommendation

**Use local dev for 90% of work**:
- All feature development
- All bug fixing
- All refactoring
- All testing

**Use VPS only for**:
- Final verification before release
- Performance testing with production data
- Deployment testing

---

**Next Steps**:
1. Run setup commands above (5 min)
2. Test that http://localhost:8000/health works
3. Make a small code change and see hot reload
4. Commit to feature branch (not master!)
5. Continue development locally

**Questions?** Check Troubleshooting section or ask in Slack.

---

**Created**: 2025-11-11  
**Version**: 1.0.0  
**Status**: ✅ Ready to use
