#!/bin/bash
# Test & Apply AI Processing Migration
# Usage: ./test-migration.sh

set -e  # Exit on error

DB_NAME="legislatie_db"
DB_USER="legislatie_user"
MIGRATION_FILE="db_service/migrations/add_ai_processing.sql"

echo "🔍 Step 1: Checking migration file exists..."
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ Migration file not found: $MIGRATION_FILE"
    exit 1
fi
echo "✅ Migration file found"

echo ""
echo "🔍 Step 2: Creating backup before migration..."
BACKUP_FILE="backup_before_ai_migration_$(date +%Y%m%d_%H%M%S).sql"
sudo -u postgres pg_dump $DB_NAME > "/tmp/$BACKUP_FILE"
echo "✅ Backup created: /tmp/$BACKUP_FILE"

echo ""
echo "🔍 Step 3: Testing migration (dry-run with transaction)..."
sudo -u postgres psql -d $DB_NAME -U $DB_USER << EOF
BEGIN;
\i $MIGRATION_FILE
ROLLBACK;
EOF

if [ $? -eq 0 ]; then
    echo "✅ Migration syntax is valid!"
else
    echo "❌ Migration has syntax errors. Fix before applying."
    exit 1
fi

echo ""
echo "🔍 Step 4: Applying migration for real..."
read -p "Do you want to apply the migration? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Migration cancelled by user"
    exit 0
fi

sudo -u postgres psql -d $DB_NAME -U $DB_USER -f $MIGRATION_FILE

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Migration applied successfully!"
    echo ""
    echo "📊 Verification:"
    sudo -u postgres psql -d $DB_NAME -U $DB_USER -c "
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'legislatie' 
        AND table_name IN ('issues', 'anexe', 'acte_issues', 'articole_issues', 'anexe_issues')
        ORDER BY table_name;
    "
    
    echo ""
    echo "📋 New columns in acte_legislative:"
    sudo -u postgres psql -d $DB_NAME -U $DB_USER -c "
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'legislatie' 
        AND table_name = 'acte_legislative'
        AND column_name IN ('ai_status', 'metadate', 'export_status', 'issue_monitoring_id')
        ORDER BY column_name;
    "
    
    echo ""
    echo "🎉 Migration complete! Backup saved at: /tmp/$BACKUP_FILE"
else
    echo "❌ Migration failed! Restoring from backup..."
    sudo -u postgres psql -d $DB_NAME < "/tmp/$BACKUP_FILE"
    echo "✅ Database restored from backup"
    exit 1
fi
