#!/bin/bash
# Quick deployment script - copy-paste in VPS terminal

echo "🚀 Deploying parser-law v2.1.0..."

cd /opt/parser-law || exit 1
git pull origin main

cd db_service || exit 1

echo "📦 Rebuilding API image..."
docker compose build --no-cache legislatie_api

echo "🗄️  Running migrations..."
cat migrations/002_add_issues_system.sql | docker exec -i legislatie_postgres psql -U legislatie_user -d monitoring_platform 2>&1 | grep -v "already exists" || true
cat migrations/003_add_domenii_system.sql | docker exec -i legislatie_postgres psql -U legislatie_user -d monitoring_platform 2>&1 | grep -v "already exists" || true
cat migrations/004_add_ai_columns.sql | docker exec -i legislatie_postgres psql -U legislatie_user -d monitoring_platform 2>&1 | grep -v "already exists" || true

echo "🔄 Restarting API..."
docker compose stop legislatie_api
docker compose up -d legislatie_api

echo "⏳ Waiting 15 seconds for startup..."
sleep 15

echo "✅ Health check..."
curl -s http://localhost:8000/health | jq .

echo ""
echo "🎉 Deployment complete!"
echo "Test endpoints:"
echo "  curl http://localhost:8000/api/v1/domenii | jq ."
echo "  curl http://localhost:8000/api/v1/ai/acte/pending?limit=1 | jq ."
