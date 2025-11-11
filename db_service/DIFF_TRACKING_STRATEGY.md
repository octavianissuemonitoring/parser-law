# 🎯 Strategie de Tracking Modificări pentru Re-etichetare LLM

## 📌 Problema Rezolvată

Când un act legislativ este modificat, trebuie să știm **exact ce articole s-au schimbat** pentru a le retrimite doar pe acestea către serviciul de etichetare LLM, evitând re-procesarea articolelor nemodificate.

## ✅ Soluția Implementată

### Schema Bazei de Date

```sql
-- Versioning pe acte
ALTER TABLE legislatie.acte_legislative 
ADD COLUMN versiune INTEGER NOT NULL DEFAULT 1;

-- Tabela de tracking modificări la nivel de act
CREATE TABLE legislatie.acte_modificari (
    id SERIAL PRIMARY KEY,
    act_id INTEGER NOT NULL REFERENCES legislatie.acte_legislative(id) ON DELETE CASCADE,
    versiune INTEGER NOT NULL,
    data_modificare TIMESTAMP DEFAULT NOW(),
    tip_modificare VARCHAR(50), -- 'initial', 'update_full', 'update_partial'
    sursa_modificare VARCHAR(500),
    modificat_de VARCHAR(100),
    
    -- Statistici
    articole_noi INTEGER DEFAULT 0,
    articole_modificate INTEGER DEFAULT 0,
    articole_sterse INTEGER DEFAULT 0,
    total_articole INTEGER DEFAULT 0,
    
    UNIQUE(act_id, versiune)
);

-- Tabela de tracking modificări la nivel de articol (GRANULAR)
CREATE TABLE legislatie.articole_modificari (
    id SERIAL PRIMARY KEY,
    modificare_id INTEGER NOT NULL REFERENCES legislatie.acte_modificari(id) ON DELETE CASCADE,
    articol_id INTEGER REFERENCES legislatie.articole(id) ON DELETE SET NULL,
    
    -- Identificare articol
    articol_nr VARCHAR(20),
    articol_label VARCHAR(50),
    ordine INTEGER,
    
    -- Tip schimbare
    tip_schimbare VARCHAR(20) NOT NULL, -- 'added', 'modified', 'deleted', 'unchanged'
    
    -- Valori vechi (pentru modified și deleted)
    text_vechi TEXT,
    issue_vechi TEXT,
    explicatie_veche TEXT,
    
    -- Valori noi (pentru added și modified)
    text_nou TEXT,
    
    -- Tracking re-etichetare
    necesita_reetichetare BOOLEAN NOT NULL DEFAULT TRUE,
    reetichetat BOOLEAN NOT NULL DEFAULT FALSE,
    reetichetat_la TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes pentru performance
CREATE INDEX idx_modificari_act_versiune ON legislatie.acte_modificari(act_id, versiune DESC);
CREATE INDEX idx_art_mod_reetichetare ON legislatie.articole_modificari(necesita_reetichetare, reetichetat);
CREATE INDEX idx_art_mod_tip ON legislatie.articole_modificari(tip_schimbare);
```

## 🔄 Flow de Import cu Diff Detection

### 1. Import Act Nou

```python
act = ActLegislativ(..., versiune=1)
db.add(act)

modificare = ActeModificari(
    act_id=act.id,
    versiune=1,
    tip_modificare='initial',
    articole_noi=len(articles)
)

for article in articles:
    db.add(Articol(...))
    
    # Track ca adăugat (needs labeling)
    db.add(ArticoleModificari(
        modificare_id=modificare.id,
        articol_id=article.id,
        tip_schimbare='added',
        text_nou=article.text,
        necesita_reetichetare=True
    ))
```

### 2. Re-import Act Existent (Cu Modificări)

