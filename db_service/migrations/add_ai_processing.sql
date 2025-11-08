-- Migration: Add AI Processing & Export Support
-- Date: 2025-11-08
-- Purpose: Parser-Law processes legislation through AI and exports to Issue Monitoring

BEGIN;

-- 1. Add AI processing status to acte_legislative
ALTER TABLE legislatie.acte_legislative 
ADD COLUMN IF NOT EXISTS ai_status VARCHAR(20) DEFAULT 'pending' 
    CHECK (ai_status IN ('pending', 'processing', 'completed', 'error')),
ADD COLUMN IF NOT EXISTS ai_processed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS ai_error TEXT,
ADD COLUMN IF NOT EXISTS metadate TEXT,
ADD COLUMN IF NOT EXISTS export_status VARCHAR(20) DEFAULT 'pending'
    CHECK (export_status IN ('pending', 'exported', 'error')),
ADD COLUMN IF NOT EXISTS export_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS export_error TEXT,
ADD COLUMN IF NOT EXISTS issue_monitoring_id INTEGER;  -- ID în BD Issue Monitoring

CREATE INDEX IF NOT EXISTS idx_acte_ai_status ON legislatie.acte_legislative(ai_status, ai_processed_at);
CREATE INDEX IF NOT EXISTS idx_acte_export_status ON legislatie.acte_legislative(export_status);
CREATE INDEX IF NOT EXISTS idx_acte_im_id ON legislatie.acte_legislative(issue_monitoring_id);

COMMENT ON COLUMN legislatie.acte_legislative.ai_status IS 
    'Status procesare AI: pending=nou, processing=în curs, completed=gata, error=eroare';
COMMENT ON COLUMN legislatie.acte_legislative.metadate IS 
    'Metadate/sumarizare generată de AI';
COMMENT ON COLUMN legislatie.acte_legislative.export_status IS
    'Status export către Issue Monitoring';
COMMENT ON COLUMN legislatie.acte_legislative.issue_monitoring_id IS
    'ID-ul actului în BD Issue Monitoring după export';

-- 2. Add AI processing to articole
ALTER TABLE legislatie.articole
ADD COLUMN IF NOT EXISTS ai_status VARCHAR(20) DEFAULT 'pending'
    CHECK (ai_status IN ('pending', 'processing', 'completed', 'error')),
ADD COLUMN IF NOT EXISTS ai_processed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS ai_error TEXT,
ADD COLUMN IF NOT EXISTS metadate TEXT,
ADD COLUMN IF NOT EXISTS issue_monitoring_id INTEGER;

CREATE INDEX IF NOT EXISTS idx_articole_ai_status ON legislatie.articole(ai_status, ai_processed_at);
CREATE INDEX IF NOT EXISTS idx_articole_im_id ON legislatie.articole(issue_monitoring_id);

COMMENT ON COLUMN legislatie.articole.metadate IS 
    'Metadate/explicație generată de AI (ex-explicatie)';
COMMENT ON COLUMN legislatie.articole.issue_monitoring_id IS
    'ID-ul articolului în BD Issue Monitoring după export';

-- Migrate existing explicatie to metadate
UPDATE legislatie.articole 
SET metadate = explicatie 
WHERE explicatie IS NOT NULL AND metadate IS NULL;

-- 3. Create Issues table (extracted by AI)
CREATE TABLE IF NOT EXISTS legislatie.issues (
    id SERIAL PRIMARY KEY,
    denumire VARCHAR(256) NOT NULL,
    descriere TEXT,
    source VARCHAR(20) DEFAULT 'ai' CHECK (source IN ('ai', 'manual')),
    confidence_score DECIMAL(3,2),  -- 0.00-1.00 (pentru AI-generated)
    issue_monitoring_id INTEGER,  -- ID în BD Issue Monitoring după export
    data_creare TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_modificare TIMESTAMP,
    
    CONSTRAINT check_denumire_not_empty CHECK (LENGTH(TRIM(denumire)) > 0)
);

