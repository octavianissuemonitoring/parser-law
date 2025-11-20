-- Migration: Add Issues System with Tier 1 (direct) and Tier 2 (structure) support
-- Date: 2025-11-20
-- Description: 
--   - Creates junction tables for many-to-many relationships between documents and issues
--   - Adds structure_issues table for hierarchical issue assignment (Tier 2)
--   - Removes old articole.issue TEXT column (replaced by articole_issues junction)
--   - Adds indexes for performance

-- =============================================================================
-- TIER 1: Direct Issues (Articole, Acte, Anexe)
-- =============================================================================

-- Junction table: articole <-> issues (Tier 1)
CREATE TABLE IF NOT EXISTS legislatie.articole_issues (
    id SERIAL PRIMARY KEY,
    articol_id INTEGER NOT NULL REFERENCES legislatie.articole(id) ON DELETE CASCADE,
    issue_id INTEGER NOT NULL REFERENCES legislatie.issues(id) ON DELETE CASCADE,
    relevance_score NUMERIC(3,2) CHECK (relevance_score >= 0.00 AND relevance_score <= 1.00),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(articol_id, issue_id)
);

-- Junction table: acte_legislative <-> issues (Tier 1)
CREATE TABLE IF NOT EXISTS legislatie.acte_issues (
    id SERIAL PRIMARY KEY,
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    issue_id INTEGER NOT NULL REFERENCES legislatie.issues(id) ON DELETE CASCADE,
    relevance_score NUMERIC(3,2) CHECK (relevance_score >= 0.00 AND relevance_score <= 1.00),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(act_id, issue_id)
);

-- Junction table: anexe <-> issues (Tier 1)
CREATE TABLE IF NOT EXISTS legislatie.anexe_issues (
    id SERIAL PRIMARY KEY,
    anexa_id INTEGER NOT NULL REFERENCES legislatie.anexe(id) ON DELETE CASCADE,
    issue_id INTEGER NOT NULL REFERENCES legislatie.issues(id) ON DELETE CASCADE,
    relevance_score NUMERIC(3,2) CHECK (relevance_score >= 0.00 AND relevance_score <= 1.00),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(anexa_id, issue_id)
);

-- =============================================================================
-- TIER 2: Structure Issues (Titluri, Capitole, Sectiuni)
-- =============================================================================

-- Junction table: structural elements <-> issues (Tier 2)
-- Uses existing text fields from articole table (titlu_nr, capitol_nr, sectiune_nr)
-- to identify structural elements without creating separate structure tables
CREATE TABLE IF NOT EXISTS legislatie.structure_issues (
    id SERIAL PRIMARY KEY,
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    structure_type VARCHAR(20) NOT NULL CHECK (structure_type IN ('titlu', 'capitol', 'sectiune')),
    
    -- Structural identifiers (match existing articole columns)
    titlu_nr VARCHAR(50),           -- Used when structure_type='titlu'
    titlu_denumire TEXT,            -- Optional: full title name
    capitol_nr VARCHAR(50),         -- Used when structure_type='capitol'
    capitol_denumire TEXT,          -- Optional: full chapter name
    sectiune_nr VARCHAR(50),        -- Used when structure_type='sectiune'
    sectiune_denumire TEXT,         -- Optional: full section name
    
    issue_id INTEGER NOT NULL REFERENCES legislatie.issues(id) ON DELETE CASCADE,
    relevance_score NUMERIC(3,2) CHECK (relevance_score >= 0.00 AND relevance_score <= 1.00),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Composite unique constraint based on structure type
    CONSTRAINT unique_structure_issue UNIQUE (act_id, structure_type, titlu_nr, capitol_nr, sectiune_nr, issue_id)
);

-- =============================================================================
-- INDEXES for Performance
-- =============================================================================

-- Tier 1 indexes
CREATE INDEX IF NOT EXISTS idx_articole_issues_articol ON legislatie.articole_issues(articol_id);
CREATE INDEX IF NOT EXISTS idx_articole_issues_issue ON legislatie.articole_issues(issue_id);
CREATE INDEX IF NOT EXISTS idx_articole_issues_score ON legislatie.articole_issues(relevance_score DESC);

CREATE INDEX IF NOT EXISTS idx_acte_issues_act ON legislatie.acte_issues(act_id);
CREATE INDEX IF NOT EXISTS idx_acte_issues_issue ON legislatie.acte_issues(issue_id);
CREATE INDEX IF NOT EXISTS idx_acte_issues_score ON legislatie.acte_issues(relevance_score DESC);

CREATE INDEX IF NOT EXISTS idx_anexe_issues_anexa ON legislatie.anexe_issues(anexa_id);
CREATE INDEX IF NOT EXISTS idx_anexe_issues_issue ON legislatie.anexe_issues(issue_id);
CREATE INDEX IF NOT EXISTS idx_anexe_issues_score ON legislatie.anexe_issues(relevance_score DESC);

-- Tier 2 indexes
CREATE INDEX IF NOT EXISTS idx_structure_issues_act ON legislatie.structure_issues(act_id);
CREATE INDEX IF NOT EXISTS idx_structure_issues_type ON legislatie.structure_issues(structure_type);
CREATE INDEX IF NOT EXISTS idx_structure_issues_issue ON legislatie.structure_issues(issue_id);
CREATE INDEX IF NOT EXISTS idx_structure_issues_score ON legislatie.structure_issues(relevance_score DESC);

