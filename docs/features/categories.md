# Categories/Domains Feature - Implementation Guide

## 📋 Overview

Sistemul permite asocierea actelor normative cu una sau mai multe **categorii/domenii** (ex: "Sănătate Publică", "Mediu", "Educație"). Categoriile sunt sincronizate dinamic de pe Issue Monitoring.

---

## 🏗️ Architecture

```
Issue Monitoring (Source of Truth)
         ↓ Sync API
Parser-Law (Local Cache)
         ↓ Assign
Legislative Acts (Many-to-Many)
```

### Data Flow:
1. **Issue Monitoring** expune categoriile prin API
2. **Parser-Law** le sincronizează în cache local (`categories` table)
3. **Users** asignează categorii la acte prin UI/API
4. **Relație many-to-many**: Un act poate avea multiple categorii

---

## 🗄️ Database Schema

### Tables Created:

```sql
-- Cache categorii din IM
legislatie.categories (
    id,
    im_category_id,  -- ID din Issue Monitoring
    name,
    slug,
    description,
    color,           -- HEX pentru UI
    icon,            -- Icon name
    ordine,          -- Display order
    is_active,
    synced_at
)

-- Junction table
legislatie.acte_categories (
    act_id,
    category_id,
    added_at,
    added_by
)
```

---

## 🚀 SETUP STEPS

### 1. Run Migration on VPS

```bash
ssh root@77.237.235.158

# Connect to PostgreSQL
docker exec -it legislatie_postgres psql -U legislatie_user -d monitoring_platform

# Run migration
\i /path/to/migrations/add_categories_support.sql

# Verify tables
\dt legislatie.categories
\dt legislatie.acte_categories

# Check default category
SELECT * FROM legislatie.categories;
```

### 2. Configure Issue Monitoring API

**On Issue Monitoring side**, create endpoint:

```python
# GET /api/v1/categories
@router.get("/categories")
async def list_categories(db: Session):
    """Return all active categories for Parser-Law sync."""
    categories = db.query(Category).filter(Category.is_active == True).all()
    
    return [
        {
            "id": cat.id,
            "name": cat.name,
            "slug": cat.slug,
            "description": cat.description,
            "color": cat.color,  # e.g., "#4CAF50"
            "icon": cat.icon,    # e.g., "medical-cross"
            "is_active": cat.is_active
        }
        for cat in categories
    ]
```

**Example categories to create in Issue Monitoring:**

```sql
INSERT INTO categories (name, slug, description, color, icon) VALUES
('Sănătate Publică', 'sanatate-publica', 'Legislație medicală, farmaceutice, pandemii', '#4CAF50', 'medical-cross'),
('Mediu și Energie', 'mediu-energie', 'Protecția mediului, energie regenerabilă', '#2196F3', 'leaf'),
('Educație', 'educatie', 'Sistem educațional, universități', '#FF9800', 'school'),
('Finanțe', 'finante', 'Legislație fiscală, buget, fonduri', '#9C27B0', 'currency-euro'),
('Justiție', 'justitie', 'Legislație penală, civilă, proceduri', '#F44336', 'gavel'),
('Transport', 'transport', 'Infrastructură rutieră, transport public', '#607D8B', 'car'),
('Muncă și Social', 'munca-social', 'Legislație muncii, asistență socială', '#795548', 'account-group'),
('Administrație Publică', 'administratie', 'Funcționarea instituțiilor publice', '#3F51B5', 'office-building'),
('Agricultură', 'agricultura', 'Legislație agricolă, subvenții', '#8BC34A', 'tractor'),
('Telecomunicații', 'telecomunicatii', 'IT, internet, comunicații', '#00BCD4', 'wifi');
```

### 3. Set API Key in Parser-Law

```bash
# On VPS
cd /opt/parser-law/db_service

# Edit .env
nano .env

# Add/update:
ISSUE_MONITORING_API_URL=https://api.issuemonitoring.ro/v1
ISSUE_MONITORING_API_KEY=your-secret-api-key-here
```

