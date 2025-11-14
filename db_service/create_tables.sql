-- Create acte_legislative table
CREATE TABLE IF NOT EXISTS legislatie.acte_legislative (
    id SERIAL PRIMARY KEY,
    tip_act VARCHAR(50) NOT NULL,
    nr_act VARCHAR(50),
    data_act DATE,
    an_act INTEGER,
    titlu_act TEXT NOT NULL,
    emitent_act VARCHAR(255),
    mof_nr VARCHAR(50),
    mof_data DATE,
    mof_an INTEGER,
    url_legislatie VARCHAR(500) NOT NULL,
    html_content TEXT,
    confidence_score FLOAT,
    -- AI Processing columns
    ai_status VARCHAR(20) DEFAULT 'pending',
    ai_processed_at TIMESTAMP,
    ai_error TEXT,
    -- Metadata and export columns
    metadate TEXT,
    export_status VARCHAR(20),
    export_at TIMESTAMP,
    export_error TEXT,
    issue_monitoring_id INTEGER,
    -- Version and timestamps
    versiune INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Create indexes on acte_legislative
CREATE INDEX IF NOT EXISTS ix_acte_tip_act ON legislatie.acte_legislative(tip_act);
CREATE INDEX IF NOT EXISTS ix_acte_an_act ON legislatie.acte_legislative(an_act);
CREATE INDEX IF NOT EXISTS ix_acte_mof_an ON legislatie.acte_legislative(mof_an);

-- Create articole table
CREATE TABLE IF NOT EXISTS legislatie.articole (
    id SERIAL PRIMARY KEY,
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    articol_nr VARCHAR(20),
    articol_label VARCHAR(50),
    titlu_nr INTEGER,
    titlu_denumire TEXT,
    capitol_nr INTEGER,
    capitol_denumire TEXT,
    sectiune_nr INTEGER,
    sectiune_denumire TEXT,
    subsectiune_nr INTEGER,
    subsectiune_denumire TEXT,
    text_articol TEXT NOT NULL,
    issue TEXT,
    explicatie TEXT,
    -- AI Processing columns
    metadate TEXT,
    ai_status VARCHAR(20) DEFAULT 'pending',
    ai_processed_at TIMESTAMP,
    ai_error TEXT,
    issue_monitoring_id INTEGER,
    -- Order and timestamps
    ordine INTEGER,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Create indexes on articole
CREATE INDEX IF NOT EXISTS ix_articole_act_id ON legislatie.articole(act_id);
CREATE INDEX IF NOT EXISTS ix_articole_act_ordine ON legislatie.articole(act_id, ordine);
CREATE INDEX IF NOT EXISTS ix_articole_act_articol ON legislatie.articole(act_id, articol_nr);

-- Create acte_modificari table (tracking changes)
CREATE TABLE IF NOT EXISTS legislatie.acte_modificari (
    id SERIAL PRIMARY KEY,
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    versiune INTEGER NOT NULL,
    data_modificare TIMESTAMP DEFAULT now(),
    tip_modificare VARCHAR(50) NOT NULL,
    sursa_modificare VARCHAR(500),
    modificat_de VARCHAR(100),
    articole_noi INTEGER DEFAULT 0,
    articole_modificate INTEGER DEFAULT 0,
    articole_sterse INTEGER DEFAULT 0,
    total_articole INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE(act_id, versiune)
);

-- Create indexes on acte_modificari
CREATE INDEX IF NOT EXISTS idx_modificari_act_versiune ON legislatie.acte_modificari(act_id, versiune);
CREATE INDEX IF NOT EXISTS idx_modificari_data ON legislatie.acte_modificari(data_modificare);

-- Create articole_modificari table (granular article change tracking)
CREATE TABLE IF NOT EXISTS legislatie.articole_modificari (
    id SERIAL PRIMARY KEY,
    modificare_id INTEGER NOT NULL REFERENCES legislatie.acte_modificari(id) ON DELETE CASCADE,
    articol_id INTEGER REFERENCES legislatie.articole(id) ON DELETE SET NULL,
    articol_nr VARCHAR(20),
    articol_label VARCHAR(50),
    ordine INTEGER,
    tip_schimbare VARCHAR(20) NOT NULL,
    text_vechi TEXT,
    issue_vechi TEXT,
    explicatie_veche TEXT,
    text_nou TEXT,
    necesita_reetichetare BOOLEAN DEFAULT true,
    reetichetat BOOLEAN DEFAULT false,
    reetichetat_la TIMESTAMP,
    created_at TIMESTAMP DEFAULT now()
);

-- Create indexes on articole_modificari
CREATE INDEX IF NOT EXISTS idx_articole_modificari_modificare ON legislatie.articole_modificari(modificare_id);
CREATE INDEX IF NOT EXISTS idx_articole_modificari_articol ON legislatie.articole_modificari(articol_id);
CREATE INDEX IF NOT EXISTS idx_articole_modificari_reetichetare ON legislatie.articole_modificari(necesita_reetichetare, reetichetat);

-- Create linkuri_legislatie table (storing legislation URLs for scraping)
CREATE TABLE IF NOT EXISTS legislatie.linkuri_legislatie (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending_scraping',
    acte_count INTEGER DEFAULT 0,
    error_message VARCHAR(1000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scraped_at TIMESTAMP
);

-- Create indexes on linkuri_legislatie
CREATE INDEX IF NOT EXISTS ix_linkuri_url ON legislatie.linkuri_legislatie(url);
CREATE INDEX IF NOT EXISTS ix_linkuri_status ON legislatie.linkuri_legislatie(status);
CREATE INDEX IF NOT EXISTS ix_linkuri_created_at ON legislatie.linkuri_legislatie(created_at);

-- Create issues table (storing identified problems/tags)
CREATE TABLE IF NOT EXISTS legislatie.issues (
    id SERIAL PRIMARY KEY,
    denumire VARCHAR(256) NOT NULL,
    descriere TEXT,
    source VARCHAR(20) DEFAULT 'ai',
    confidence_score NUMERIC(3, 2),
    issue_monitoring_id INTEGER UNIQUE,
    data_creare TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    data_modificare TIMESTAMP WITH TIME ZONE
);

-- Create indexes on issues
CREATE INDEX IF NOT EXISTS ix_issues_denumire ON legislatie.issues(denumire);
CREATE INDEX IF NOT EXISTS ix_issues_issue_monitoring_id ON legislatie.issues(issue_monitoring_id);
CREATE INDEX IF NOT EXISTS ix_issues_data_creare ON legislatie.issues(data_creare);

-- Create anexe table (storing legislative act annexes)
CREATE TABLE IF NOT EXISTS legislatie.anexe (
    id SERIAL PRIMARY KEY,
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    anexa_nr VARCHAR(50),
    ordine INTEGER NOT NULL,
    titlu TEXT,
    continut TEXT NOT NULL,
    metadate TEXT,
    ai_status VARCHAR(20) DEFAULT 'pending',
    ai_processed_at TIMESTAMP WITH TIME ZONE,
    ai_error TEXT,
    issue_monitoring_id INTEGER,
    data_creare TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    data_modificare TIMESTAMP WITH TIME ZONE,
    CONSTRAINT unique_anexa_per_act UNIQUE (act_id, ordine)
);

-- Create indexes on anexe
CREATE INDEX IF NOT EXISTS ix_anexe_act_id ON legislatie.anexe(act_id);
CREATE INDEX IF NOT EXISTS ix_anexe_ordine ON legislatie.anexe(ordine);
CREATE INDEX IF NOT EXISTS ix_anexe_issue_monitoring_id ON legislatie.anexe(issue_monitoring_id);