```python
# 1. Calculate DIFF
old_articles = existing_act.articole
new_articles_data = parse_csv()

diff = ArticleDiffService.calculate_diff(old_articles, new_articles_data)
# diff = {
#     'added': [{'articol_nr': '5', 'text_nou': '...'}],
#     'modified': [{'articol_nr': '3', 'text_vechi': '...', 'text_nou': '...', 'issue_vechi': '...'}],
#     'deleted': [{'articol_nr': '7', 'text_vechi': '...'}],
#     'unchanged': [{'articol_nr': '1'}]
# }

# 2. Increment version
existing_act.versiune += 1

# 3. Create modification record
modificare = ActeModificari(
    act_id=existing_act.id,
    versiune=existing_act.versiune,
    tip_modificare='update_partial',
    articole_noi=len(diff['added']),
    articole_modificate=len(diff['modified']),
    articole_sterse=len(diff['deleted'])
)

# 4. DELETE old articles
db.execute(delete(Articol).where(Articol.act_id == existing_act.id))

# 5. INSERT new articles
for art_data in new_articles_data:
    new_art = Articol(...)
    db.add(new_art)
    db.flush()  # Get new_art.id

# 6. TRACK changes
for modified_info in diff['modified']:
    db.add(ArticoleModificari(
        modificare_id=modificare.id,
        articol_id=new_art.id,  # ID-ul noului articol
        tip_schimbare='modified',
        text_vechi=modified_info['text_vechi'],
        text_nou=modified_info['text_nou'],
        issue_vechi=modified_info['issue_vechi'],
        explicatie_veche=modified_info['explicatie_veche'],
        necesita_reetichetare=True  # ← IMPORTANT!
    ))

for added_info in diff['added']:
    db.add(ArticoleModificari(
        tip_schimbare='added',
        text_nou=added_info['text_nou'],
        necesita_reetichetare=True
    ))

for deleted_info in diff['deleted']:
    db.add(ArticoleModificari(
        tip_schimbare='deleted',
        text_vechi=deleted_info['text_vechi'],
        necesita_reetichetare=False  # Nu mai trebuie etichetat
    ))
```

## 📊 Query-uri pentru Serviciul de Etichetare

### 1. Găsește Toate Articolele Care Necesită Re-etichetare

```sql
SELECT 
    am.id as change_id,
    am.articol_id,
    am.articol_nr,
    am.tip_schimbare,
    am.text_vechi,
    am.text_nou,
    am.issue_vechi,
    am.explicatie_veche,
    a.tip_act,
    a.nr_act,
    a.an_act,
    acm.versiune
FROM legislatie.articole_modificari am
JOIN legislatie.acte_modificari acm ON am.modificare_id = acm.id
JOIN legislatie.acte_legislative a ON acm.act_id = a.id
WHERE am.necesita_reetichetare = TRUE 
  AND am.reetichetat = FALSE
ORDER BY acm.data_modificare DESC, am.ordine ASC;
```

**Rezultat:**
```
change_id | articol_id | articol_nr | tip_schimbare | text_vechi | text_nou | issue_vechi | ...
----------|------------|------------|---------------|------------|----------|-------------|----
1234      | 567        | 3          | modified      | Text v1... | Text v2  | "Issue1"    | ...
1235      | 568        | 5          | added         | NULL       | Text new | NULL        | ...
```

### 2. Găsește Articolele Modificate Dintr-un Anumit Act

```sql
SELECT *
FROM legislatie.articole_modificari am
JOIN legislatie.acte_modificari acm ON am.modificare_id = acm.id
WHERE acm.act_id = 123
  AND am.tip_schimbare IN ('added', 'modified')
  AND am.necesita_reetichetare = TRUE;
```

### 3. Statistici Re-etichetare

```sql
SELECT 
    COUNT(*) FILTER (WHERE tip_schimbare = 'added') as noi,
    COUNT(*) FILTER (WHERE tip_schimbare = 'modified') as modificate,
    COUNT(*) FILTER (WHERE reetichetat = TRUE) as etichetate,
    COUNT(*) FILTER (WHERE necesita_reetichetare = TRUE AND reetichetat = FALSE) as pending
FROM legislatie.articole_modificari
WHERE necesita_reetichetare = TRUE;
```

## 🤖 Payload pentru Serviciul LLM

### Format pentru Articol Adăugat (added)

```json
{
  "change_id": 1234,
  "article_id": 567,
  "articol_nr": "5",
  "change_type": "added",
  "act_context": {
    "tip_act": "LEGE",
    "nr_act": "123",
    "an_act": 2024,
    "titlu_act": "..."
  },
  "new": {
    "text": "Articolul nou introdus prin modificare..."
  }
}
```

### Format pentru Articol Modificat (modified)

```json
{
  "change_id": 1235,
  "article_id": 568,
  "articol_nr": "3",
  "change_type": "modified",
  "act_context": {...},
  "old": {
    "text": "Textul vechi al articolului...",
    "issue": "Eticheta veche generată de LLM",
    "explicatie": "Explicația veche"
  },
  "new": {
    "text": "Textul NOU modificat al articolului..."
  }
}
```

**Serviciul LLM decide:**
- Dacă schimbarea e minoră → păstrează issue/explicație veche
- Dacă schimbarea e majoră → generează issue/explicație nouă