### 4. Deploy & Test

```bash
# Deploy code
cd /opt/parser-law
git pull
cd db_service
docker-compose restart api

# Wait for API
sleep 15

# Test sync
curl -X POST http://legislatie.issuemonitoring.ro/api/v1/categories/sync

# List categories
curl http://legislatie.issuemonitoring.ro/api/v1/categories
```

---

## 📡 API Endpoints

### 1. List Categories (Public)
```bash
GET /api/v1/categories?active_only=true

Response:
{
  "items": [
    {
      "id": 1,
      "im_category_id": 10,
      "name": "Sănătate Publică",
      "slug": "sanatate-publica",
      "description": "...",
      "color": "#4CAF50",
      "icon": "medical-cross",
      "is_active": true,
      "synced_at": "2025-11-10T22:00:00"
    }
  ],
  "total": 10,
  "synced_at": "2025-11-10T22:00:00"
}
```

### 2. Sync Categories from IM
```bash
POST /api/v1/categories/sync

Response:
{
  "message": "Category sync completed",
  "stats": {
    "total_fetched": 10,
    "created": 2,
    "updated": 8,
    "errors": 0,
    "synced_at": "2025-11-10T22:00:00"
  }
}
```

### 3. Get Act Categories
```bash
GET /api/v1/categories/acts/1

Response:
{
  "act_id": 1,
  "categories": [
    {
      "id": 1,
      "name": "Sănătate Publică",
      "slug": "sanatate-publica",
      "color": "#4CAF50",
      "added_at": "2025-11-10T20:00:00",
      "added_by": "user"
    }
  ],
  "total": 1
}
```

### 4. Assign Categories to Act
```bash
POST /api/v1/categories/acts/1
Content-Type: application/json

{
  "category_ids": [1, 2, 5],
  "added_by": "john.doe"
}

Response:
{
  "act_id": 1,
  "added": 3,
  "skipped": 0,
  "message": "Categories assigned successfully"
}
```

### 5. Remove Categories from Act
```bash
DELETE /api/v1/categories/acts/1?category_ids=2&category_ids=5

Response:
{
  "act_id": 1,
  "removed": 2,
  "message": "Categories removed successfully"
}
```

### 6. Replace All Categories
```bash
PUT /api/v1/categories/acts/1
Content-Type: application/json

{
  "category_ids": [1, 3],
  "added_by": "john.doe"
}

Response:
{
  "act_id": 1,
  "removed": 3,
  "added": 2,
  "message": "Categories replaced successfully"
}
```

---

## 🎨 UI Integration (Web Interface)

### Add to `index.html` - Acts Tab

```html
<!-- In acts detail modal -->
<div class="form-group">
    <label>Categorii/Domenii:</label>
    <select id="actCategories" multiple class="form-control">
        <!-- Populated dynamically from /api/v1/categories -->
    </select>
    <small class="form-text text-muted">
        Selectează una sau mai multe categorii (CTRL+Click pentru multiple)
    </small>
</div>
```

### JavaScript Functions

```javascript
// Load categories on page load
async function loadCategories() {
    const response = await fetch('/api/v1/categories');
    const data = await response.json();
    
    const select = document.getElementById('actCategories');
    select.innerHTML = '';
    
    data.items.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat.id;
        option.textContent = cat.name;
        option.style.color = cat.color;
        select.appendChild(option);
    });
}

// Load act categories when viewing act
async function loadActCategories(actId) {
    const response = await fetch(`/api/v1/categories/acts/${actId}`);
    const data = await response.json();
    
    // Mark selected in dropdown
    const select = document.getElementById('actCategories');
    const selectedIds = data.categories.map(c => c.id);
    
    Array.from(select.options).forEach(opt => {
        opt.selected = selectedIds.includes(parseInt(opt.value));
    });
}

// Save categories when submitting act
async function saveActCategories(actId) {
    const select = document.getElementById('actCategories');
    const selectedIds = Array.from(select.selectedOptions).map(opt => parseInt(opt.value));
    
    await fetch(`/api/v1/categories/acts/${actId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            category_ids: selectedIds,
            added_by: 'web_user'
        })
    });
}

