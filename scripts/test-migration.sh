#!/bin/bash
# Test & Apply AI Processing Migration
# Usage: ./test-migration.sh (run from /opt/parser-law)

set -e  # Exit on error

# Source common configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common-config.sh"

# Ensure we're in the deployment directory
ensure_deploy_dir

MIGRATION_FILE="$DEPLOY_DIR/db_service/migrations/add_ai_processing.sql"
CONTAINER_NAME="legislatie_postgres"

# Check if PostgreSQL is running in Docker
if docker ps | grep -q "$CONTAINER_NAME"; then
    DB_MODE="docker"
    log_info "PostgreSQL detected in Docker container: $CONTAINER_NAME"
elif command -v psql &> /dev/null; then
    DB_MODE="native"
    log_info "PostgreSQL detected as native installation"
else
    log_error "PostgreSQL not found (neither Docker nor native)"
    exit 1
fi

log_info "Step 1: Checking migration file exists..."
if [ ! -f "$MIGRATION_FILE" ]; then
    log_error "Migration file not found: $MIGRATION_FILE"
    exit 1
fi
log_success "Migration file found"

echo ""
log_info "Step 2: Creating backup before migration..."
BACKUP_FILE="backup_before_ai_migration_$(timestamp).sql"

if [ "$DB_MODE" = "docker" ]; then
    docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME > "/tmp/$BACKUP_FILE"
else
    sudo -u postgres pg_dump $DB_NAME > "/tmp/$BACKUP_FILE"
fi

log_success "Backup created: /tmp/$BACKUP_FILE"

log_info "Step 3: Testing migration (dry-run with transaction)..."

if [ "$DB_MODE" = "docker" ]; then
    # Copy migration file to container
    docker cp $MIGRATION_FILE $CONTAINER_NAME:/tmp/migration.sql
    
    # Test with rollback
    docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME << EOF
BEGIN;
\i /tmp/migration.sql
ROLLBACK;
EOF
else
    sudo -u postgres psql -d $DB_NAME -U $DB_USER << EOF
BEGIN;
\i $MIGRATION_FILE
ROLLBACK;
EOF
fi

if [ $? -eq 0 ]; then
    log_success "Migration syntax is valid!"
else
    log_error "Migration has syntax errors. Fix before applying."
    exit 1
fi

log_info "Step 4: Applying migration for real..."
read -p "Do you want to apply the migration? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    log_warning "Migration cancelled by user"
    exit 0
fi

if [ "$DB_MODE" = "docker" ]; then
    docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -f /tmp/migration.sql
else
    sudo -u postgres psql -d $DB_NAME -U $DB_USER -f $MIGRATION_FILE
fi

if [ $? -eq 0 ]; then
    echo ""
    log_success "Migration applied successfully!"
    echo ""
    log_info "Verification:"
    
    if [ "$DB_MODE" = "docker" ]; then
        docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '$DB_SCHEMA' 
            AND table_name IN ('issues', 'anexe', 'acte_issues', 'articole_issues', 'anexe_issues')
            ORDER BY table_name;
        "
        
        echo ""
        log_info "New columns in acte_legislative:"
        docker exec $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME -c "
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = '$DB_SCHEMA' 
            AND table_name = 'acte_legislative'
            AND column_name IN ('ai_status', 'metadate', 'export_status', 'issue_monitoring_id')
            ORDER BY column_name;
        "
    else
        sudo -u postgres psql -d $DB_NAME -U $DB_USER -c "
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '$DB_SCHEMA' 
            AND table_name IN ('issues', 'anexe', 'acte_issues', 'articole_issues', 'anexe_issues')
            ORDER BY table_name;
        "
        
        echo ""
        log_info "New columns in acte_legislative:"
        sudo -u postgres psql -d $DB_NAME -U $DB_USER -c "
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = '$DB_SCHEMA' 
            AND table_name = 'acte_legislative'
            AND column_name IN ('ai_status', 'metadate', 'export_status', 'issue_monitoring_id')
            ORDER BY column_name;
        "
    fi
    
    echo ""
    log_success "Migration complete! Backup saved at: /tmp/$BACKUP_FILE"
else
    log_error "Migration failed! Restoring from backup..."
    
    if [ "$DB_MODE" = "docker" ]; then
        docker exec -i $CONTAINER_NAME psql -U $DB_USER -d $DB_NAME < "/tmp/$BACKUP_FILE"
    else
        sudo -u postgres psql -d $DB_NAME < "/tmp/$BACKUP_FILE"
    fi
    
    log_success "Database restored from backup"
    exit 1
fi