CREATE INDEX idx_issues_data_creare ON legislatie.issues(data_creare DESC);
CREATE INDEX idx_issues_source ON legislatie.issues(source);
CREATE INDEX idx_issues_im_id ON legislatie.issues(issue_monitoring_id);

COMMENT ON TABLE legislatie.issues IS 'Issues extrase de AI sau adăugate manual';
COMMENT ON COLUMN legislatie.issues.source IS 'Sursa issue: ai=extras automat, manual=adăugat de user';
COMMENT ON COLUMN legislatie.issues.confidence_score IS 'Scor confidență AI (0-1)';
COMMENT ON COLUMN legislatie.issues.issue_monitoring_id IS 'ID în BD Issue Monitoring după export';

-- 4. Create Anexe table
CREATE TABLE IF NOT EXISTS legislatie.anexe (
    id SERIAL PRIMARY KEY,
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    anexa_nr VARCHAR(50),
    ordine INTEGER NOT NULL,
    titlu TEXT,
    continut TEXT NOT NULL,
    metadate TEXT,
    ai_status VARCHAR(20) DEFAULT 'pending'
        CHECK (ai_status IN ('pending', 'processing', 'completed', 'error')),
    ai_processed_at TIMESTAMP,
    ai_error TEXT,
    issue_monitoring_id INTEGER,
    data_creare TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_modificare TIMESTAMP,
    
    CONSTRAINT check_continut_not_empty CHECK (LENGTH(TRIM(continut)) > 0),
    CONSTRAINT unique_anexa_per_act UNIQUE (act_id, ordine)
);

CREATE INDEX idx_anexe_act_id ON legislatie.anexe(act_id);
CREATE INDEX idx_anexe_ordine ON legislatie.anexe(act_id, ordine);
CREATE INDEX idx_anexe_ai_status ON legislatie.anexe(ai_status, ai_processed_at);
CREATE INDEX idx_anexe_im_id ON legislatie.anexe(issue_monitoring_id);

COMMENT ON TABLE legislatie.anexe IS 'Anexe separate ale actelor legislative';
COMMENT ON COLUMN legislatie.anexe.metadate IS 'Sumarizare/explicație generată de AI';
COMMENT ON COLUMN legislatie.anexe.issue_monitoring_id IS 'ID în BD Issue Monitoring după export';

-- 5. Junction table: acte_legislative ↔ issues
CREATE TABLE IF NOT EXISTS legislatie.acte_issues (
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    issue_id INTEGER NOT NULL REFERENCES legislatie.issues(id) ON DELETE CASCADE,
    data_adaugare TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    adaugat_de VARCHAR(20) DEFAULT 'ai' CHECK (adaugat_de IN ('ai', 'manual')),
    
    PRIMARY KEY (act_id, issue_id)
);

CREATE INDEX idx_acte_issues_act ON legislatie.acte_issues(act_id);
CREATE INDEX idx_acte_issues_issue ON legislatie.acte_issues(issue_id);

COMMENT ON TABLE legislatie.acte_issues IS 'Relație many-to-many: acte ↔ issues';

-- 6. Junction table: articole ↔ issues
CREATE TABLE IF NOT EXISTS legislatie.articole_issues (
    articol_id INTEGER NOT NULL REFERENCES legislatie.articole(id) ON DELETE CASCADE,
    issue_id INTEGER NOT NULL REFERENCES legislatie.issues(id) ON DELETE CASCADE,
    data_adaugare TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    adaugat_de VARCHAR(20) DEFAULT 'ai' CHECK (adaugat_de IN ('ai', 'manual')),
    
    PRIMARY KEY (articol_id, issue_id)
);

CREATE INDEX idx_articole_issues_articol ON legislatie.articole_issues(articol_id);
CREATE INDEX idx_articole_issues_issue ON legislatie.articole_issues(issue_id);