-- Composite indexes for structure lookups
CREATE INDEX IF NOT EXISTS idx_structure_issues_titlu ON legislatie.structure_issues(act_id, structure_type, titlu_nr) 
    WHERE structure_type = 'titlu';
CREATE INDEX IF NOT EXISTS idx_structure_issues_capitol ON legislatie.structure_issues(act_id, structure_type, capitol_nr) 
    WHERE structure_type = 'capitol';
CREATE INDEX IF NOT EXISTS idx_structure_issues_sectiune ON legislatie.structure_issues(act_id, structure_type, sectiune_nr) 
    WHERE structure_type = 'sectiune';

-- =============================================================================
-- DATA MIGRATION: Move existing articole.issue to articole_issues
-- =============================================================================

-- Optional: Migrate existing issue data before dropping column
-- This assumes articole.issue contains a single issue name
-- If you want to preserve this data, uncomment the following:

/*
DO $$
DECLARE
    article_record RECORD;
    issue_record RECORD;
BEGIN
    -- Loop through articles with non-null issue field
    FOR article_record IN 
        SELECT id, issue, explicatie 
        FROM legislatie.articole 
        WHERE issue IS NOT NULL AND issue != ''
    LOOP
        -- Find or create issue
        SELECT id INTO issue_record 
        FROM legislatie.issues 
        WHERE LOWER(denumire) = LOWER(article_record.issue)
        LIMIT 1;
        
        -- If issue doesn't exist, create it
        IF NOT FOUND THEN
            INSERT INTO legislatie.issues (denumire, descriere, source, confidence_score)
            VALUES (
                article_record.issue,
                COALESCE(article_record.explicatie, 'Migrated from old articole.issue field'),
                'migration',
                0.50  -- Default confidence for migrated data
            )
            RETURNING id INTO issue_record;
        END IF;
        
        -- Link article to issue (ignore if already exists)
        INSERT INTO legislatie.articole_issues (articol_id, issue_id, relevance_score)
        VALUES (article_record.id, issue_record.id, 0.80)  -- Default relevance for migrated data
        ON CONFLICT (articol_id, issue_id) DO NOTHING;
        
    END LOOP;
    
    RAISE NOTICE 'Migration completed: articole.issue -> articole_issues';
END $$;
*/

-- =============================================================================
-- SCHEMA CLEANUP: Remove old issue column from articole
-- =============================================================================

-- Drop the old TEXT issue column (replaced by articole_issues junction table)
-- WARNING: This is destructive! Make sure to run migration block above first if needed
ALTER TABLE legislatie.articole DROP COLUMN IF EXISTS issue;

-- =============================================================================
-- COMMENTS for Documentation
-- =============================================================================

COMMENT ON TABLE legislatie.articole_issues IS 'Tier 1: Many-to-many relationship between articles and issues. Direct assignment at article level.';
COMMENT ON TABLE legislatie.acte_issues IS 'Tier 1: Many-to-many relationship between legislative acts and issues. Act-level themes.';
COMMENT ON TABLE legislatie.anexe_issues IS 'Tier 1: Many-to-many relationship between annexes and issues. Annex-specific topics.';
COMMENT ON TABLE legislatie.structure_issues IS 'Tier 2: Issues assigned to structural elements (title/chapter/section). Inherited by child articles in UI tree view.';

COMMENT ON COLUMN legislatie.structure_issues.structure_type IS 'Type of structural element: titlu (title), capitol (chapter), or sectiune (section)';
COMMENT ON COLUMN legislatie.structure_issues.titlu_nr IS 'Title number identifier (e.g., "I", "II", "III-A"). Used when structure_type=titlu';
COMMENT ON COLUMN legislatie.structure_issues.capitol_nr IS 'Chapter number identifier (e.g., "1", "2", "3bis"). Used when structure_type=capitol';
COMMENT ON COLUMN legislatie.structure_issues.sectiune_nr IS 'Section number identifier (e.g., "1", "2", "A"). Used when structure_type=sectiune';
COMMENT ON COLUMN legislatie.articole_issues.relevance_score IS 'AI-assigned relevance score (0.00-1.00) indicating how relevant the issue is to this specific article';
COMMENT ON COLUMN legislatie.structure_issues.relevance_score IS 'AI-assigned relevance score (0.00-1.00) indicating how relevant the issue is to this structural element and its children';

-- =============================================================================
-- VERIFICATION QUERIES (Run these after migration to verify success)
-- =============================================================================

-- Check table creation
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'legislatie' AND table_name LIKE '%issues%';

-- Check indexes
-- SELECT indexname, tablename FROM pg_indexes WHERE schemaname = 'legislatie' AND tablename LIKE '%issues%';

-- Count migrated data (if migration was run)
-- SELECT COUNT(*) as migrated_issues FROM legislatie.articole_issues WHERE added_at > NOW() - INTERVAL '5 minutes';

-- Verify articole.issue column dropped
-- SELECT column_name FROM information_schema.columns WHERE table_schema = 'legislatie' AND table_name = 'articole' AND column_name = 'issue';
