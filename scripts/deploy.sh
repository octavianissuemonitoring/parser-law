#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DEPLOY_DIR="/opt/parser-law"
BACKUP_DIR="/opt/parser-law-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/backup_$TIMESTAMP"

echo -e "${GREEN}🚀 Starting deployment...${NC}"

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

# Save current git commit hash
cd $DEPLOY_DIR
CURRENT_COMMIT=$(git rev-parse HEAD)
echo $CURRENT_COMMIT > /tmp/last_commit.txt
echo -e "${YELLOW}📝 Current commit: $CURRENT_COMMIT${NC}"

# Backup current state
echo -e "${YELLOW}💾 Creating backup...${NC}"
mkdir -p $BACKUP_PATH
cp -r $DEPLOY_DIR/* $BACKUP_PATH/ 2>/dev/null || true
echo $CURRENT_COMMIT > $BACKUP_PATH/commit_hash.txt

# Pull latest changes
echo -e "${YELLOW}📥 Pulling from GitHub...${NC}"
git fetch origin
NEW_COMMIT=$(git rev-parse origin/master)
echo -e "${YELLOW}📝 New commit: $NEW_COMMIT${NC}"

if [ "$CURRENT_COMMIT" = "$NEW_COMMIT" ]; then
    echo -e "${GREEN}✅ Already up to date!${NC}"
    exit 0
fi

git pull origin master

# Check if critical files changed
CHANGED_FILES=$(git diff --name-only $CURRENT_COMMIT $NEW_COMMIT)
echo -e "${YELLOW}📝 Changed files:${NC}"
echo "$CHANGED_FILES"

# Determine restart strategy
NEEDS_REBUILD=false
if echo "$CHANGED_FILES" | grep -q "Dockerfile"; then
    NEEDS_REBUILD=true
fi

# Restart services
if [ "$NEEDS_REBUILD" = true ]; then
    echo -e "${YELLOW}🔨 Rebuilding containers...${NC}"
    cd $DEPLOY_DIR/db_service
    docker compose down
    docker compose build --no-cache
    docker compose up -d
else
    echo -e "${YELLOW}♻️  Restarting services...${NC}"
    cd $DEPLOY_DIR/db_service
    docker compose restart api
fi

# Restart scheduler if exists
if [ -f "$DEPLOY_DIR/docker-compose.scheduler.yml" ]; then
    echo -e "${YELLOW}♻️  Restarting scheduler...${NC}"
    cd $DEPLOY_DIR
    docker compose -f docker-compose.scheduler.yml restart || true
fi

# Wait for health check
echo -e "${YELLOW}🏥 Checking health...${NC}"
sleep 10

# Health check
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo -e "${GREEN}✅ Health check passed${NC}"
    
    # Keep only last 5 backups
    cd $BACKUP_DIR
    ls -t | tail -n +6 | xargs -r rm -rf
    
    echo -e "${GREEN}📊 Container status:${NC}"
    cd $DEPLOY_DIR/db_service
    docker compose ps
    
    echo ""
    echo -e "${GREEN}🌐 Service URLs:${NC}"
    echo -e "  Health: ${GREEN}https://legislatie.issuemonitoring.ro/health${NC}"
    echo -e "  Docs:   ${GREEN}https://legislatie.issuemonitoring.ro/docs${NC}"
else
    echo -e "${RED}❌ Health check failed! Rolling back...${NC}"
    $DEPLOY_DIR/scripts/rollback.sh $BACKUP_PATH
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${YELLOW}ℹ️  To rollback, run: ./scripts/rollback.sh $BACKUP_PATH${NC}"
