-- Migration: Add Issues Cache & Sync Support for Issue Monitoring
-- Date: 2025-11-08
-- Purpose: Parser-Law acts as producer - sends new legislation to Issue Monitoring
--          and caches received tags (issues + metadate) locally

BEGIN;

-- 1. Add sync status tracking to acte_legislative
ALTER TABLE legislatie.acte_legislative 
ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'pending' 
    CHECK (sync_status IN ('pending', 'sent', 'tagged', 'synced', 'error')),
ADD COLUMN IF NOT EXISTS sync_sent_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS sync_received_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS sync_error TEXT,
ADD COLUMN IF NOT EXISTS metadate TEXT;

CREATE INDEX IF NOT EXISTS idx_acte_sync_status ON legislatie.acte_legislative(sync_status, sync_sent_at);

COMMENT ON COLUMN legislatie.acte_legislative.sync_status IS 
    'Status sincronizare: pending=nou, sent=trimis, tagged=etichetat, synced=sincronizat, error=eroare';
COMMENT ON COLUMN legislatie.acte_legislative.metadate IS 
    'Metadate/sumarizare primită de la Issue Monitoring';

-- 2. Add sync tracking to articole
ALTER TABLE legislatie.articole
ADD COLUMN IF NOT EXISTS sync_status VARCHAR(20) DEFAULT 'pending'
    CHECK (sync_status IN ('pending', 'sent', 'tagged', 'synced', 'error')),
ADD COLUMN IF NOT EXISTS sync_sent_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS sync_received_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS sync_error TEXT,
ADD COLUMN IF NOT EXISTS metadate TEXT;

CREATE INDEX IF NOT EXISTS idx_articole_sync_status ON legislatie.articole(sync_status, sync_sent_at);

COMMENT ON COLUMN legislatie.articole.metadate IS 
    'Metadate/explicație primită de la Issue Monitoring (ex-explicatie)';

-- Migrate existing explicatie to metadate
UPDATE legislatie.articole 
SET metadate = explicatie 
WHERE explicatie IS NOT NULL AND metadate IS NULL;

-- 3. Create Issues Cache table (local copy of Issue Monitoring issues)
CREATE TABLE IF NOT EXISTS legislatie.issues_cache (
    id SERIAL PRIMARY KEY,
    issue_monitoring_id INTEGER,  -- ID din Issue Monitoring
    denumire VARCHAR(256) NOT NULL,
    descriere TEXT,
    data_creare TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_actualizare TIMESTAMP,
    
    CONSTRAINT check_denumire_not_empty CHECK (LENGTH(TRIM(denumire)) > 0),
    CONSTRAINT unique_issue_monitoring_id UNIQUE (issue_monitoring_id)
);

CREATE INDEX idx_issues_cache_im_id ON legislatie.issues_cache(issue_monitoring_id);
CREATE INDEX idx_issues_cache_data ON legislatie.issues_cache(data_actualizare DESC);

COMMENT ON TABLE legislatie.issues_cache IS 'Cache local pentru issues primite de la Issue Monitoring';
COMMENT ON COLUMN legislatie.issues_cache.issue_monitoring_id IS 'ID-ul issue-ului în BD Issue Monitoring';

-- 4. Create Anexe table (separate from articles)
CREATE TABLE IF NOT EXISTS legislatie.anexe (
    id SERIAL PRIMARY KEY,
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    anexa_nr VARCHAR(50),
    ordine INTEGER NOT NULL,
    titlu TEXT,
    continut TEXT NOT NULL,
    metadate TEXT,
    sync_status VARCHAR(20) DEFAULT 'pending'
        CHECK (sync_status IN ('pending', 'sent', 'tagged', 'synced', 'error')),
    sync_sent_at TIMESTAMP,
    sync_received_at TIMESTAMP,
    sync_error TEXT,
    data_creare TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_modificare TIMESTAMP,
    
    CONSTRAINT check_continut_not_empty CHECK (LENGTH(TRIM(continut)) > 0),
    CONSTRAINT unique_anexa_per_act UNIQUE (act_id, ordine)
);

CREATE INDEX idx_anexe_act_id ON legislatie.anexe(act_id);
CREATE INDEX idx_anexe_ordine ON legislatie.anexe(act_id, ordine);
CREATE INDEX idx_anexe_sync_status ON legislatie.anexe(sync_status, sync_sent_at);