COMMENT ON TABLE legislatie.articole_issues IS 'Relație many-to-many: articole ↔ issues';

-- 7. Junction table: anexe ↔ issues
CREATE TABLE IF NOT EXISTS legislatie.anexe_issues (
    anexa_id INTEGER NOT NULL REFERENCES legislatie.anexe(id) ON DELETE CASCADE,
    issue_id INTEGER NOT NULL REFERENCES legislatie.issues(id) ON DELETE CASCADE,
    data_adaugare TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    adaugat_de VARCHAR(20) DEFAULT 'ai' CHECK (adaugat_de IN ('ai', 'manual')),
    
    PRIMARY KEY (anexa_id, issue_id)
);

CREATE INDEX idx_anexe_issues_anexa ON legislatie.anexe_issues(anexa_id);
CREATE INDEX idx_anexe_issues_issue ON legislatie.anexe_issues(issue_id);

COMMENT ON TABLE legislatie.anexe_issues IS 'Relație many-to-many: anexe ↔ issues';

-- 8. View for pending AI processing
CREATE OR REPLACE VIEW legislatie.v_pending_ai_processing AS
SELECT 
    'act' AS tip,
    id,
    tip_act || ' ' || numar || '/' || data_an AS identificator,
    ai_status,
    ai_processed_at,
    ai_error
FROM legislatie.acte_legislative
WHERE ai_status IN ('pending', 'processing', 'error')

UNION ALL

SELECT 
    'articol' AS tip,
    a.id,
    'Art. ' || a.articol_nr || ' din ' || al.tip_act || ' ' || al.nr_act AS identificator,
    a.ai_status,
    a.ai_processed_at,
    a.ai_error
FROM legislatie.articole a
JOIN legislatie.acte_legislative al ON a.act_id = al.id
WHERE a.ai_status IN ('pending', 'processing', 'error')

UNION ALL

SELECT 
    'anexa' AS tip,
    an.id,
    'Anexa ' || COALESCE(an.anexa_nr, an.ordine::text) || ' din ' || al.tip_act || ' ' || al.nr_act AS identificator,
    an.ai_status,
    an.ai_processed_at,
    an.ai_error
FROM legislatie.anexe an
JOIN legislatie.acte_legislative al ON an.act_id = al.id
WHERE an.ai_status IN ('pending', 'processing', 'error')

ORDER BY ai_processed_at NULLS FIRST;

COMMENT ON VIEW legislatie.v_pending_ai_processing IS 
    'Elemente care așteaptă procesare AI';

-- 9. View for pending export to Issue Monitoring
CREATE OR REPLACE VIEW legislatie.v_pending_export AS
SELECT 
    al.id,
    al.tip_act,
    al.nr_act,
    al.an_act,
    al.titlu_act,
    al.metadate,
    al.ai_status,
    al.export_status,
    COUNT(DISTINCT a.id) AS nr_articole,
    COUNT(DISTINCT an.id) AS nr_anexe,
    COUNT(DISTINCT ai.issue_id) AS nr_issues
FROM legislatie.acte_legislative al
LEFT JOIN legislatie.articole a ON al.id = a.act_id
LEFT JOIN legislatie.anexe an ON al.id = an.act_id
LEFT JOIN legislatie.acte_issues ai ON al.id = ai.act_id
WHERE al.ai_status = 'completed' 
  AND al.export_status IN ('pending', 'error')
GROUP BY al.id, al.tip_act, al.nr_act, al.an_act, al.titlu_act, al.metadate, al.ai_status, al.export_status
ORDER BY al.data_creare DESC;

COMMENT ON VIEW legislatie.v_pending_export IS 
    'Acte procesate de AI care așteaptă export către Issue Monitoring';

