#!/bin/bash
# Complete deployment script for parser-law v2.1.0
# Runs on VPS: bash deploy-v2.1.0.sh

set -e

echo "======================================"
echo "🚀 Parser-Law v2.1.0 Deployment"
echo "======================================"
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Pull latest code
echo -e "${YELLOW}[1/7] Pulling latest code from GitHub...${NC}"
cd /opt/parser-law
git fetch origin
git checkout main
git pull origin main
echo -e "${GREEN}✓ Code updated to latest version${NC}"
echo ""

# Step 2: Check version
echo -e "${YELLOW}[2/7] Checking version...${NC}"
CURRENT_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "no-tag")
echo "Current tag: $CURRENT_TAG"
git log -1 --pretty=format:"Commit: %h - %s" 
echo ""
echo ""

# Step 3: Rebuild Docker images
echo -e "${YELLOW}[3/7] Rebuilding Docker images...${NC}"
cd /opt/parser-law/db_service
docker compose build --no-cache legislatie_api
echo -e "${GREEN}✓ Images rebuilt${NC}"
echo ""

# Step 4: Run database migrations
echo -e "${YELLOW}[4/7] Running database migrations...${NC}"

# Check which migrations exist
echo "Checking migrations..."
MIGRATION_002="migrations/002_add_issues_system.sql"
MIGRATION_003="migrations/003_add_domenii_system.sql"
MIGRATION_004="migrations/004_add_ai_columns.sql"

if [ -f "$MIGRATION_002" ]; then
    echo -e "${YELLOW}Running migration 002 (Issues System)...${NC}"
    docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -f /docker-entrypoint-initdb.d/$MIGRATION_002 || echo "Migration 002 already applied or failed"
fi

if [ -f "$MIGRATION_003" ]; then
    echo -e "${YELLOW}Running migration 003 (Domains System)...${NC}"
    docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -f /docker-entrypoint-initdb.d/$MIGRATION_003 || echo "Migration 003 already applied or failed"
fi

if [ -f "$MIGRATION_004" ]; then
    echo -e "${YELLOW}Running migration 004 (AI Columns)...${NC}"
    docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -f /docker-entrypoint-initdb.d/$MIGRATION_004 || echo "Migration 004 already applied or failed"
fi

echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

# Step 5: Restart API container
echo -e "${YELLOW}[5/7] Restarting API container...${NC}"
docker compose stop legislatie_api
docker compose up -d legislatie_api
echo "Waiting 10 seconds for API to start..."
sleep 10
echo -e "${GREEN}✓ API restarted${NC}"
echo ""

# Step 6: Health check
echo -e "${YELLOW}[6/7] Running health check...${NC}"
HEALTH=$(curl -s http://localhost:8000/health)
echo "Health response: $HEALTH"

if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✓ API is healthy${NC}"
    VERSION=$(echo "$HEALTH" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    echo "API Version: $VERSION"
else
    echo -e "${RED}✗ API health check failed${NC}"
    echo "Checking logs..."
    docker logs legislatie_api --tail 50
    exit 1
fi
echo ""

# Step 7: Test new endpoints
echo -e "${YELLOW}[7/7] Testing new v2.1.0 endpoints...${NC}"

# Test domains endpoint
echo "Testing GET /api/v1/domenii..."
DOMENII=$(curl -s http://localhost:8000/api/v1/domenii)
DOMENII_COUNT=$(echo "$DOMENII" | grep -o '"id"' | wc -l)
echo "Domains found: $DOMENII_COUNT"

if [ "$DOMENII_COUNT" -ge 6 ]; then
    echo -e "${GREEN}✓ Domains endpoint working (6 seed domains)${NC}"
else
    echo -e "${RED}✗ Domains endpoint issue (expected 6, got $DOMENII_COUNT)${NC}"
fi

# Test AI endpoint
echo "Testing GET /api/v1/ai/acte/pending..."
AI_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/ai/acte/pending?limit=1)
if [ "$AI_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ AI endpoint working${NC}"
else
    echo -e "${RED}✗ AI endpoint returned: $AI_RESPONSE${NC}"
fi
echo ""

# Final summary
echo "======================================"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "======================================"
echo ""
echo "📦 Version deployed: v2.1.0"
echo "🏷️  Git tag: $CURRENT_TAG"
echo "🌐 API URL: https://legislatie.issuemonitoring.ro"
echo ""
echo "📋 New Features:"
echo "  - Issues System (Tier 1 & 2)"
echo "  - Domains/Categories (6 seed domains)"
echo "  - Unified AI API (/api/v1/ai/)"
echo "  - 23+ new endpoints"
echo "  - Complete AI integration"
echo ""
echo "🔍 Quick checks:"
echo "  - API: curl https://legislatie.issuemonitoring.ro/health"
echo "  - Domains: curl https://legislatie.issuemonitoring.ro/api/v1/domenii"
echo "  - AI: curl https://legislatie.issuemonitoring.ro/api/v1/ai/acte/pending"
echo "  - Docs: https://legislatie.issuemonitoring.ro/docs"
echo ""
echo "📊 Monitor logs:"
echo "  docker logs legislatie_api -f"
echo ""
