# 🔄 Strategia de Actualizare a Actelor Legislative

## 📌 Rezumat Executiv

Sistemul implementează **UPDATE IN-PLACE** pentru actualizarea actelor legislative când se reimportează același act (identificat prin URL).

## ✅ Comportament Actual (FAZA 1 - Implementat)

### Când se reimportează un act existent:

1. **Detectare:** Verifică dacă actul există deja în bază (prin `url_legislatie`)
2. **Update Metadata:** Actualizează toate câmpurile actului (titlu, dată, MOF, etc.)
3. **Ștergere Articole:** Șterge TOATE articolele vechi asociate actului
4. **Insert Articole Noi:** Inserează toate articolele din noul CSV
5. **Timestamp:** `updated_at` se actualizează automat la data curentă

### Exemplu Flow:

```
Act ID 1: LEGE 123/2024 (53 articole) - created_at: 2025-01-01
                ↓ REIMPORT
Act ID 1: LEGE 123/2024 (55 articole) - updated_at: 2025-11-07
   • Metadata actualizată (titlu, HTML content)
   • 53 articole vechi ȘTERSE
   • 55 articole noi INSERATE
```

## 🎯 Rezultate Import

```json
{
  "success": true,
  "total_files": 7,
  "imported_acts": 0,      // Acte NOI create
  "updated_acts": 7,       // Acte EXISTENTE actualizate
  "imported_articles": 383,
  "skipped_acts": 0,
  "errors": []
}
```

## 📊 Tracking Disponibil Acum

### Ce poți vedea:

- **`created_at`**: Când a fost creat actul inițial
- **`updated_at`**: Ultima dată când a fost modificat
- **Count articole**: Câte articole are acum

### Exemplu Query:

```sql
-- Acte modificate recent
SELECT id, tip_act, nr_act, an_act, 
       created_at, updated_at,
       updated_at - created_at as timp_de_la_creare
FROM legislatie.acte_legislative
WHERE updated_at > created_at
ORDER BY updated_at DESC;

-- Acte niciodată modificate
SELECT COUNT(*) 
FROM legislatie.acte_legislative
WHERE updated_at = created_at;
```

## 🔮 Evoluție Viitoare

Documentația completă pentru implementări avansate se află în: **`UPDATE_STRATEGY.md`**

### FAZA 2: Tracking Modificări (Planificat)
- Tabel `acte_modificari` pentru istoric
- Câmp `versiune` pe `ActLegislativ`
- Statistici: articole adăugate/modificate/șterse

### FAZA 3: Diff Granular (Enterprise)
- Tabel `articole_istoric` pentru tracking la nivel de articol
- Comparare versiuni
- Reconstituire versiuni anterioare

## 🚀 Utilizare

### 1. Import Inițial
```bash
curl -X POST "http://localhost:8000/api/v1/acte/import"
```

### 2. Re-import (Update)
```bash
# Modifică fișierele în rezultate/
# Rulează același import:
curl -X POST "http://localhost:8000/api/v1/acte/import"
```

### 3. Verificare Modificări
```bash
# Vezi acte actualizate recent
curl "http://localhost:8000/api/v1/acte?sort=updated_at&order=desc"
```

## 📝 Logging

La fiecare update vezi în log:

```
🔄 Processing: LEGE_123_2024.csv
   🔄 Updating existing act (ID: 1)...
   🗑️  Deleted 53 old articles
   ✅ Added 55 new articles
🔄 Updated: Legea energiei...
   📊 55 articles (was 53)
```

## ⚙️ Cod Relevant

**Fișier:** `db_service/app/services/import_service.py`

**Funcție:** `import_csv_file()`

**Logica:**
```python
existing_act = await db.get_by_url(url)

if existing_act:
    # UPDATE metadata
    for key, value in act_data.items():
        setattr(existing_act, key, value)
    
    # DELETE old articles
    await db.execute(delete(Articol).where(Articol.act_id == existing_act.id))
    
    # INSERT new articles
    for row in csv_rows:
        article = Articol(act_id=existing_act.id, ...)
        db.add(article)
```

## 🎯 Limitări Actuale

❌ **NU păstrăm istoric**: Nu știi ce s-a modificat exact între versiuni
❌ **NU avem versioning**: Nu poți face rollback la versiunea anterioară
❌ **NU detectăm diff-uri**: Nu știi care articole s-au schimbat

✅ **AVEM**: Date actualizate, timestamp modificare, performanță excelentă

## 💡 Recomandări

**Pentru proiecte mici/medii (0-10,000 acte):**
- ✅ FAZA 1 (actual) este **suficientă**
- Simplu, rapid, fără overhead
- `updated_at` oferă informații de bază

**Pentru proiecte mari (10,000+ acte):**
- Consider FAZA 2 pentru tracking modificări
- Vezi `UPDATE_STRATEGY.md` pentru detalii

**Pentru cerințe enterprise/compliance:**
- Implementează FAZA 3 cu diff granular
- Necesită resurse suplimentare (storage, procesare)

## 📚 Documentație Adițională

- **`UPDATE_STRATEGY.md`**: Strategii avansate (Faza 2-3)
- **`DEPLOYMENT.md`**: Deployment și configurare
- **`README.md`**: Overview general al sistemului

## 🐛 Troubleshooting

### Problem: Actele nu se updatează

**Verificare:**
```sql
-- Verifică URL-ul actului
SELECT id, url_legislatie FROM legislatie.acte_legislative WHERE id = 1;
```

**Cauză:** URL-ul din CSV nu matches cu URL-ul din baza de date

**Fix:** Asigură-te că CSV-ul conține același `url_legislatie`

### Problem: Articolele vechi rămân

**Cauză:** Probabil eroare la DELETE

**Verificare:**
```python
# Vezi în log dacă apare:
# "🗑️  Deleted X old articles"
```

**Fix:** Verifică constraint-ul CASCADE pe foreign key

## 📞 Contact

Pentru întrebări despre strategia de actualizare, consultă:
1. Acest document (`UPDATE_README.md`)
2. Strategia completă (`UPDATE_STRATEGY.md`)
3. Code: `app/services/import_service.py`

---

**Ultima actualizare:** 2025-11-07  
**Status:** ✅ FAZA 1 Implementată și Testată  
**Versiune:** 1.0
