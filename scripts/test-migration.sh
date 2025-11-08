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

log_info "Step 1: Checking migration file exists..."
if [ ! -f "$MIGRATION_FILE" ]; then
    log_error "Migration file not found: $MIGRATION_FILE"
    exit 1
fi
log_success "Migration file found"

echo ""
log_info "Step 2: Creating backup before migration..."
BACKUP_FILE="backup_before_ai_migration_$(timestamp).sql"
sudo -u postgres pg_dump $DB_NAME > "/tmp/$BACKUP_FILE"
log_success "Backup created: /tmp/$BACKUP_FILE"

log_info "Step 3: Testing migration (dry-run with transaction)..."
sudo -u postgres psql -d $DB_NAME -U $DB_USER << EOF
BEGIN;
\i $MIGRATION_FILE
ROLLBACK;
EOF

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

sudo -u postgres psql -d $DB_NAME -U $DB_USER -f $MIGRATION_FILE

if [ $? -eq 0 ]; then
    echo ""
    log_success "Migration applied successfully!"
    echo ""
    log_info "Verification:"
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
    
    echo ""
    log_success "Migration complete! Backup saved at: /tmp/$BACKUP_FILE"
else
    log_error "Migration failed! Restoring from backup..."
    sudo -u postgres psql -d $DB_NAME < "/tmp/$BACKUP_FILE"
    log_success "Database restored from backup"
    exit 1
fi
