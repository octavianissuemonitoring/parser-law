# Deployment Fixes - Reinstalare de la 0

**Data**: 20 noiembrie 2025
**Versiune**: v2.1.1

## Rezumat

Am identificat și rezolvat 3 probleme majore în timpul reinstalării complete a aplicației pe VPS:

1. **Multiple head revisions** - Lanț de migrații rupt
2. **Duplicate column errors** - Coloane duplicate între schema inițială și migrații incrementale
3. **Migration order** - Ordinea greșită a migrațiilor (dependințe încurcate)

## Probleme Identificate

### 1. Multiple Head Revisions

**Eroare**:
```
FAILED: Multiple head revisions are present for given argument 'head'; 
please specify a specific target revision
```

**Cauză**: Două migrații aveau același `down_revision`:
- `5f128176a40b` → pointează la `5417c175c050`
- `0b4c93b0a665` → pointează la `5417c175c050`

**Fix**: 
- Commit `c2cabbb`: Schimbat `0b4c93b0a665` să pointeze la `5f128176a40b`
- Lanț corect: `aa4552000831` → `5417c175c050` → `5f128176a40b` → `0b4c93b0a665` → `1007e30b0c57`

### 2. Duplicate Column: ai_status

**Eroare**:
```
asyncpg.exceptions.DuplicateColumnError: column "ai_status" of relation 
"acte_legislative" already exists
```

**Cauză**: Migrația inițială `aa4552000831_initial_schema_from_models.py` deja creează coloanele:
- `ai_status`
- `ai_processed_at`  
- `ai_error`
- `metadate`
- `export_status`
- `issue_monitoring_id`

Dar migrația `0b4c93b0a665_add_ai_processing_columns.py` încearcă să le adauge din nou.

**Fix**:
- Commit `fc17bc6`: Eliminat adăugarea coloanelor pentru `acte_legislative` 
- Păstrat doar adăugarea pentru `articole` și indexes

### 3. Duplicate Column: ai_status (articole)

**Eroare**:
```
asyncpg.exceptions.DuplicateColumnError: column "ai_status" of relation 
"articole" already exists
```

**Cauză**: Schema inițială pentru `articole` (liniile 130-156) deja include TOATE coloanele AI:
- `metadate` (linia 146)
- `ai_status` (linia 147)
- `ai_processed_at` (linia 148)
- `ai_error` (linia 149)
- `issue_monitoring_id` (linia 150)

**Fix**:
- Commit `0e4c3d9`: Transformat migrația `0b4c93b0a665` să adauge DOAR indexuri
- Toate coloanele existau deja în schema inițială

### 4. Migration Order (domenii → articole_issues)

**Eroare**:
```
asyncpg.exceptions.UndefinedTableError: relation "legislatie.domenii" does not exist
```

**Cauză**: `5f128176a40b_add_issues_system` creează `articole_issues` cu Foreign Key către `domenii`, dar `5417c175c050_add_domenii_system` vine DUPĂ.

**Fix**:
- Commit `79a3bbd`: Inversat ordinea:
  - `5417c175c050` acum pointează la `aa4552000831` (înainte de issues)
  - `5f128176a40b` acum pointează la `5417c175c050` (după domenii)

## Lanț Final de Migrații

```
aa4552000831 (None)           → Initial schema from models
    ↓
5417c175c050 (aa4552000831)   → Add domenii system  
    ↓
5f128176a40b (5417c175c050)   → Add issues system and junction tables
    ↓
0b4c93b0a665 (5f128176a40b)   → Add AI processing indexes (NO columns)
    ↓
1007e30b0c57 (0b4c93b0a665)   → Fix metadate type to JSONB
```

## Deployment Final Command (O SINGURĂ COMANDĂ)

Pentru reinstalare completă de la 0:

```bash
ssh root@109.123.249.228 "
  cd /root/parser-law && \
  git fetch && \
  git reset --hard origin/main && \
  cd db_service && \
  docker compose down -v && \
  docker compose build --no-cache && \
  docker compose up -d && \
  sleep 10 && \
  docker exec legislatie_api alembic upgrade head
"
```

**Durata**: ~3-4 minute
- Build: ~80-90 secunde
- Migrations: ~5-10 secunde
- Sleep pentru postgres health check: 10 secunde

## Verificare Post-Deployment

```bash
# Health check
curl https://legislatie.issuemonitoring.ro/health

# Răspuns așteptat:
# {"status":"healthy","service":"Legislatie Database API","version":"2.1.1"}

# Test API
curl "https://legislatie.issuemonitoring.ro/api/v1/acte?limit=1"

# Răspuns așteptat (database gol după instalare):
# {"items":[],"total":0,"page":1,"size":1,"pages":0}
```

## Commits Relevante

1. **79a3bbd**: fix: correct migration order - domenii before articole_issues
2. **c2cabbb**: fix: correct full migration chain - single head  
3. **fc17bc6**: fix: remove duplicate columns from migration 0b4c93b0a665
4. **0e4c3d9**: fix: migration 0b4c93b0a665 to only add indexes - all columns exist

## Lecții Învățate

1. **Schema inițială trebuie să fie sursă de adevăr** - Orice migrație incrementală trebuie să verifice ce există deja
2. **Alembic tracking** - `alembic current` și `alembic history` ajută la debugging
3. **Testing migrations pe database gol** - Cel mai sigur mod de a verifica că totul funcționează
4. **Ordinea dependințelor** - Foreign keys trebuie create DUPĂ tabela la care referă
5. **Migration comments** - Comentarii clare despre ce adaugă fiecare migrație (ex: "NO-OP: columns already exist")

## Next Steps pentru Producție

După deployment success:
1. Import date din backup/export
2. Configurare scraper pentru colectare nouă
3. Setup monitoring și alerting
4. Backup schedule pentru date noi

## Warning Docker Compose

Versiunea 2.1.1+ produce warning:
```
the attribute `version` is obsolete, it will be ignored
```

**Non-blocking** - Docker Compose v2 nu mai necesită `version:` în YAML. Poate fi șters în viitor.
