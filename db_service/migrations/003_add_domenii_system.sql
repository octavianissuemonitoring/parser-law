-- Migration: Add Domenii (Domain/Category) System
-- Date: 2025-11-20
-- Description:
--   - Creates domenii (domains) table for categorizing legislative acts
--   - Links acts to domains (many-to-many via acte_domenii)
--   - Links articles to domains (many-to-many via articole_domenii) - OPTIONAL override
--   - Makes domeniu_id MANDATORY in all issues junction tables
--   - Issues are always contextualized within a specific domain

-- =============================================================================
-- DOMENII: Categories for Legislative Acts
-- =============================================================================

CREATE TABLE IF NOT EXISTS legislatie.domenii (
    id SERIAL PRIMARY KEY,
    cod VARCHAR(50) UNIQUE NOT NULL,        -- ex: "FARMA", "TUTUN", "DISP_MED"
    denumire VARCHAR(255) NOT NULL,         -- ex: "Produse Farmaceutice"
    descriere TEXT,                         -- detailed description
    culoare VARCHAR(7),                     -- hex color for UI: "#3B82F6"
    ordine INTEGER DEFAULT 0,               -- display order in dropdowns
    activ BOOLEAN DEFAULT true,             -- soft delete flag
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create index for active domains sorted by ordine
CREATE INDEX IF NOT EXISTS idx_domenii_activ_ordine ON legislatie.domenii(activ, ordine) WHERE activ = true;
CREATE INDEX IF NOT EXISTS idx_domenii_cod ON legislatie.domenii(cod);

-- =============================================================================
-- ACTE <-> DOMENII: Many-to-Many (Act Level Assignment)
-- =============================================================================

CREATE TABLE IF NOT EXISTS legislatie.acte_domenii (
    id SERIAL PRIMARY KEY,
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    domeniu_id INTEGER NOT NULL REFERENCES legislatie.domenii(id) ON DELETE CASCADE,
    relevanta NUMERIC(3,2) CHECK (relevanta >= 0.00 AND relevanta <= 1.00),  -- optional: relevance score
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    added_by VARCHAR(100),              -- user who assigned (optional)
    UNIQUE(act_id, domeniu_id)
);

CREATE INDEX IF NOT EXISTS idx_acte_domenii_act ON legislatie.acte_domenii(act_id);
CREATE INDEX IF NOT EXISTS idx_acte_domenii_domeniu ON legislatie.acte_domenii(domeniu_id);

-- =============================================================================
-- ARTICOLE <-> DOMENII: Many-to-Many (Article Level Override - OPTIONAL)
-- =============================================================================

CREATE TABLE IF NOT EXISTS legislatie.articole_domenii (
    id SERIAL PRIMARY KEY,
    articol_id INTEGER NOT NULL REFERENCES legislatie.articole(id) ON DELETE CASCADE,
    domeniu_id INTEGER NOT NULL REFERENCES legislatie.domenii(id) ON DELETE CASCADE,
    relevanta NUMERIC(3,2) CHECK (relevanta >= 0.00 AND relevanta <= 1.00),
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    added_by VARCHAR(100),
    UNIQUE(articol_id, domeniu_id)
);

CREATE INDEX IF NOT EXISTS idx_articole_domenii_articol ON legislatie.articole_domenii(articol_id);
CREATE INDEX IF NOT EXISTS idx_articole_domenii_domeniu ON legislatie.articole_domenii(domeniu_id);

-- =============================================================================
-- UPDATE ISSUES TABLES: Add MANDATORY domeniu_id
-- =============================================================================

-- Tier 1: Articole Issues with Domain Context
ALTER TABLE legislatie.articole_issues 
ADD COLUMN IF NOT EXISTS domeniu_id INTEGER NOT NULL REFERENCES legislatie.domenii(id) ON DELETE CASCADE;

-- Drop old unique constraint and create new one including domeniu_id
ALTER TABLE legislatie.articole_issues DROP CONSTRAINT IF EXISTS articole_issues_articol_id_issue_id_key;
ALTER TABLE legislatie.articole_issues ADD CONSTRAINT unique_articol_issue_domeniu 
    UNIQUE(articol_id, issue_id, domeniu_id);

CREATE INDEX IF NOT EXISTS idx_articole_issues_domeniu ON legislatie.articole_issues(domeniu_id);

-- Tier 1: Acte Issues with Domain Context
ALTER TABLE legislatie.acte_issues
ADD COLUMN IF NOT EXISTS domeniu_id INTEGER NOT NULL REFERENCES legislatie.domenii(id) ON DELETE CASCADE;

ALTER TABLE legislatie.acte_issues DROP CONSTRAINT IF EXISTS acte_issues_act_id_issue_id_key;
ALTER TABLE legislatie.acte_issues ADD CONSTRAINT unique_act_issue_domeniu
    UNIQUE(act_id, issue_id, domeniu_id);

CREATE INDEX IF NOT EXISTS idx_acte_issues_domeniu ON legislatie.acte_issues(domeniu_id);

-- Tier 1: Anexe Issues with Domain Context
ALTER TABLE legislatie.anexe_issues
ADD COLUMN IF NOT EXISTS domeniu_id INTEGER NOT NULL REFERENCES legislatie.domenii(id) ON DELETE CASCADE;

ALTER TABLE legislatie.anexe_issues DROP CONSTRAINT IF EXISTS anexe_issues_anexa_id_issue_id_key;
ALTER TABLE legislatie.anexe_issues ADD CONSTRAINT unique_anexa_issue_domeniu
    UNIQUE(anexa_id, issue_id, domeniu_id);

CREATE INDEX IF NOT EXISTS idx_anexe_issues_domeniu ON legislatie.anexe_issues(domeniu_id);

-- Tier 2: Structure Issues with Domain Context
ALTER TABLE legislatie.structure_issues
ADD COLUMN IF NOT EXISTS domeniu_id INTEGER NOT NULL REFERENCES legislatie.domenii(id) ON DELETE CASCADE;

-- Drop old unique constraint and recreate with domeniu_id
ALTER TABLE legislatie.structure_issues DROP CONSTRAINT IF EXISTS unique_structure_issue;
ALTER TABLE legislatie.structure_issues ADD CONSTRAINT unique_structure_issue_domeniu
    UNIQUE(act_id, structure_type, titlu_nr, capitol_nr, sectiune_nr, issue_id, domeniu_id);

CREATE INDEX IF NOT EXISTS idx_structure_issues_domeniu ON legislatie.structure_issues(domeniu_id);

-- =============================================================================
-- SEED DATA: Common Domains (Examples)
-- =============================================================================

INSERT INTO legislatie.domenii (cod, denumire, descriere, culoare, ordine, activ) VALUES
    ('FARMA', 'Produse Farmaceutice', 'Legislație privind medicamentele și produsele farmaceutice', '#3B82F6', 10, true),
    ('DISP_MED', 'Dispozitive Medicale', 'Reglementări pentru dispozitive și echipamente medicale', '#10B981', 20, true),
    ('TUTUN', 'Produse din Tutun', 'Legislație antifumat și reglementări tutun', '#F59E0B', 30, true),
    ('PROT_CONS', 'Protecția Consumatorilor', 'Drepturi și protecție consumatori', '#8B5CF6', 40, true),
    ('SANATATE', 'Sănătate Publică', 'Legislație generală de sănătate publică', '#EF4444', 50, true),
    ('MEDIU', 'Protecția Mediului', 'Reglementări privind protecția mediului', '#14B8A6', 60, true)
ON CONFLICT (cod) DO NOTHING;

-- =============================================================================
-- HELPER FUNCTION: Get Effective Domains for Article
-- =============================================================================

-- Function to get effective domains for an article (with inheritance from act)
-- If article has specific domains assigned, return those; otherwise inherit from act
CREATE OR REPLACE FUNCTION legislatie.get_articol_domenii(p_articol_id INTEGER)
RETURNS TABLE (
    domeniu_id INTEGER,
    cod VARCHAR(50),
    denumire VARCHAR(255),
    source VARCHAR(10)  -- 'articol' or 'act' (inherited)
) AS $$
BEGIN
    -- Check if article has specific domain assignments
    IF EXISTS (SELECT 1 FROM legislatie.articole_domenii WHERE articol_id = p_articol_id) THEN
        -- Return article-specific domains
        RETURN QUERY
        SELECT 
            d.id as domeniu_id,
            d.cod,
            d.denumire,
            'articol'::VARCHAR(10) as source
        FROM legislatie.articole_domenii ad
        JOIN legislatie.domenii d ON ad.domeniu_id = d.id
        WHERE ad.articol_id = p_articol_id AND d.activ = true;
    ELSE
        -- Inherit domains from parent act
        RETURN QUERY
        SELECT 
            d.id as domeniu_id,
            d.cod,
            d.denumire,
            'act'::VARCHAR(10) as source
        FROM legislatie.articole a
        JOIN legislatie.acte_domenii ad ON a.act_id = ad.act_id
        JOIN legislatie.domenii d ON ad.domeniu_id = d.id
        WHERE a.id = p_articol_id AND d.activ = true;
    END IF;
END;
$$ LANGUAGE plpgsql STABLE;

-- =============================================================================
-- COMMENTS for Documentation
-- =============================================================================

COMMENT ON TABLE legislatie.domenii IS 'Domains/Categories for organizing legislative acts by subject matter (e.g., Pharma, Medical Devices, Tobacco)';
COMMENT ON TABLE legislatie.acte_domenii IS 'Many-to-many: Legislative acts to domains. Assigned when scraping/importing acts.';
COMMENT ON TABLE legislatie.articole_domenii IS 'Many-to-many: Articles to domains. OPTIONAL override - if set, article uses these instead of inheriting from act.';
COMMENT ON COLUMN legislatie.domenii.cod IS 'Unique code identifier for domain (e.g., FARMA, TUTUN). Used in APIs and code.';
COMMENT ON COLUMN legislatie.domenii.culoare IS 'Hex color code for UI visualization (e.g., #3B82F6 for blue)';
COMMENT ON COLUMN legislatie.domenii.ordine IS 'Display order in dropdowns/lists (lower = displayed first)';
COMMENT ON COLUMN legislatie.articole_issues.domeniu_id IS 'MANDATORY: Issue context is always within a specific domain. Same article can have different issues per domain.';
COMMENT ON FUNCTION legislatie.get_articol_domenii(INTEGER) IS 'Helper function: Returns effective domains for an article (article-specific if assigned, otherwise inherited from act)';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Check tables created
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'legislatie' AND table_name LIKE '%domeni%';

-- Check seed data
-- SELECT * FROM legislatie.domenii ORDER BY ordine;

-- Test inheritance function (replace 123 with real article ID)
-- SELECT * FROM legislatie.get_articol_domenii(123);

-- Check that all issues tables now have domeniu_id
-- SELECT column_name, data_type, is_nullable FROM information_schema.columns 
-- WHERE table_schema = 'legislatie' AND table_name LIKE '%issues' AND column_name = 'domeniu_id';
