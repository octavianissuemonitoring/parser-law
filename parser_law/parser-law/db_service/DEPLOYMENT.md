# Deployment Guide - Legislative Acts API

## Prerequisites

- Docker Desktop installed and running
- Python 3.11+ installed
- Git

## Quick Start

### 1. Start Database

```bash
cd db_service
docker-compose up -d postgres
```

Wait for PostgreSQL to be ready (about 10 seconds).

### 2. Run Migrations

```bash
# Set Python executable path
$PYTHON = "C:/Users/octavian/AppData/Local/Programs/Python/Python313/python.exe"

# Run Alembic migrations
$PYTHON -m alembic upgrade head
```

### 3. Import Data

```bash
# Option A: Via API (FastAPI must be running)
# Start API first: uvicorn app.main:app --reload
# Then POST to: http://localhost:8000/api/v1/acte/import

# Option B: Via CLI script
$PYTHON scripts/run_import.py --dir ../rezultate
```

### 4. Start API

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access API

- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Full Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# Run migrations inside container
docker-compose exec api alembic upgrade head

# Import data inside container
docker-compose exec api python scripts/run_import.py

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Database Access

### Via Docker

```bash
docker-compose exec postgres psql -U postgres -d legislatie_db
```

### Via pgAdmin

1. Access http://localhost:5050
2. Login: admin@admin.com / admin
3. Add server:
   - Host: postgres
   - Port: 5432
   - Database: legislatie_db
   - Username: postgres
   - Password: postgres

### Direct Connection

```bash
psql postgresql://postgres:postgres@localhost:5432/legislatie_db
```

## API Endpoints

### Acts (Acte Legislative)

- `GET /api/v1/acte` - List acts (with filters)
- `GET /api/v1/acte/{id}` - Get single act
- `GET /api/v1/acte/{id}/articole` - Get act with articles
- `POST /api/v1/acte` - Create act
- `PUT /api/v1/acte/{id}` - Update act
- `DELETE /api/v1/acte/{id}` - Delete act
- `GET /api/v1/acte/{id}/stats` - Get statistics
- `POST /api/v1/acte/import` - Import from CSV

### Articles (Articole)

- `GET /api/v1/articole` - List articles (with filters)
- `GET /api/v1/articole/{id}` - Get single article
- `GET /api/v1/articole/{id}/with-act` - Get article with act
- `POST /api/v1/articole` - Create article
- `PUT /api/v1/articole/{id}` - Update article
- `PATCH /api/v1/articole/{id}/labels` - Update LLM labels
- `POST /api/v1/articole/batch-update-labels` - Bulk update labels
- `DELETE /api/v1/articole/{id}` - Delete article
- `GET /api/v1/articole/search/text` - Full-text search

## Database Schema

### Tables

- `legislatie.acte_legislative` - Legislative acts metadata
- `legislatie.articole` - Articles from acts

### Relationships

- One ActLegislativ has many Articole (CASCADE delete)
- Foreign key: `articole.act_id` → `acte_legislative.id`

### Indexes

- `acte_legislative`: tip_act, an_act, mof_an
- `articole`: act_id, (act_id, ordine), (act_id, articol_nr)

## Import Process

### What gets imported?

1. **CSV files** from `rezultate/` directory
2. **MD files** (HTML content) with matching names
3. **Act metadata** from first CSV row
4. **All articles** from CSV rows (with text_articol)

### Deduplication

- Acts are checked by `url_legislatie`
- Existing acts are skipped
- Import continues with next file

### Statistics

Import returns:
- Total files found
- Acts imported
- Acts skipped
- Articles imported
- Errors (with details)

## Troubleshooting

### Docker issues

```bash
# Check if Docker is running
docker ps

# Restart services
docker-compose restart

# View logs
docker-compose logs -f postgres
docker-compose logs -f api
```

### Database issues

```bash
# Check if database exists
docker-compose exec postgres psql -U postgres -l

# Recreate database
docker-compose exec postgres psql -U postgres -c "DROP DATABASE IF EXISTS legislatie_db;"
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE legislatie_db;"

# Run migrations again
alembic upgrade head
```

### Migration issues

```bash
# Check current migration version
alembic current

# Show migration history
alembic history

# Downgrade one version
alembic downgrade -1

# Upgrade to latest
alembic upgrade head
```

### Import issues

```bash
# Check if rezultate/ has CSV files
ls ../rezultate/*.csv

# Run import with verbose logging
python scripts/run_import.py --dir ../rezultate

# Check database for imported acts
docker-compose exec postgres psql -U postgres -d legislatie_db -c "SELECT COUNT(*) FROM legislatie.acte_legislative;"
```

## Environment Variables

Create `.env` file in `db_service/` directory:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/legislatie_db
DB_SCHEMA=legislatie

# API
API_TITLE=Legislative Acts API
API_VERSION=1.0.0

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

## Testing

### Manual Testing

1. Start API: `uvicorn app.main:app --reload`
2. Open Swagger: http://localhost:8000/docs
3. Try endpoints:
   - POST `/api/v1/acte/import` - Import data
   - GET `/api/v1/acte` - List acts
   - GET `/api/v1/acte/{id}/stats` - Statistics

### Database Queries

```sql
-- Count acts
SELECT COUNT(*) FROM legislatie.acte_legislative;

-- Count articles
SELECT COUNT(*) FROM legislatie.articole;

-- Acts with article count
SELECT 
    a.id,
    a.tip_act,
    a.nr_act,
    a.an_act,
    a.titlu_act,
    COUNT(art.id) as articole_count
FROM legislatie.acte_legislative a
LEFT JOIN legislatie.articole art ON art.act_id = a.id
GROUP BY a.id
ORDER BY a.id;

-- Articles with labels
SELECT 
    COUNT(*) FILTER (WHERE issue IS NOT NULL OR explicatie IS NOT NULL) as with_labels,
    COUNT(*) as total
FROM legislatie.articole;
```

## Production Deployment

### Security

1. Change default passwords in `docker-compose.yml`
2. Use environment variables for secrets
3. Enable SSL/TLS for PostgreSQL
4. Configure firewall rules
5. Use reverse proxy (nginx) for API

### Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres legislatie_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres legislatie_db < backup.sql
```

### Monitoring

- Check API logs: `docker-compose logs -f api`
- Monitor database: `docker stats`
- Health check: `curl http://localhost:8000/health`

## Next Steps

1. **Add Authentication** - JWT tokens for API access
2. **Add Tests** - Unit and integration tests with pytest
3. **Add Caching** - Redis for frequently accessed data
4. **Add Search** - Full-text search with PostgreSQL tsvector
5. **Add LLM Integration** - Automate label generation
6. **Add Versioning** - Track changes to acts/articles
7. **Add Export** - Export to PDF, DOCX, etc.
