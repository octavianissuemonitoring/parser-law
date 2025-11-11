# Documentație Bază de Date - Legislație Parser

**Versiune:** 1.0  
**Data:** 11 Noiembrie 2025  
**Bază de date:** `monitoring_platform`  
**Schema:** `legislatie`

---

## 📋 Cuprins

1. [Prezentare Generală](#prezentare-generală)
2. [Diagrama Relațiilor](#diagrama-relațiilor)
3. [Tabele Principale](#tabele-principale)
4. [Tabele de Relații (Junction)](#tabele-de-relații-junction)
5. [Tabele de Modificări](#tabele-de-modificări)
6. [Views](#views)
7. [Indecși și Performanță](#indecși-și-performanță)
8. [Workflow și Integrări](#workflow-și-integrări)

---

## 🎯 Prezentare Generală

Baza de date stochează **acte normative românești** cu structura lor ierarhică completă (articole, anexe) și permite integrarea cu sistemul **Issue Monitoring** pentru analiza automată AI.

### Entități Principale

| Entitate | Descriere | Relații |
|----------|-----------|---------|
| **acte_legislative** | Actele normative (legi, OUG-uri, etc.) | → articole, anexe, categories, issues |
| **articole** | Articolele din acte (structură ierarhică) | → act, issues, modificări |
| **anexe** | Anexele actelor normative | → act, issues |
| **categories** | Categorii/domenii din Issue Monitoring | ← acte |
| **issues** | Probleme/teme identificate de IM | ← acte, articole, anexe |
| **linkuri_legislatie** | URL-uri către surse legislație.just.ro | → acte |

---

## 🔗 Diagrama Relațiilor

```
┌─────────────────────┐
│  linkuri_legislatie │
└──────────┬──────────┘
           │
           │ (1:N)
           ▼
┌─────────────────────┐         ┌─────────────────┐
│  acte_legislative   │◄────────┤   categories    │
│  (Actul normativ)   │  (M:N)  │   (Domenii)     │
└──────────┬──────────┘         └─────────────────┘
           │                            ▲
           │                            │
           │ (1:N)                      │ sync
           │                            │
           ├─────────────┐              │
           │             │              │
           ▼             ▼              │
    ┌──────────┐  ┌──────────┐   ┌─────────────┐
    │ articole │  │  anexe   │   │   issues    │
    │(Articol) │  │ (Anexă)  │   │ (Probleme)  │
    └────┬─────┘  └────┬─────┘   └──────┬──────┘
         │             │                 │
         │             │                 │
         │ (M:N)       │ (M:N)          │
         │             │                 │
         └─────────────┴─────────────────┘
              (articole_issues,
               acte_issues,
               anexe_issues)

┌─────────────────────┐
│  acte_modificari    │  (Istoric modificări acte)
└─────────────────────┘

┌─────────────────────┐
│articole_modificari  │  (Istoric modificări articole)
└─────────────────────┘
```

---

## 📊 Tabele Principale

### 1. `acte_legislative`

**Descriere:** Actele normative (legi, OUG, metodologii, etc.)

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID unic |
| `tip_act` | VARCHAR(50) | NOT NULL | Tipul actului (LEGE, OUG, ORDIN, etc.) |
| `nr_act` | VARCHAR(50) | NULL | Numărul actului |
| `data_act` | DATE | NULL | Data actului |
| `an_act` | INTEGER | NULL | Anul actului |
| `titlu_act` | TEXT | NOT NULL | Titlul complet |
| `emitent_act` | VARCHAR(255) | NULL | Instituția emitentă |
| `mof_nr` | VARCHAR(50) | NULL | Număr Monitorul Oficial |
| `mof_data` | DATE | NULL | Data publicare MOf |
| `mof_an` | INTEGER | NULL | An publicare MOf |
| `url_legislatie` | VARCHAR(500) | NOT NULL | URL sursă (legislatie.just.ro) |
| `html_content` | TEXT | NULL | Conținut HTML complet |
| `confidence_score` | DOUBLE | NULL | Scor încredere parser (0-1) |
| `versiune` | INTEGER | DEFAULT 1 | Versiunea actului |
| `ai_status` | VARCHAR(20) | DEFAULT 'pending' | Status procesare AI |
| `ai_processed_at` | TIMESTAMP | NULL | Data procesării AI |
| `ai_error` | TEXT | NULL | Eroare AI (dacă există) |
| `metadate` | TEXT | NULL | Metadate/sumarizare generată de AI |
| `export_status` | VARCHAR(20) | DEFAULT 'pending' | Status export către IM |
| `export_at` | TIMESTAMP | NULL | Data exportului către IM |
| `export_error` | TEXT | NULL | Eroare export (dacă există) |
| `issue_monitoring_id` | INTEGER | NULL | ID în baza Issue Monitoring |
| `created_at` | TIMESTAMP | DEFAULT now() | Data creării |
| `updated_at` | TIMESTAMP | DEFAULT now() | Data actualizării |

**Constrângeri:**
- `ai_status IN ('pending', 'processing', 'completed', 'error')`
- `export_status IN ('pending', 'exported', 'error')`

**Indecși:**
- `ix_acte_tip_act` - pe `tip_act`
- `ix_acte_an_act` - pe `an_act`
- `ix_acte_mof_an` - pe `mof_an`
- `idx_acte_ai_status` - pe `ai_status`
- `idx_acte_export_status` - pe `export_status`
- `idx_acte_im_id` - pe `issue_monitoring_id`

---

### 2. `articole`

**Descriere:** Articolele din acte cu structură ierarhică completă

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID unic |
| `act_id` | INTEGER | FK → acte_legislative | Actul din care face parte |
| `articol_nr` | VARCHAR(20) | NULL | Numărul articolului (ex: "1", "2.1") |
| `articol_label` | VARCHAR(50) | NULL | Label complet (ex: "Articolul 1") |
| `titlu_nr` | INTEGER | NULL | Număr titlu (dacă face parte dintr-un titlu) |
| `titlu_denumire` | TEXT | NULL | Denumirea titlului |
| `capitol_nr` | INTEGER | NULL | Număr capitol |
| `capitol_denumire` | TEXT | NULL | Denumirea capitolului |
| `sectiune_nr` | INTEGER | NULL | Număr secțiune |
| `sectiune_denumire` | TEXT | NULL | Denumirea secțiunii |
| `subsectiune_nr` | INTEGER | NULL | Număr subsecțiune |
| `subsectiune_denumire` | TEXT | NULL | Denumirea subsecțiunii |
| `text_articol` | TEXT | NOT NULL | Textul complet al articolului |
| `issue` | TEXT | NULL | **Eticheta Issue (din IM - analiză AI)** |
| `explicatie` | TEXT | NULL | **Explicația articolului (din IM)** |
| `ordine` | INTEGER | NULL | Ordinea în act (pentru sortare) |
| `ai_status` | VARCHAR(20) | DEFAULT 'pending' | Status procesare AI |
| `ai_processed_at` | TIMESTAMP | NULL | Data procesării AI |
| `ai_error` | TEXT | NULL | Eroare AI |
| `metadate` | TEXT | NULL | **Metadate generate de AI** |
| `issue_monitoring_id` | INTEGER | NULL | ID în baza Issue Monitoring |
| `created_at` | TIMESTAMP | DEFAULT now() | Data creării |
| `updated_at` | TIMESTAMP | DEFAULT now() | Data actualizării |

**Structură Ierarhică:**
```
Titlu I: Dispoziții generale
  Capitol I: Scopul și obiectul
    Secțiunea 1: Definiții
      Articolul 1: text...
      Articolul 2: text...
```

**Constrângeri:**
- `ai_status IN ('pending', 'processing', 'completed', 'error')`

**Indecși:**
- `ix_articole_act_id` - pe `act_id` (cel mai important!)
- `ix_articole_act_articol` - pe `(act_id, articol_nr)`
- `ix_articole_act_ordine` - pe `(act_id, ordine)`
- `idx_articole_ai_status` - pe `ai_status`
- `idx_articole_im_id` - pe `issue_monitoring_id`

---

### 3. `anexe`

**Descriere:** Anexele actelor normative

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID unic |
| `act_id` | INTEGER | FK → acte_legislative | Actul căruia îi aparține |
| `anexa_nr` | VARCHAR(20) | NULL | Numărul anexei (ex: "1", "A") |
| `anexa_label` | VARCHAR(100) | NULL | Label complet (ex: "Anexa nr. 1") |
| `titlu_anexa` | TEXT | NULL | Titlul anexei |
| `text_anexa` | TEXT | NOT NULL | Conținutul complet al anexei |
| `ordine` | INTEGER | NULL | Ordinea în act |
| `ai_status` | VARCHAR(20) | DEFAULT 'pending' | Status procesare AI |
| `ai_processed_at` | TIMESTAMP | NULL | Data procesării AI |
| `ai_error` | TEXT | NULL | Eroare AI |
| `metadate` | TEXT | NULL | Metadate generate de AI |
| `issue_monitoring_id` | INTEGER | NULL | ID în baza Issue Monitoring |
| `created_at` | TIMESTAMP | DEFAULT now() | Data creării |
| `updated_at` | TIMESTAMP | DEFAULT now() | Data actualizării |

**Constrângeri:**
- `UNIQUE (act_id, anexa_nr)` - o anexă unică per act
- `ai_status IN ('pending', 'processing', 'completed', 'error')`

**Indecși:**
- `idx_anexe_act_id` - pe `act_id`
- `idx_anexe_ordine` - pe `(act_id, ordine)`
- `idx_anexe_ai_status` - pe `ai_status`
- `idx_anexe_im_id` - pe `issue_monitoring_id`

---

### 4. `categories`

**Descriere:** Categorii/domenii din Issue Monitoring (cache local)

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID local |
| `im_category_id` | INTEGER | UNIQUE | **ID categorie în Issue Monitoring** |
| `name` | VARCHAR(255) | NOT NULL | Numele categoriei (ex: "Educație", "Sănătate") |
| `slug` | VARCHAR(100) | UNIQUE | URL-friendly identifier |
| `description` | TEXT | NULL | Descrierea categoriei |
| `color` | VARCHAR(7) | NULL | Culoare hex (ex: "#3B82F6") |
| `icon` | VARCHAR(50) | NULL | Nume icon (ex: "school", "health") |
| `ordine` | INTEGER | DEFAULT 0 | Ordine afișare în UI |
| `is_active` | BOOLEAN | DEFAULT true | Categorie activă? |
| `synced_at` | TIMESTAMP | DEFAULT now() | Ultima sincronizare din IM |
| `created_at` | TIMESTAMP | DEFAULT now() | Data creării |

**Soft-Delete Strategy:** 
- Când se face sync cu IM, categoriile care nu mai există → `is_active = false`
- Nu se șterge fizic datele pentru păstrarea istoricului

**Indecși:**
- `idx_categories_slug` - pe `slug` (UNIQUE)
- `idx_categories_im_id` - pe `im_category_id` (UNIQUE)
- `idx_categories_ordine` - pe `ordine`
- `idx_categories_active` - pe `is_active`

---

### 5. `issues`

**Descriere:** Probleme/teme identificate în Issue Monitoring

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID local |
| `im_issue_id` | INTEGER | UNIQUE | **ID issue în Issue Monitoring** |
| `titlu` | VARCHAR(500) | NOT NULL | Titlul issue-ului |
| `descriere` | TEXT | NULL | Descrierea detaliată |
| `tags` | TEXT[] | NULL | Array de taguri |
| `source` | VARCHAR(50) | NULL | Sursa issue-ului (ex: "manual", "ai") |
| `data_creare` | TIMESTAMP | NULL | Data creării în IM |
| `synced_at` | TIMESTAMP | DEFAULT now() | Ultima sincronizare |
| `created_at` | TIMESTAMP | DEFAULT now() | Data creării locale |

**Indecși:**
- `idx_issues_im_id` - pe `im_issue_id` (UNIQUE)
- `idx_issues_source` - pe `source`
- `idx_issues_data_creare` - pe `data_creare`

---

### 6. `linkuri_legislatie`

**Descriere:** URL-uri către legislatie.just.ro (sursă date)

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID unic |
| `url` | VARCHAR(500) | UNIQUE | URL complet |
| `tip_act` | VARCHAR(50) | NULL | Tip act (extras din URL) |
| `an_act` | INTEGER | NULL | An act (extras din URL) |
| `status` | VARCHAR(20) | DEFAULT 'pending' | Status procesare |
| `error_message` | TEXT | NULL | Mesaj eroare (dacă status = error) |
| `processed_at` | TIMESTAMP | NULL | Data procesării |
| `created_at` | TIMESTAMP | DEFAULT now() | Data adăugării |

**Constrângeri:**
- `status IN ('pending', 'processing', 'completed', 'error')`
- `url` - UNIQUE

**Indecși:**
- `ix_legislatie_linkuri_legislatie_id` - pe `id`
- `ix_legislatie_linkuri_legislatie_url` - pe `url` (UNIQUE)

---

## 🔗 Tabele de Relații (Junction)

### 1. `acte_categories`

**Relație:** Many-to-Many între `acte_legislative` și `categories`

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `act_id` | INTEGER | FK → acte_legislative | PK Composite |
| `category_id` | INTEGER | FK → categories | PK Composite |
| `added_at` | TIMESTAMP | DEFAULT now() | Când s-a adăugat |
| `added_by` | VARCHAR(100) | NULL | Cine a adăugat (user/system) |

**Primary Key:** `(act_id, category_id)`

**Indecși:**
- `idx_acte_categories_act` - pe `act_id`
- `idx_acte_categories_category` - pe `category_id`

---

### 2. `acte_issues`

**Relație:** Many-to-Many între `acte_legislative` și `issues`

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `act_id` | INTEGER | FK → acte_legislative | PK Composite |
| `issue_id` | INTEGER | FK → issues | PK Composite |
| `relevance_score` | DOUBLE | NULL | Scor relevanță (0-1) |
| `added_at` | TIMESTAMP | DEFAULT now() | Când s-a adăugat |

**Primary Key:** `(act_id, issue_id)`

**Indecși:**
- `idx_acte_issues_act` - pe `act_id`
- `idx_acte_issues_issue` - pe `issue_id`

---

### 3. `articole_issues`

**Relație:** Many-to-Many între `articole` și `issues`

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `articol_id` | INTEGER | FK → articole | PK Composite |
| `issue_id` | INTEGER | FK → issues | PK Composite |
| `relevance_score` | DOUBLE | NULL | Scor relevanță (0-1) |
| `added_at` | TIMESTAMP | DEFAULT now() | Când s-a adăugat |

**Primary Key:** `(articol_id, issue_id)`

**Indecși:**
- `idx_articole_issues_articol` - pe `articol_id`
- `idx_articole_issues_issue` - pe `issue_id`

---

### 4. `anexe_issues`

**Relație:** Many-to-Many între `anexe` și `issues`

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `anexa_id` | INTEGER | FK → anexe | PK Composite |
| `issue_id` | INTEGER | FK → issues | PK Composite |
| `relevance_score` | DOUBLE | NULL | Scor relevanță (0-1) |
| `added_at` | TIMESTAMP | DEFAULT now() | Când s-a adăugat |

**Primary Key:** `(anexa_id, issue_id)`

**Indecși:**
- `idx_anexe_issues_anexa` - pe `anexa_id`
- `idx_anexe_issues_issue` - pe `issue_id`

---

## 📜 Tabele de Modificări

### 1. `acte_modificari`

**Descriere:** Istoric modificări ale actelor legislative

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID unic |
| `act_id` | INTEGER | FK → acte_legislative | Actul modificat |
| `versiune_veche` | INTEGER | NULL | Versiunea anterioară |
| `versiune_noua` | INTEGER | NULL | Versiunea nouă |
| `data_modificare` | DATE | NULL | Data modificării |
| `tip_modificare` | VARCHAR(50) | NULL | Tipul (completare, abrogare, etc.) |
| `descriere_modificare` | TEXT | NULL | Descriere modificare |
| `act_modificator_id` | INTEGER | NULL | ID act care modifică |
| `created_at` | TIMESTAMP | DEFAULT now() | Data înregistrării |

**Indecși:**
- `idx_modificari_act_versiune` - pe `(act_id, versiune_noua)`
- `idx_modificari_data` - pe `data_modificare`

---

### 2. `articole_modificari`

**Descriere:** Istoric modificări ale articolelor

| Coloană | Tip | Null | Descriere |
|---------|-----|------|-----------|
| `id` | INTEGER | PK | ID unic |
| `articol_id` | INTEGER | FK → articole | Articolul modificat |
| `modificare_id` | INTEGER | FK → acte_modificari | Modificarea (act) |
| `text_vechi` | TEXT | NULL | Textul anterior |
| `text_nou` | TEXT | NULL | Textul nou |
| `tip_modificare` | VARCHAR(50) | NULL | Tipul (modificare, abrogare, etc.) |
| `necesita_reetichetare` | BOOLEAN | DEFAULT false | **Flag pentru re-analiză AI** |
| `created_at` | TIMESTAMP | DEFAULT now() | Data înregistrării |

**Indecși:**
- `idx_articole_modificari_articol` - pe `articol_id`
- `idx_articole_modificari_modificare` - pe `modificare_id`
- `idx_articole_modificari_reetichetare` - pe `necesita_reetichetare`

---

## 👁️ Views

### 1. `v_acte_cu_categorii`

**Descriere:** View pentru acte cu categoriile lor (JSON aggregat)

```sql
SELECT 
    a.id, 
    a.tip_act, 
    a.nr_act, 
    a.an_act, 
    a.titlu_act,
    json_agg(
        json_build_object(
            'id', c.id,
            'name', c.name,
            'slug', c.slug,
            'color', c.color,
            'icon', c.icon
        )
    ) AS categories
FROM acte_legislative a
LEFT JOIN acte_categories ac ON a.id = ac.act_id
LEFT JOIN categories c ON ac.category_id = c.id
GROUP BY a.id;
```

**Utilizare:** Afișare în UI cu categorii inline

---

### 2. `v_pending_export`

**Descriere:** Acte gata pentru export către Issue Monitoring

```sql
SELECT 
    a.id,
    a.tip_act,
    a.nr_act,
    a.an_act,
    a.titlu_act,
    a.metadate,
    a.ai_status,
    a.export_status,
    COUNT(DISTINCT ar.id) AS nr_articole,
    COUNT(DISTINCT an.id) AS nr_anexe,
    COUNT(DISTINCT ai.issue_id) AS nr_issues
FROM acte_legislative a
LEFT JOIN articole ar ON a.id = ar.act_id
LEFT JOIN anexe an ON a.id = an.act_id
LEFT JOIN acte_issues ai ON a.id = ai.act_id
WHERE a.ai_status = 'completed' 
  AND a.export_status = 'pending'
GROUP BY a.id;
```

**Utilizare:** Scheduler pentru export automat

---

## ⚡ Indecși și Performanță

### Indecși Critici

**Pentru queries frecvente:**

```sql
-- Căutare articole pe act
CREATE INDEX ix_articole_act_id ON articole(act_id);

-- Căutare acte pe tip și an
CREATE INDEX ix_acte_tip_act ON acte_legislative(tip_act);
CREATE INDEX ix_acte_an_act ON acte_legislative(an_act);

-- Status AI și Export (pentru dashboard)
CREATE INDEX idx_acte_ai_status ON acte_legislative(ai_status);
CREATE INDEX idx_acte_export_status ON acte_legislative(export_status);

-- Relații many-to-many (pentru JOIN-uri)
CREATE INDEX idx_acte_categories_act ON acte_categories(act_id);
CREATE INDEX idx_acte_categories_category ON acte_categories(category_id);
```

### Query Optimization Tips

**❌ BAD:**
```sql
-- Fără index pe act_id
SELECT * FROM articole WHERE act_id = 68;
```

**✅ GOOD:**
```sql
-- Cu index ix_articole_act_id
SELECT * FROM articole WHERE act_id = 68 ORDER BY ordine;
```

---

## 🔄 Workflow și Integrări

### 1. Scraping → Parsing → Storage

```
┌──────────┐    ┌─────────────┐    ┌──────────────┐
│ Scraper  │───▶│ HTML Parser │───▶│ PostgreSQL   │
│ (Python) │    │ (hybrid)    │    │ (acte + art.)│
└──────────┘    └─────────────┘    └──────────────┘
     │                                      │
     │ URL-uri                             │ act_id
     ▼                                      ▼
┌──────────────────┐             ┌──────────────────┐
│linkuri_legislatie│             │    articole      │
└──────────────────┘             └──────────────────┘
```

### 2. Categories Sync (Issue Monitoring)

```
┌──────────────────┐
│ Issue Monitoring │
│   /categories    │  ← API endpoint cu toate domeniile
└────────┬─────────┘
         │ GET (periodic)
         ▼
┌────────────────────┐
│ Category Service   │  1. Fetch categories
│ (parser-law)       │  2. Sync to local DB
└────────┬───────────┘  3. Soft-delete inactive
         │
         ▼
┌────────────────────┐
│   categories       │  Cache local cu is_active flag
│   (PostgreSQL)     │
└────────────────────┘
```

**Sync Strategy:**
- **Soft-delete**: Categories care nu mai există în IM → `is_active = false`
- **Update**: Categories existente → update name, color, icon, ordine
- **Insert**: Categories noi → insert cu `im_category_id`

### 3. AI Analysis → Issue Labeling

```
┌──────────────────┐
│ Parser-Law API   │
│ GET /acte/{id}/  │  ← Export act cu toate articolele
│ export-for-      │
│ analysis         │
└────────┬─────────┘
         │ JSON: {act: {...}, articole: [...]}
         ▼
┌────────────────────┐
│ Issue Monitoring   │  1. Primește articole
│ AI Service         │  2. Analizează cu AI
└────────┬───────────┘  3. Generează etichete
         │
         │ PUT pentru fiecare articol
         ▼
┌────────────────────┐
│ Parser-Law API     │  Update articole cu:
│ PUT /articole/{id} │  - issue: "Educație digitală"
└────────┬───────────┘  - explicatie: "Prevede..."
         │               - metadate: {...}
         ▼
┌────────────────────┐
│   articole.issue   │  Articole etichetate
│   articole.        │  pentru Issue Monitoring
│   explicatie       │
└────────────────────┘
```

### 4. Web UI Categories

```
┌──────────────────┐
│ Web Interface    │
│ (index.html)     │
└────────┬─────────┘
         │
         │ 1. Click "Manage Categories"
         ▼
┌────────────────────┐
│ Modal Dialog       │  2. GET /categories (toate)
│ - Checkboxes       │  3. GET /acte/{id}/categories (actuale)
│ - Multi-select     │  4. POST /acte/{id}/categories
└────────┬───────────┘     (selectate)
         │
         ▼
┌────────────────────┐
│ acte_categories    │  5. Insert relații
│ (junction table)   │
└────────────────────┘
```

---

## 🛠️ Exemple de Query-uri Utile

### 1. Toate actele cu categoriile lor

```sql
SELECT 
    a.id,
    a.tip_act || ' ' || a.nr_act || '/' || a.an_act AS identificator,
    a.titlu_act,
    array_agg(c.name) AS categories
FROM acte_legislative a
LEFT JOIN acte_categories ac ON a.id = ac.act_id
LEFT JOIN categories c ON ac.category_id = c.id AND c.is_active = true
GROUP BY a.id, a.tip_act, a.nr_act, a.an_act, a.titlu_act
ORDER BY a.an_act DESC, a.nr_act;
```

### 2. Statistici acte pe categorie

```sql
SELECT 
    c.name AS categorie,
    COUNT(DISTINCT ac.act_id) AS nr_acte,
    SUM(stats.nr_articole) AS total_articole
FROM categories c
LEFT JOIN acte_categories ac ON c.id = ac.category_id
LEFT JOIN (
    SELECT act_id, COUNT(*) AS nr_articole
    FROM articole
    GROUP BY act_id
) stats ON ac.act_id = stats.act_id
WHERE c.is_active = true
GROUP BY c.id, c.name
ORDER BY nr_acte DESC;
```

### 3. Articole neanalyzate (pending AI)

```sql
SELECT 
    a.tip_act || ' ' || a.nr_act || '/' || a.an_act AS act,
    COUNT(ar.id) AS articole_pending
FROM acte_legislative a
JOIN articole ar ON a.id = ar.act_id
WHERE ar.ai_status = 'pending'
GROUP BY a.id, a.tip_act, a.nr_act, a.an_act
ORDER BY articole_pending DESC;
```

### 4. Coverage analiză AI

```sql
SELECT 
    a.id,
    a.tip_act || ' ' || a.nr_act || '/' || a.an_act AS act,
    COUNT(ar.id) AS total_articole,
    COUNT(ar.issue) FILTER (WHERE ar.issue IS NOT NULL) AS articole_etichetate,
    ROUND(
        100.0 * COUNT(ar.issue) FILTER (WHERE ar.issue IS NOT NULL) / 
        NULLIF(COUNT(ar.id), 0), 
        2
    ) AS coverage_percent
FROM acte_legislative a
LEFT JOIN articole ar ON a.id = ar.act_id
GROUP BY a.id, a.tip_act, a.nr_act, a.an_act
HAVING COUNT(ar.id) > 0
ORDER BY coverage_percent DESC;
```

### 5. Sincronizare categories (last sync)

```sql
SELECT 
    name,
    slug,
    is_active,
    synced_at,
    AGE(NOW(), synced_at) AS time_since_sync
FROM categories
ORDER BY synced_at DESC;
```

---

## 📝 Notes

### Foreign Keys

Toate relațiile sunt enforced prin FK constraints:
- `articole.act_id` → `acte_legislative.id` (ON DELETE CASCADE)
- `anexe.act_id` → `acte_legislative.id` (ON DELETE CASCADE)
- `acte_categories.act_id` → `acte_legislative.id` (ON DELETE CASCADE)
- `acte_categories.category_id` → `categories.id` (ON DELETE CASCADE)
- `acte_issues.act_id` → `acte_legislative.id` (ON DELETE CASCADE)
- `acte_issues.issue_id` → `issues.id` (ON DELETE CASCADE)
- etc.

### Timestamps

Toate tabelele au:
- `created_at` - data creării (DEFAULT now())
- `updated_at` - data ultimei modificări (DEFAULT now(), trigger pentru auto-update)

### AI Status Flow

```
pending → processing → completed
   │                       │
   └──────── error ────────┘
```

### Export Status Flow

```
pending → exported
   │          │
   └─ error ──┘
```

---

## 🔐 Security Notes

- **User:** `legislatie_user`
- **Schema:** `legislatie` (isolated)
- **No public access** - toate tabelele sunt în schema privată
- **API layer** - toate queries prin FastAPI cu validare

---

## 📊 Current Stats (Nov 11, 2025)

```
Acte legislative: 5
Articole: ~2,000
Anexe: ~10
Categories: 1 (default: "Necategorizat")
Issues: 0 (pending IM integration)
```

---

**Versiune documentație:** 1.0  
**Ultima actualizare:** 11 Noiembrie 2025  
**Autor:** Octavian (Issue Monitoring Team)