-- 10. View for complete export package
CREATE OR REPLACE VIEW legislatie.v_export_package AS
SELECT 
    al.id AS act_id,
    al.tip_act,
    al.nr_act,
    al.an_act,
    al.titlu_act,
    al.metadate AS act_metadate,
    al.issue_monitoring_id AS act_im_id,
    
    -- Articole cu metadate și issues
    COALESCE(
        json_agg(DISTINCT jsonb_build_object(
            'id', a.id,
            'articol_nr', a.articol_nr,
            'ordine', a.ordine,
            'text_articol', a.text_articol,
            'metadate', a.metadate,
            'issue_monitoring_id', a.issue_monitoring_id,
            'issues', (
                SELECT json_agg(jsonb_build_object(
                    'id', i.id,
                    'denumire', i.denumire,
                    'descriere', i.descriere,
                    'confidence_score', i.confidence_score,
                    'issue_monitoring_id', i.issue_monitoring_id
                ))
                FROM legislatie.articole_issues aiss
                JOIN legislatie.issues i ON aiss.issue_id = i.id
                WHERE aiss.articol_id = a.id
            )
        ) ORDER BY a.ordine) FILTER (WHERE a.id IS NOT NULL),
        '[]'::json
    ) AS articole,
    
    -- Anexe cu metadate și issues
    COALESCE(
        json_agg(DISTINCT jsonb_build_object(
            'id', an.id,
            'anexa_nr', an.anexa_nr,
            'ordine', an.ordine,
            'titlu', an.titlu,
            'continut', an.continut,
            'metadate', an.metadate,
            'issue_monitoring_id', an.issue_monitoring_id,
            'issues', (
                SELECT json_agg(jsonb_build_object(
                    'id', i.id,
                    'denumire', i.denumire,
                    'descriere', i.descriere,
                    'confidence_score', i.confidence_score,
                    'issue_monitoring_id', i.issue_monitoring_id
                ))
                FROM legislatie.anexe_issues anis
                JOIN legislatie.issues i ON anis.issue_id = i.id
                WHERE anis.anexa_id = an.id
            )
        ) ORDER BY an.ordine) FILTER (WHERE an.id IS NOT NULL),
        '[]'::json
    ) AS anexe,
    
    -- Issues la nivel de act
    COALESCE(
        (
            SELECT json_agg(DISTINCT jsonb_build_object(
                'id', i.id,
                'denumire', i.denumire,
                'descriere', i.descriere,
                'confidence_score', i.confidence_score,
                'issue_monitoring_id', i.issue_monitoring_id
            ))
            FROM legislatie.acte_issues aci
            JOIN legislatie.issues i ON aci.issue_id = i.id
            WHERE aci.act_id = al.id
        ),
        '[]'::json
    ) AS act_issues

FROM legislatie.acte_legislative al
LEFT JOIN legislatie.articole a ON al.id = a.act_id
LEFT JOIN legislatie.anexe an ON al.id = an.act_id
WHERE al.ai_status = 'completed'
GROUP BY al.id, al.tip_act, al.nr_act, al.an_act, al.titlu_act, al.metadate, al.issue_monitoring_id;

COMMENT ON VIEW legislatie.v_export_package IS 
    'Pachet complet pentru export către Issue Monitoring (act + articole + anexe + issues)';

-- 11. Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON legislatie.issues TO legislatie_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON legislatie.anexe TO legislatie_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON legislatie.acte_issues TO legislatie_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON legislatie.articole_issues TO legislatie_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON legislatie.anexe_issues TO legislatie_user;
GRANT SELECT ON legislatie.v_pending_ai_processing TO legislatie_user;
GRANT SELECT ON legislatie.v_pending_export TO legislatie_user;
GRANT SELECT ON legislatie.v_export_package TO legislatie_user;

GRANT USAGE, SELECT ON SEQUENCE legislatie.issues_id_seq TO legislatie_user;
GRANT USAGE, SELECT ON SEQUENCE legislatie.anexe_id_seq TO legislatie_user;

COMMIT;

-- Summary
SELECT 
    'Migration completed!' AS status,
    'Parser-Law ready for AI processing and Issue Monitoring export' AS message;
