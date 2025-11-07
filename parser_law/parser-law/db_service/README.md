# Database Service - API pentru Acte Legislative

Microserviciu FastAPI pentru gestionarea actelor legislative în PostgreSQL.

## Structura Proiectului

```
db_service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── database.py          # DB connection
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API routes
│   └── services/            # Business logic
├── alembic/                 # Database migrations
├── tests/                   # Tests
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Quick Start

### 1. Setup Environment

```bash
# Creează virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalează dependencies
pip install -r requirements.txt
```

### 2. Start Database

```bash
# Start PostgreSQL cu Docker
docker-compose up -d postgres

# Rulează migrations
alembic upgrade head
```

### 3. Run API

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Access API

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Create Migration

```bash
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Import Data

```bash
python -m app.services.import_service --dir ../rezultate/
```

## API Endpoints

### Acte Legislative

- `POST /api/v1/acte/import` - Import act din CSV/MD
- `GET /api/v1/acte` - List acte (paginated)
- `GET /api/v1/acte/{id}` - Get act by ID
- `GET /api/v1/acte/{id}/articole` - Get articole pentru act
- `PUT /api/v1/acte/{id}` - Update act
- `DELETE /api/v1/acte/{id}` - Delete act

### Articole

- `GET /api/v1/articole` - List articole (paginated)
- `GET /api/v1/articole/{id}` - Get articol by ID
- `PUT /api/v1/articole/{id}/labels` - Update issue/explicatie
- `POST /api/v1/articole/batch-update` - Batch update labels
- `GET /api/v1/articole/search` - Search articole

### Health & Info

- `GET /health` - Health check
- `GET /api/v1/info` - API info

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/monitoring_platform
DB_SCHEMA=legislatie

# API
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Logging
LOG_LEVEL=INFO
```

## Tech Stack

- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
- **Database**: PostgreSQL 15+
- **Validation**: Pydantic v2
- **Testing**: pytest + httpx

## License

MIT
