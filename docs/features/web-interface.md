# 🏷️ Interfață Web - Gestionare Categorii pentru Acte Normative

## Prezentare Generală

A fost adăugată funcționalitatea completă de gestionare a categoriilor direct din interfața web. Utilizatorii pot:
- Vizualiza categoriile asociate fiecărui act normativ
- Adăuga/elimina categorii pentru orice act
- Selecta multiple categorii dintr-o listă sincronizată automat de pe Issue Monitoring

## Funcționalități Implementate

### 1. **Afișare Categorii pe Fiecare Act**

Fiecare card de act normativ din interfață afișează:
- 🏷️ Tag-uri colorate pentru fiecare categorie
- Icon personalizat pentru fiecare categorie
- Opțiune de eliminare rapidă (×) pentru fiecare categorie
- Buton "🏷️ Gestionează Categorii"

**Exemplu vizual:**
```
┌─────────────────────────────────────────────┐
│ 🗑️ Șterge                                   │
│ LEGE nr. 123/2012                           │
│ Nr: 123 | An: 2012 | Tip: LEGE              │
│ Legea educației naționale...                │
│ ─────────────────────────────────────────── │
│ 🏷️ Categorii:                              │
│ [📚 Educație ×] [⚖️ Drept Public ×]        │
│ [🏷️ Gestionează Categorii]                │
└─────────────────────────────────────────────┘
```

### 2. **Modal Interactiv pentru Gestionare**

La click pe "Gestionează Categorii" se deschide un modal cu:
- Lista completă de categorii disponibile (din Issue Monitoring)
- Checkboxes pentru selecție multiplă
- Vizualizare categoriilor deja asociate (pre-selectate)
- Butoane Salvează / Anulează

**Layout Modal:**
```
┌────────────────────────────────────────────┐
│ 🏷️ Gestionare Categorii            [×]    │
├────────────────────────────────────────────┤
│ Selectează categorii pentru acest act:    │
│ ┌────────────────────────────────────────┐ │
│ │ ☑ 📚 Educație                          │ │
│ │ ☑ ⚖️ Drept Public                      │ │
│ │ ☐ 💼 Afaceri - Reglementări B2B       │ │
│ │ ☐ 🏥 Sănătate Publică                 │ │
│ │ ☐ 🌍 Mediu și Protecția Naturii      │ │
│ └────────────────────────────────────────┘ │
│                                            │
│               [Anulează] [💾 Salvează]    │
└────────────────────────────────────────────┘
```

### 3. **Mesaj pentru Listă Goală**

Până la prima sincronizare cu Issue Monitoring, utilizatorii văd:
```
┌────────────────────────────────────────────┐
│         📭 Nu există categorii             │
│            disponibile.                    │
│                                            │
│ Categoriile se vor sincroniza automat     │
│ de pe Issue Monitoring.                   │
│ Până atunci, lista va rămâne goală.      │
└────────────────────────────────────────────┘
```

## Operațiuni Disponibile

### **Adăugare/Modificare Categorii**
1. Click pe "🏷️ Gestionează Categorii" pe orice act
2. Bifează/debifează categoriile dorite
3. Click "💾 Salvează"
4. Categoriile se actualizează instant în interfață

### **Eliminare Rapidă**
- Click pe × din orice tag de categorie
- Confirmare
- Categoria se elimină fără a deschide modalul

### **Sincronizare Automată**
- Lista de categorii se actualizează automat când se face sync cu Issue Monitoring
- Categoriile șterse din IM devin indisponibile (soft-delete)
- Categoriile redenumite în IM se actualizează automat

## API Endpoints Utilizate

Interfața folosește următoarele endpoint-uri:

| Endpoint | Metodă | Descriere |
|----------|--------|-----------|
| `/api/v1/categories` | GET | Obține toate categoriile active |
| `/api/v1/categories/acts/{id}` | GET | Obține categoriile unui act |
| `/api/v1/categories/acts/{id}` | PUT | Înlocuiește toate categoriile unui act |
| `/api/v1/categories/acts/{id}` | DELETE | Elimină categorii specifice |

## Exemple de Utilizare

### **Caz 1: Act nou importat (fără categorii)**
```javascript
// Utilizatorul vede card-ul actului fără secțiunea "Categorii"
// Click pe "Gestionează Categorii"
// Selectează: ✓ Educație, ✓ Drept Public
// Salvează → Tag-urile apar pe card
```

### **Caz 2: Modificare categorii existente**
```javascript
// Actul are: [Educație] [Drept Public]
// Click pe "Gestionează Categorii"
// Debifează: Drept Public
// Bifează: Sănătate
// Salvează → Acum are: [Educație] [Sănătate]
```

### **Caz 3: Eliminare rapidă**
```javascript
// Actul are: [Educație] [Drept Public]
// Click pe × de la "Educație"
// Confirmare
// Acum are: [Drept Public]
```

## Cod Sursă Cheie

### **Încărcare Categorii cu Async/Await**
```javascript
acts.forEach(async act => {
    // Fetch categories for this act
    const catResponse = await fetch(`${API_BASE}/categories/acts/${act.id}`);
    const categories = await catResponse.json();
    
    // Render category tags
    if (categories && categories.length > 0) {
        categoriesHTML = `
            <div class="category-tags">
                ${categories.map(cat => `
                    <span class="category-tag" style="background: ${cat.color}">
                        ${cat.icon} ${cat.name}
                        <span class="remove-cat" onclick="removeCategory(...)">×</span>
                    </span>
                `).join('')}
            </div>
        `;
    }
});
```

