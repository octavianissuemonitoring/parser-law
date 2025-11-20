# Deployment Commands for v2.1.0 on VPS

## Connect to VPS
```bash
ssh octavian@109.123.249.228
```

## Run Deployment

```bash
# Navigate to project
cd /opt/parser-law

# Pull latest code (v2.1.0)
git fetch origin
git checkout main
git pull origin main

# Verify version
git describe --tags --abbrev=0
git log -1 --oneline

# Navigate to db_service
cd /opt/parser-law/db_service

# Rebuild API container
docker compose build --no-cache legislatie_api

# Run migrations
echo "Running migration 002 - Issues System..."
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform < migrations/002_add_issues_system.sql

echo "Running migration 003 - Domains System..."
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform < migrations/003_add_domenii_system.sql

echo "Running migration 004 - AI Columns..."
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform < migrations/004_add_ai_columns.sql

# Restart API
docker compose stop legislatie_api
docker compose up -d legislatie_api

# Wait for startup
sleep 10

# Health check
curl http://localhost:8000/health

# Test new endpoints
curl http://localhost:8000/api/v1/domenii | jq .
curl http://localhost:8000/api/v1/ai/acte/pending?limit=1 | jq .

# Check logs
docker logs legislatie_api --tail 50
```

## Quick One-Liner Deployment

```bash
cd /opt/parser-law && \
git pull origin main && \
cd db_service && \
docker compose build --no-cache legislatie_api && \
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform < migrations/002_add_issues_system.sql 2>/dev/null || true && \
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform < migrations/003_add_domenii_system.sql 2>/dev/null || true && \
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform < migrations/004_add_ai_columns.sql 2>/dev/null || true && \
docker compose stop legislatie_api && \
docker compose up -d legislatie_api && \
sleep 10 && \
curl http://localhost:8000/health
```

## Verification

```bash
# Check version
curl https://legislatie.issuemonitoring.ro/health

# Expected response:
# {"status":"healthy","service":"Legislatie Database API","version":"2.1.0"}

# Test domains
curl https://legislatie.issuemonitoring.ro/api/v1/domenii

# Expected: 6 domains (FARMA, DISP_MED, TUTUN, PROT_CONS, SANATATE, MEDIU)

# Test AI endpoint
curl https://legislatie.issuemonitoring.ro/api/v1/ai/acte/pending?limit=1

# Expected: List of acts with domains and article counts

# View API docs
# Open browser: https://legislatie.issuemonitoring.ro/docs
```

## Rollback (if needed)

```bash
cd /opt/parser-law
git checkout v1.0.0
cd db_service
docker compose build --no-cache legislatie_api
docker compose restart legislatie_api
```

## Troubleshooting

```bash
# Check container status
docker compose ps

# View logs
docker logs legislatie_api -f

# Check database
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "SELECT COUNT(*) FROM legislatie.domenii;"
# Expected: 6

docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\d legislatie.articole" | grep ai_status
# Expected: ai_status column exists

# Restart all services
docker compose restart

# Full rebuild
docker compose down
docker compose up -d --build
```