### Format pentru Articol Șters (deleted)

```json
{
  "change_id": 1236,
  "article_id": null,
  "articol_nr": "7",
  "change_type": "deleted",
  "old": {
    "text": "Textul articolului șters...",
    "issue": "Eticheta veche",
    "explicatie": "Explicația veche"
  }
}
```

## 🔄 Flow Complet: Import → Etichetare → Update

### 1. Import cu Diff Tracking

```bash
POST /api/v1/acte/import
```

**Response:**
```json
{
  "success": true,
  "updated_acts": 3,
  "total_changes": {
    "added": 5,
    "modified": 12,
    "deleted": 2,
    "needs_relabeling": 17
  }
}
```

### 2. Get Pending Articles for Labeling

```bash
GET /api/v1/articole/modificari/pending
```

**Response:**
```json
{
  "pending_count": 17,
  "articles": [
    {
      "change_id": 1234,
      "article_id": 567,
      "articol_nr": "3",
      "change_type": "modified",
      "old": {"text": "...", "issue": "...", "explicatie": "..."},
      "new": {"text": "..."}
    },
    ...
  ]
}
```

### 3. Send to LLM Service

```python
# Microserviciul de etichetare
for article_change in pending_articles:
    payload = {
        "text": article_change["new"]["text"],
        "context": {
            "old_issue": article_change["old"]["issue"],
            "old_explicatie": article_change["old"]["explicatie"],
            "change_type": article_change["change_type"]
        }
    }
    
    # Call LLM
    result = llm_service.label(payload)
    # result = {"issue": "...", "explicatie": "..."}
    
    # Update article
    await update_article_labels(
        article_id=article_change["article_id"],
        issue=result["issue"],
        explicatie=result["explicatie"]
    )
    
    # Mark as re-labeled
    await mark_relabeled(change_id=article_change["change_id"])
```

### 4. Mark Article as Re-labeled

```bash
POST /api/v1/articole/modificari/{change_id}/mark-relabeled
Body: {
  "issue": "Noua etichetă",
  "explicatie": "Noua explicație"
}
```

**Update în DB:**
```sql
-- Update article
UPDATE legislatie.articole
SET issue = 'Noua etichetă',
    explicatie = 'Noua explicație',
    updated_at = NOW()
WHERE id = 567;

-- Mark as relabeled
UPDATE legislatie.articole_modificari
SET reetichetat = TRUE,
    reetichetat_la = NOW()
WHERE id = 1234;
```

## 📈 Avantaje

✅ **Eficiență**: Doar articolele modificate sunt retrimise la LLM  
✅ **Istoric Complet**: Știi exact ce s-a schimbat și când  
✅ **Audit Trail**: Poți vedea evoluția etichetelor în timp  
✅ **Rollback**: Poți restaura etichete vechi dacă e necesar  
✅ **Statistici**: Tracking precis al articolelor etichetate/pending  

## 📝 TODO: Implementare Completă

### Pași Rămași:

1. ✅ **Migrație bază de date** (creat fișier)
2. ✅ **Modele SQLAlchemy** (ActeModificari, ArticoleModificari)
3. ✅ **Diff Service** (calculate_diff cu similarity detection)
4. ✅ **Update Import Service** (integrare diff tracking)
5. ⏳ **Rulare migrație** (alembic upgrade head)
6. ⏳ **API Endpoints noi:**
   - `GET /api/v1/articole/modificari/pending` - Lista articole pending
   - `POST /api/v1/articole/modificari/{id}/mark-relabeled` - Mark ca etichetat
   - `GET /api/v1/acte/{id}/modificari` - Istoric modificări act
   - `GET /api/v1/acte/{id}/diff?v1=1&v2=2` - Comparare versiuni
7. ⏳ **Integrare cu serviciul LLM** (microserviciu separat)
8. ⏳ **Testing** (teste unitare + integration)

## 🚀 Next Steps

1. **Rulează migrația:**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

2. **Testează import cu diff:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/acte/import"
   ```

3. **Verifică tracking:**
   ```sql
   SELECT COUNT(*) FROM legislatie.articole_modificari 
   WHERE necesita_reetichetare = TRUE;
   ```

4. **Implementează endpoints pentru LLM service**

5. **Integrează cu microserviciul de etichetare**

---

**Status:** 🟡 Parțial Implementat (80%)  
**Necesită:** Rulare migrație + API endpoints + LLM integration  
**Ultima actualizare:** 2025-11-07
