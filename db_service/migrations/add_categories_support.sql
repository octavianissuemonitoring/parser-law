-- Migration: Add Categories Support
-- Date: 2025-11-10
-- Purpose: Add categories/domains for legislative acts, synced from Issue Monitoring

BEGIN;

-- 1. Create categories cache table
CREATE TABLE IF NOT EXISTS legislatie.categories (
    id SERIAL PRIMARY KEY,
    im_category_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    color VARCHAR(7),  -- HEX color for UI (#RRGGBB)
    icon VARCHAR(50),  -- Icon name for UI
    ordine INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    synced_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_categories_im_id ON legislatie.categories(im_category_id);
CREATE INDEX idx_categories_slug ON legislatie.categories(slug);
CREATE INDEX idx_categories_active ON legislatie.categories(is_active);
CREATE INDEX idx_categories_ordine ON legislatie.categories(ordine);

COMMENT ON TABLE legislatie.categories IS 'Categorii/domenii pentru acte legislative (cache din Issue Monitoring)';
COMMENT ON COLUMN legislatie.categories.im_category_id IS 'ID categorie în Issue Monitoring';
COMMENT ON COLUMN legislatie.categories.slug IS 'URL-friendly identifier';
COMMENT ON COLUMN legislatie.categories.ordine IS 'Ordine afișare în UI';
COMMENT ON COLUMN legislatie.categories.synced_at IS 'Ultima sincronizare din Issue Monitoring';

-- 2. Create junction table for acts ↔ categories (many-to-many)
CREATE TABLE IF NOT EXISTS legislatie.acte_categories (
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES legislatie.categories(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT NOW(),
    added_by VARCHAR(100),
    
    PRIMARY KEY (act_id, category_id)
);

CREATE INDEX idx_acte_categories_act ON legislatie.acte_categories(act_id);
CREATE INDEX idx_acte_categories_category ON legislatie.acte_categories(category_id);

COMMENT ON TABLE legislatie.acte_categories IS 'Relație many-to-many: acte ↔ categorii';
COMMENT ON COLUMN legislatie.acte_categories.added_by IS 'User/system care a adăugat categoria';

-- 3. Add some default categories (will be replaced by sync)
INSERT INTO legislatie.categories (im_category_id, name, slug, description, color, ordine, is_active)
VALUES
    (0, 'Necategorizat', 'necategorizat', 'Acte fără categorie asignată', '#9E9E9E', 999, true)
ON CONFLICT (im_category_id) DO NOTHING;

-- 4. Create view for acts with categories
CREATE OR REPLACE VIEW legislatie.v_acte_cu_categorii AS
SELECT 
    al.id,
    al.tip_act,
    al.nr_act,
    al.an_act,
    al.titlu_act,
    COALESCE(
        json_agg(
            json_build_object(
                'id', c.id,
                'name', c.name,
                'slug', c.slug,
                'color', c.color,
                'icon', c.icon
            ) ORDER BY c.ordine, c.name
        ) FILTER (WHERE c.id IS NOT NULL),
        '[]'::json
    ) AS categories
FROM legislatie.acte_legislative al
LEFT JOIN legislatie.acte_categories ac ON al.id = ac.act_id
LEFT JOIN legislatie.categories c ON ac.category_id = c.id AND c.is_active = true
GROUP BY al.id;

COMMENT ON VIEW legislatie.v_acte_cu_categorii IS 'Acte cu categorii asociate (JSON)';

-- 5. Function to sync category to act when exporting to IM
CREATE OR REPLACE FUNCTION legislatie.sync_act_categories_from_im(
    p_act_id INTEGER,
    p_im_category_ids INTEGER[]
)
RETURNS INTEGER AS $$
DECLARE
    v_synced_count INTEGER := 0;
    v_cat_id INTEGER;
    v_local_cat_id INTEGER;
BEGIN
    -- For each IM category ID, find local category and link to act
    FOREACH v_cat_id IN ARRAY p_im_category_ids
    LOOP
        -- Find local category by IM ID
        SELECT id INTO v_local_cat_id
        FROM legislatie.categories
        WHERE im_category_id = v_cat_id AND is_active = true;
        
        IF v_local_cat_id IS NOT NULL THEN
            -- Insert if not exists
            INSERT INTO legislatie.acte_categories (act_id, category_id, added_by)
            VALUES (p_act_id, v_local_cat_id, 'im_sync')
            ON CONFLICT (act_id, category_id) DO NOTHING;
            
            v_synced_count := v_synced_count + 1;
        END IF;
    END LOOP;
    
    RETURN v_synced_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION legislatie.sync_act_categories_from_im IS 'Sincronizare categorii din IM la act (folosit după export)';

-- 6. Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON legislatie.categories TO legislatie_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON legislatie.acte_categories TO legislatie_user;
GRANT SELECT ON legislatie.v_acte_cu_categorii TO legislatie_user;
GRANT USAGE, SELECT ON SEQUENCE legislatie.categories_id_seq TO legislatie_user;

COMMIT;

-- Summary
SELECT 
    'Categories migration completed!' AS status,
    COUNT(*) FILTER (WHERE table_name = 'categories') AS categories_table,
    COUNT(*) FILTER (WHERE table_name = 'acte_categories') AS junction_table
FROM information_schema.tables
WHERE table_schema = 'legislatie' AND table_name IN ('categories', 'acte_categories');
