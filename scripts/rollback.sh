#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

DEPLOY_DIR="/opt/parser-law"
BACKUP_DIR="/opt/parser-law-backups"

# Function to list available backups
list_backups() {
    echo -e "${YELLOW}📦 Available backups:${NC}"
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR)" ]; then
        echo -e "${RED}No backups found${NC}"
        return
    fi
    
    cd $BACKUP_DIR
    ls -lt | grep "^d" | head -n 10 | awk '{print NR". " $9}' | while read line; do
        backup=$(echo $line | cut -d' ' -f2)
        if [ -f "$backup/commit_hash.txt" ]; then
            commit=$(cat "$backup/commit_hash.txt")
            echo -e "$line (commit: ${commit:0:8})"
        else
            echo "$line"
        fi
    done
}

# If no argument, show list
if [ -z "$1" ]; then
    list_backups
    echo ""
    echo -e "${YELLOW}Usage: ./scripts/rollback.sh <backup_path>${NC}"
    echo -e "${YELLOW}   or: ./scripts/rollback.sh last${NC}"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  ./scripts/rollback.sh last"
    echo -e "  ./scripts/rollback.sh /opt/parser-law-backups/backup_20251108_143022"
    exit 1
fi

# Determine backup path
if [ "$1" = "last" ]; then
    BACKUP_PATH=$(ls -t $BACKUP_DIR 2>/dev/null | head -n 1)
    if [ -z "$BACKUP_PATH" ]; then
        echo -e "${RED}❌ No backups found${NC}"
        exit 1
    fi
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_PATH"
else
    BACKUP_PATH=$1
fi

if [ ! -d "$BACKUP_PATH" ]; then
    echo -e "${RED}❌ Backup not found: $BACKUP_PATH${NC}"
    list_backups
    exit 1
fi

echo -e "${RED}⚠️  WARNING: This will rollback to backup: $BACKUP_PATH${NC}"
if [ -f "$BACKUP_PATH/commit_hash.txt" ]; then
    COMMIT=$(cat "$BACKUP_PATH/commit_hash.txt")
    echo -e "${YELLOW}Commit: $COMMIT${NC}"
fi
echo ""
echo -e "${YELLOW}Press Ctrl+C to cancel, or Enter to continue...${NC}"
read

echo -e "${YELLOW}🔄 Rolling back...${NC}"

# Stop current services
echo -e "${YELLOW}🛑 Stopping services...${NC}"
cd $DEPLOY_DIR/db_service
docker compose down

if [ -f "$DEPLOY_DIR/docker-compose.scheduler.yml" ]; then
    cd $DEPLOY_DIR
    docker compose -f docker-compose.scheduler.yml down || true
fi

# Restore backup (excluding .git directory)
echo -e "${YELLOW}📦 Restoring files...${NC}"
rsync -a --delete --exclude='.git' $BACKUP_PATH/ $DEPLOY_DIR/

# Get commit hash and reset
if [ -f "$BACKUP_PATH/commit_hash.txt" ]; then
    COMMIT=$(cat "$BACKUP_PATH/commit_hash.txt")
    cd $DEPLOY_DIR
    git fetch origin
    git reset --hard $COMMIT
    echo -e "${GREEN}✅ Reset to commit: $COMMIT${NC}"
fi

# Restart services
echo -e "${YELLOW}🔄 Restarting services...${NC}"
cd $DEPLOY_DIR/db_service
docker compose up -d

if [ -f "$DEPLOY_DIR/docker-compose.scheduler.yml" ]; then
    cd $DEPLOY_DIR
    docker compose -f docker-compose.scheduler.yml up -d || true
fi

# Health check
echo -e "${YELLOW}🏥 Checking health...${NC}"
sleep 10
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Rollback successful!${NC}"
    echo -e "${GREEN}✅ Health check passed${NC}"
    
    echo ""
    echo -e "${GREEN}🌐 Service URLs:${NC}"
    echo -e "  Health: ${GREEN}https://legislatie.issuemonitoring.ro/health${NC}"
    echo -e "  Docs:   ${GREEN}https://legislatie.issuemonitoring.ro/docs${NC}"
else
    echo -e "${RED}❌ Rollback completed but health check failed!${NC}"
    echo -e "${YELLOW}Check logs: docker compose logs -f api${NC}"
fi

echo ""
echo -e "${GREEN}📊 Container status:${NC}"
cd $DEPLOY_DIR/db_service
docker compose ps
