# Strategia de Actualizare a Actelor Legislative

## 🎯 Obiectiv

Gestionarea actualizărilor actelor legislative când un act normativ modifică articole existente.

## 📊 Implementare în 3 Faze

### **FAZA 1: UPDATE IN-PLACE (Implementat acum)**

**Comportament:**
- Detectează act existent prin `url_legislatie`
- Actualizează conținutul actului
- **ȘTERGE** toate articolele vechi
- **INSEREAZĂ** articolele noi
- `updated_at` se actualizează automat

**Cod:**
```python
# În import_service.py
existing_act = await db.execute(
    select(ActLegislativ).where(ActLegislativ.url_legislatie == url)
)
existing_act = existing_act.scalar_one_or_none()

if existing_act:
    # Update act metadata
    existing_act.titlu_act = new_data["titlu_act"]
    existing_act.html_content = markdown_content
    # ... update other fields
    
    # Delete old articles
    await db.execute(
        delete(Articol).where(Articol.act_id == existing_act.id)
    )
    
    # Insert new articles
    for row in csv_rows:
        article = Articol(act_id=existing_act.id, ...)
        db.add(article)
    
    await db.commit()
```

**Avantaje:**
- ✅ Simplu, rapid de implementat
- ✅ Fără duplicări
- ✅ `updated_at` arată când s-a modificat ultima dată

**Limitări:**
- ❌ Pierzi istoricul modificărilor
- ❌ Nu știi ce articole s-au schimbat

---

### **FAZA 2: TRACKING MODIFICĂRI (Medium-term)**

**Adaugă tabel pentru istoric:**

```sql
-- Migration: add_modification_tracking.sql
CREATE TABLE legislatie.acte_modificari (
    id SERIAL PRIMARY KEY,
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    
    -- Versioning
    versiune INTEGER NOT NULL DEFAULT 1,
    data_modificare TIMESTAMP DEFAULT NOW(),
    
    -- Metadata
    tip_modificare VARCHAR(50) NOT NULL, -- 'initial', 'update_full', 'update_partial'
    sursa_modificare VARCHAR(500), -- URL al actului care a modificat
    modificat_de VARCHAR(100), -- user/system
    
    -- Snapshot-ul modificării
    snapshot_json JSONB, -- Conținut complet sau diff
    
    -- Stats
    articole_adaugate INTEGER DEFAULT 0,
    articole_modificate INTEGER DEFAULT 0,
    articole_sterse INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_act_version UNIQUE(act_id, versiune)
);

CREATE INDEX idx_modificari_act ON legislatie.acte_modificari(act_id, versiune DESC);
CREATE INDEX idx_modificari_data ON legislatie.acte_modificari(data_modificare DESC);

-- Add versiune to main table
ALTER TABLE legislatie.acte_legislative ADD COLUMN versiune INTEGER DEFAULT 1;
```

**Implementare:**

```python
async def import_with_tracking(self, csv_file: Path, db: AsyncSession):
    existing_act = await self._get_act_by_url(url, db)
    
    if existing_act:
        # Save current state before update
        modificare = ActeModificari(
            act_id=existing_act.id,
            versiune=existing_act.versiune + 1,
            tip_modificare='update_full',
            sursa_modificare=url,
            snapshot_json={
                'old_title': existing_act.titlu_act,
                'old_articles_count': len(existing_act.articole),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        db.add(modificare)
        
        # Increment version
        existing_act.versiune += 1
        
        # Update act & articles (same as FAZA 1)
        # ...
```

**Avantaje:**
- ✅ Păstrezi când s-a modificat
- ✅ Poți vedea câte versiuni are un act
- ✅ Audit trail simplu
- ✅ Minim overhead (doar metadata)

---

### **FAZA 3: DIFF GRANULAR (Long-term / Enterprise)**

**Pentru tracking la nivel de articol:**

```sql
CREATE TABLE legislatie.articole_istoric (
    id SERIAL PRIMARY KEY,
    articol_id INTEGER NOT NULL REFERENCES legislatie.articole(id) ON DELETE CASCADE,
    modificare_id INTEGER NOT NULL REFERENCES legislatie.acte_modificari(id) ON DELETE CASCADE,
    
    -- Articol info
    articol_nr VARCHAR(20),
    
    -- Content diff
    text_vechi TEXT,
    text_nou TEXT,
    
    -- Change type
    tip_modificare VARCHAR(20) NOT NULL, -- 'added', 'modified', 'deleted'
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_articol FOREIGN KEY (articol_id) REFERENCES legislatie.articole(id),
    CONSTRAINT fk_modificare FOREIGN KEY (modificare_id) REFERENCES legislatie.acte_modificari(id)
);

CREATE INDEX idx_articole_istoric_articol ON legislatie.articole_istoric(articol_id);
CREATE INDEX idx_articole_istoric_modificare ON legislatie.articole_istoric(modificare_id);
```