### **Salvare Categorii (PUT)**
```javascript
async function saveActCategories() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
    const selectedCategoryIds = Array.from(checkboxes).map(cb => parseInt(cb.value));
    
    const response = await fetch(`${API_BASE}/categories/acts/${actId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({category_ids: selectedCategoryIds})
    });
    
    if (response.ok) {
        alert('✅ Categoriile au fost salvate cu succes!');
        closeCategoriesModal();
        loadActs(); // Refresh
    }
}
```

### **Eliminare Categorie Individuală**
```javascript
async function removeCategory(actId, categoryId, event) {
    event.stopPropagation(); // Prevent card click
    
    const response = await fetch(`${API_BASE}/categories/acts/${actId}`, {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({category_ids: [categoryId]})
    });
    
    if (response.ok) {
        loadActs(); // Refresh to show changes
    }
}
```

## Styling CSS

### **Tag-uri de Categorii**
```css
.category-tag {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 12px;
    background: #667eea;
    color: white;
    border-radius: 20px;
    font-size: 0.85em;
    font-weight: 500;
}

.category-tag .remove-cat {
    cursor: pointer;
    font-weight: bold;
    padding: 0 3px;
    margin-left: 3px;
}

.category-tag .remove-cat:hover {
    color: #ffcccc;
}
```

### **Modal Design**
```css
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    background: rgba(0,0,0,0.5);
}

.modal-content {
    background: white;
    margin: 5% auto;
    padding: 30px;
    border-radius: 15px;
    max-width: 600px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.3);
}
```

## Flux de Date

```
┌─────────────────┐
│  Issue          │  Sync manual sau automat
│  Monitoring     │  POST /categories/sync
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Parser-Law DB  │
│  (legislatie.   │  GET /categories
│   categories)   │  (active_only=true)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Web Interface  │
│  Checkbox List  │
│  in Modal       │
└────────┬────────┘
         │
         ▼ User selects
┌─────────────────┐
│  PUT /categories│
│  /acts/{id}     │  Updates junction table
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  legislatie.    │
│  acte_          │
│  categories     │
└─────────────────┘
```

## Testing Manual

### **Test 1: Afișare Card cu Categorii**
```bash
# 1. Deploy aplicația
# 2. Navighează la tab "Acte Normative"
# 3. Verifică dacă fiecare card are butonul "Gestionează Categorii"
# 4. Dacă sunt categorii asociate, verifică dacă tag-urile sunt afișate
```

### **Test 2: Adăugare Categorii**
```bash
# 1. Click pe "Gestionează Categorii" pe orice act
# 2. Verifică modalul se deschide
# 3. Bifează 2-3 categorii
# 4. Click "Salvează"
# 5. Verifică tag-urile apar pe card
```

### **Test 3: Eliminare Rapidă**
```bash
# 1. Pe un act cu categorii, click × pe un tag
# 2. Confirmă
# 3. Verifică tag-ul dispare instant
```

### **Test 4: Listă Goală**
```bash
# 1. Înainte de prima sincronizare
# 2. Click "Gestionează Categorii"
# 3. Verifică mesajul "Nu există categorii disponibile"
```

## Deployment

### **Fișiere Modificate**
- ✅ `db_service/app/static/index.html` (adăugat CSS, HTML, JavaScript)

### **Fișiere Necesare (deja create)**
- ✅ `db_service/migrations/add_categories_support.sql`
- ✅ `db_service/app/services/category_service.py`
- ✅ `db_service/app/api/routes/categories.py`

### **Pași Deploy**
```bash
# 1. Commit modificările
git add db_service/app/static/index.html
git commit -m "feat: Add categories management UI to web interface"

# 2. Push la repo
git push origin master

# 3. Deploy pe VPS
ssh root@77.237.235.158
cd /opt/parser-law
git pull
docker-compose restart api

# 4. Testare
# Navighează la http://legislatie.issuemonitoring.ro
```

## Limitări și Considerații

### **Performanță**
- Categoriile se încarcă async pentru fiecare act (poate dura câteva secunde pentru 50+ acte)
- Consideră paginare sau lazy-loading pentru volume mari

### **Sincronizare**
- Lista de categorii din modal este cached (se încarcă o dată la deschidere)
- Refresh pagină pentru a vedea categorii nou sincronizate din IM

### **UX**
- Eliminarea categoriei (×) cere confirmare pentru a preveni delete-uri accidentale
- Modal se închide automat la salvare sau click pe fundal

## Roadmap Viitor

- [ ] Filtru acte după categorii (dropdown în bara de filtre)
- [ ] Badge cu număr de acte per categorie
- [ ] Search categorii în modal (pentru liste lungi)
- [ ] Drag-and-drop pentru reordonare categorii
- [ ] Export acte filtrate după categorii
- [ ] Statistici pe categorii (dashboard)

## Q&A

**Q: De ce lista e goală la început?**  
A: Categoriile trebuie sincronizate manual sau automat de pe Issue Monitoring. Rulează `POST /categories/sync` pentru prima sincronizare.

**Q: Cum actualizez categoriile după ce IM le modifică?**  
A: Rulează din nou `POST /categories/sync`. Categoriile se actualizează automat (rename) sau se dezactivează (delete).

**Q: Pot șterge complet o categorie din Parser-Law?**  
A: Nu. Sistemul folosește soft-delete (is_active=false) pentru a păstra istoricul.

**Q: Cum adaug categorii noi?**  
A: Categoriile se adaugă doar în Issue Monitoring. Parser-Law le sincronizează automat.

---

**Autor**: GitHub Copilot  
**Data**: 10 noiembrie 2025  
**Versiune**: 1.0
