-- Migration 004: Add AI processing columns to acte_legislative and articole
-- Purpose: Add ai_status, ai_processed_at, ai_error columns for AI workflow tracking

-- Add AI columns to acte_legislative table
ALTER TABLE legislatie.acte_legislative
    ADD COLUMN IF NOT EXISTS ai_status VARCHAR(20) DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS ai_processed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS ai_error TEXT,
    ADD COLUMN IF NOT EXISTS metadate JSONB,
    ADD COLUMN IF NOT EXISTS export_status VARCHAR(20),
    ADD COLUMN IF NOT EXISTS export_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS export_error TEXT,
    ADD COLUMN IF NOT EXISTS issue_monitoring_id INTEGER;

-- Add index for ai_status filtering
CREATE INDEX IF NOT EXISTS ix_acte_ai_status ON legislatie.acte_legislative(ai_status);

-- Add AI columns to articole table (if not exist)
ALTER TABLE legislatie.articole
    ADD COLUMN IF NOT EXISTS ai_status VARCHAR(20) DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS ai_processed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS ai_error TEXT,
    ADD COLUMN IF NOT EXISTS metadate JSONB,
    ADD COLUMN IF NOT EXISTS issue_monitoring_id INTEGER;

-- Add index for ai_status filtering on articole
CREATE INDEX IF NOT EXISTS ix_articole_ai_status ON legislatie.articole(ai_status);

-- Add comment
COMMENT ON COLUMN legislatie.acte_legislative.ai_status IS 'AI processing status: pending, processing, processed, error, needs_reprocessing';
COMMENT ON COLUMN legislatie.articole.ai_status IS 'AI processing status: pending, processing, processed, error, needs_reprocessing';

-- Verify
SELECT 
    'acte_legislative' as table_name,
    COUNT(*) FILTER (WHERE ai_status = 'pending') as pending_count,
    COUNT(*) as total_count
FROM legislatie.acte_legislative

UNION ALL

SELECT 
    'articole' as table_name,
    COUNT(*) FILTER (WHERE ai_status = 'pending') as pending_count,
    COUNT(*) as total_count
FROM legislatie.articole;