**Implementare cu diff algorithm:**

```python
from difflib import SequenceMatcher

async def import_with_diff(self, csv_file: Path, db: AsyncSession):
    existing_act = await self._get_act_by_url(url, db)
    
    if existing_act:
        # Get current articles
        old_articles = {a.articol_nr: a for a in existing_act.articole}
        new_articles_data = self._parse_articles(csv_file)
        
        # Calculate diff
        stats = {
            'added': 0,
            'modified': 0,
            'deleted': 0
        }
        
        modificare = ActeModificari(
            act_id=existing_act.id,
            versiune=existing_act.versiune + 1,
            tip_modificare='update_partial'
        )
        db.add(modificare)
        await db.flush()  # Get modificare.id
        
        # Process changes
        new_article_nrs = set(a['articol_nr'] for a in new_articles_data)
        old_article_nrs = set(old_articles.keys())
        
        # Added articles
        added = new_article_nrs - old_article_nrs
        for art_nr in added:
            art_data = next(a for a in new_articles_data if a['articol_nr'] == art_nr)
            new_article = Articol(act_id=existing_act.id, **art_data)
            db.add(new_article)
            await db.flush()
            
            db.add(ArticoleIstoric(
                articol_id=new_article.id,
                modificare_id=modificare.id,
                articol_nr=art_nr,
                text_nou=art_data['text_articol'],
                tip_modificare='added'
            ))
            stats['added'] += 1
        
        # Modified articles
        for art_nr in new_article_nrs & old_article_nrs:
            old_art = old_articles[art_nr]
            new_data = next(a for a in new_articles_data if a['articol_nr'] == art_nr)
            
            if old_art.text_articol != new_data['text_articol']:
                db.add(ArticoleIstoric(
                    articol_id=old_art.id,
                    modificare_id=modificare.id,
                    articol_nr=art_nr,
                    text_vechi=old_art.text_articol,
                    text_nou=new_data['text_articol'],
                    tip_modificare='modified'
                ))
                
                # Update article
                old_art.text_articol = new_data['text_articol']
                stats['modified'] += 1
        
        # Deleted articles
        deleted = old_article_nrs - new_article_nrs
        for art_nr in deleted:
            old_art = old_articles[art_nr]
            db.add(ArticoleIstoric(
                articol_id=old_art.id,
                modificare_id=modificare.id,
                articol_nr=art_nr,
                text_vechi=old_art.text_articol,
                tip_modificare='deleted'
            ))
            await db.delete(old_art)
            stats['deleted'] += 1
        
        # Update stats
        modificare.articole_adaugate = stats['added']
        modificare.articole_modificate = stats['modified']
        modificare.articole_sterse = stats['deleted']
        
        existing_act.versiune += 1
        await db.commit()
```

**Avantaje:**
- ✅ Istoric complet la nivel de articol
- ✅ Poți reconstrui orice versiune
- ✅ Diff vizual între versiuni
- ✅ Audit trail granular

---

## 🚀 Plan de Implementare

### **Acum (Faza 1):**
1. Modifică `import_service.py` să facă UPDATE în loc de SKIP
2. Testează cu acte modificate

### **Luna viitoare (Faza 2):**
1. Creează migration pentru `acte_modificari`
2. Adaugă `versiune` la `ActLegislativ`
3. Implementează tracking simplu

### **Peste 3 luni (Faza 3):**
1. Adaugă `articole_istoric`
2. Implementează diff algorithm
3. Creează endpoints pentru vizualizare istoric

---

## 📊 API Endpoints Noi (Faza 2-3)

```python
# Get act history
GET /api/v1/acte/{act_id}/modificari
Response: [
    {
        "versiune": 2,
        "data_modificare": "2025-11-07T10:00:00Z",
        "articole_modificate": 5,
        "tip_modificare": "update_partial"
    }
]

# Get specific version
GET /api/v1/acte/{act_id}/versiuni/{versiune}

# Compare versions
GET /api/v1/acte/{act_id}/diff?v1=1&v2=2
Response: {
    "added": [{"articol_nr": "5", "text": "..."}],
    "modified": [{"articol_nr": "3", "old": "...", "new": "..."}],
    "deleted": [{"articol_nr": "7"}]
}

# Article history
GET /api/v1/articole/{articol_id}/istoric
```

---

## 🎯 Recomandare Finală

**START cu Faza 1** (simplu, funcțional) și **evoluează treptat** către Faza 2-3 când ai:
- Multe acte care se modifică frecvent
- Nevoia de audit trail
- Cerințe compliance/legale pentru tracking

**Nu implementa Faza 3 dacă:**
- Ai <1000 acte
- Modificările sunt rare
- Nu ai resurse pentru mentenanță

**Implementează Faza 3 dacă:**
- Ai zeci de mii de acte
- Modificări frecvente (săptămânale)
- Cerințe stricte de audit
- Necesitate de comparare versiuni
