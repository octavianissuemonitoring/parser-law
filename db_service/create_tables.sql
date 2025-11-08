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
