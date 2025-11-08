#!/bin/bash
# Common configuration for all parser-law scripts
# Source this file in other scripts: source "$(dirname "$0")/common-config.sh"

# Standard deployment paths
export DEPLOY_DIR="/opt/parser-law"
export BACKUP_DIR="/opt/parser-law-backups"
export LOG_DIR="/var/log/parser-law"

# Database configuration
export DB_NAME="legislatie_db"
export DB_USER="legislatie_user"
export DB_SCHEMA="legislatie"

# GitHub repository
export GIT_REPO="https://github.com/octavianissuemonitoring/parser-law.git"
export GIT_BRANCH="master"

# Docker compose files
export COMPOSE_DB_SERVICE="$DEPLOY_DIR/db_service/docker-compose.yml"
export COMPOSE_SCHEDULER="$DEPLOY_DIR/docker-compose.scheduler.yml"

# Colors for output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Ensure we're in the correct directory
ensure_deploy_dir() {
    if [ ! -d "$DEPLOY_DIR" ]; then
        log_error "Deploy directory not found: $DEPLOY_DIR"
        exit 1
    fi
    cd "$DEPLOY_DIR"
}

# Check if script is run with proper permissions
check_permissions() {
    if [ "$EUID" -ne 0 ] && [ "$1" != "skip-root-check" ]; then
        log_warning "This script should be run as root or with sudo"
        read -p "Continue anyway? (yes/no): " CONFIRM
        if [ "$CONFIRM" != "yes" ]; then
            exit 1
        fi
    fi
}

# Timestamp for backups/logs
timestamp() {
    date +%Y%m%d_%H%M%S
}