COMMENT ON TABLE legislatie.anexe IS 'Anexe separate ale actelor legislative';
COMMENT ON COLUMN legislatie.anexe.ordine IS 'Ordinea anexei în document (pentru sortare)';
COMMENT ON COLUMN legislatie.anexe.metadate IS 'Sumarizare/explicație anexă primită de la Issue Monitoring';

-- 5. Junction table: acte_legislative ↔ issues_cache
CREATE TABLE IF NOT EXISTS legislatie.acte_issues (
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    issue_cache_id INTEGER NOT NULL REFERENCES legislatie.issues_cache(id) ON DELETE CASCADE,
    data_adaugare TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (act_id, issue_cache_id)
);

CREATE INDEX idx_acte_issues_act ON legislatie.acte_issues(act_id);
CREATE INDEX idx_acte_issues_issue ON legislatie.acte_issues(issue_cache_id);

COMMENT ON TABLE legislatie.acte_issues IS 'Relație many-to-many: acte ↔ issues (cache local)';

-- 6. Junction table: articole ↔ issues_cache
CREATE TABLE IF NOT EXISTS legislatie.articole_issues (
    articol_id INTEGER NOT NULL REFERENCES legislatie.articole(id) ON DELETE CASCADE,
    issue_cache_id INTEGER NOT NULL REFERENCES legislatie.issues_cache(id) ON DELETE CASCADE,
    data_adaugare TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (articol_id, issue_cache_id)
);

CREATE INDEX idx_articole_issues_articol ON legislatie.articole_issues(articol_id);
CREATE INDEX idx_articole_issues_issue ON legislatie.articole_issues(issue_cache_id);

COMMENT ON TABLE legislatie.articole_issues IS 'Relație many-to-many: articole ↔ issues (cache local)';

-- 7. Junction table: anexe ↔ issues
CREATE TABLE IF NOT EXISTS legislatie.anexe_issues (
    anexa_id INTEGER NOT NULL REFERENCES legislatie.anexe(id) ON DELETE CASCADE,
    issue_id INTEGER NOT NULL REFERENCES legislatie.issues(id) ON DELETE CASCADE,
    data_adaugare TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    adaugat_de VARCHAR(100),
    
    PRIMARY KEY (anexa_id, issue_id)
);

CREATE INDEX idx_anexe_issues_anexa ON legislatie.anexe_issues(anexa_id);
CREATE INDEX idx_anexe_issues_issue ON legislatie.anexe_issues(issue_id);

COMMENT ON TABLE legislatie.anexe_issues IS 'Relație many-to-many: anexe ↔ issues';

-- 8. Create views for easy querying
CREATE OR REPLACE VIEW legislatie.v_articole_cu_issues AS
SELECT 
    a.*,
    COALESCE(
        json_agg(
            json_build_object(
                'issue_id', i.id,
                'denumire', i.denumire,
                'descriere', i.descriere
            ) ORDER BY i.denumire
        ) FILTER (WHERE i.id IS NOT NULL),
        '[]'::json
    ) AS issues
FROM legislatie.articole a
LEFT JOIN legislatie.articole_issues ai ON a.id = ai.articol_id
LEFT JOIN legislatie.issues i ON ai.issue_id = i.id
GROUP BY a.id;

COMMENT ON VIEW legislatie.v_articole_cu_issues IS 'Articole cu issues asociate (JSON)';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON legislatie.issues TO legislatie_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON legislatie.anexe TO legislatie_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON legislatie.acte_issues TO legislatie_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON legislatie.articole_issues TO legislatie_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON legislatie.anexe_issues TO legislatie_user;
GRANT SELECT ON legislatie.v_articole_cu_issues TO legislatie_user;

GRANT USAGE, SELECT ON SEQUENCE legislatie.issues_id_seq TO legislatie_user;
GRANT USAGE, SELECT ON SEQUENCE legislatie.anexe_id_seq TO legislatie_user;

COMMIT;

-- Summary of changes
SELECT 
    'Migration completed successfully!' AS status,
    COUNT(*) FILTER (WHERE table_name = 'issues') AS issues_table,
    COUNT(*) FILTER (WHERE table_name = 'anexe') AS anexe_table,
    COUNT(*) FILTER (WHERE table_name LIKE '%_issues') AS junction_tables
FROM information_schema.tables
WHERE table_schema = 'legislatie';