// Sync categories from IM
async function syncCategories() {
    const response = await fetch('/api/v1/categories/sync', {method: 'POST'});
    const data = await response.json();
    alert(`Sync completed: ${data.stats.created} created, ${data.stats.updated} updated`);
    loadCategories(); // Refresh dropdown
}
```

### Display Categories in Acts List

```javascript
// Add category badges to each act row
function displayActCategories(act) {
    if (!act.categories || act.categories.length === 0) {
        return '<span class="badge badge-secondary">Necategorizat</span>';
    }
    
    return act.categories.map(cat => 
        `<span class="badge" style="background-color: ${cat.color}">${cat.name}</span>`
    ).join(' ');
}
```

---

## 🔄 Automated Sync

### Add to Scheduler (`scheduler.py`)

```python
# Add scheduled task for daily category sync
async def sync_categories_job():
    """Sync categories from Issue Monitoring daily."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/categories/sync"
        )
        if response.status_code == 200:
            logger.info(f"Category sync: {response.json()}")
        else:
            logger.error(f"Category sync failed: {response.status_code}")

# In scheduler setup
schedule.every().day.at("02:00").do(run_async_job, sync_categories_job)
```

---

## 🧪 Testing

```bash
# 1. Sync categories
curl -X POST http://legislatie.issuemonitoring.ro/api/v1/categories/sync

# 2. List all categories
curl http://legislatie.issuemonitoring.ro/api/v1/categories

# 3. Assign to act #1
curl -X POST http://legislatie.issuemonitoring.ro/api/v1/categories/acts/1 \
  -H "Content-Type: application/json" \
  -d '{"category_ids": [1, 2], "added_by": "test"}'

# 4. View act categories
curl http://legislatie.issuemonitoring.ro/api/v1/categories/acts/1

# 5. Remove one category
curl -X DELETE "http://legislatie.issuemonitoring.ro/api/v1/categories/acts/1?category_ids=2"

# 6. Replace all categories
curl -X PUT http://legislatie.issuemonitoring.ro/api/v1/categories/acts/1 \
  -H "Content-Type: application/json" \
  -d '{"category_ids": [1, 3], "added_by": "test"}'
```

---

## 📊 Benefits

✅ **Categorii dinamice** - Actualizate automat din Issue Monitoring  
✅ **Cache local** - Nu depinde de disponibilitatea IM pentru citire  
✅ **Many-to-many** - Un act poate avea multiple domenii  
✅ **UI friendly** - Colors & icons pentru display  
✅ **Audit trail** - Track când și cine a adăugat categorii  
✅ **Filtrare** - Posibilitate să cauți acte după categorie  

---

## 🔮 Next Steps

1. **Deploy migration** pe VPS
2. **Create categories** în Issue Monitoring
3. **Configure API key** în Parser-Law
4. **Test sync** manual
5. **Update UI** cu dropdown pentru categorii
6. **Add scheduled sync** (daily)

---

## ❓ Q&A

**Q: Ce se întâmplă dacă Issue Monitoring e offline?**  
A: Categories din cache local rămân disponibile. Sync-ul va eșua dar citirea merge.

**Q: Pot șterge o categorie?**  
A: Nu se șterge, se dezactivează (`is_active = false`). Actele păstrează asocierea istorică.

**Q: Pot adăuga categorii manual (fără IM)?**  
A: Da, prin INSERT direct în `legislatie.categories` cu `im_category_id = 0`.

**Q: Cum filtrează userii după categorie?**  
A: Adaugă query param: `GET /api/v1/acte?category=sanatate-publica`

---

## 📞 Support

Pentru issues: contact Octavian
