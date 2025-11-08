# Legislative Acts API - FastAPI Microservice

REST API microservice pentru gestionarea actelor legislative românești și articolelor acestora.

## 🚀 Features

- **FastAPI** - Modern, fast web framework cu validare automată
- **SQLAlchemy 2.0** - ORM async pentru PostgreSQL
- **Alembic** - Database migrations
- **Pydantic v2** - Validare date cu type hints
- **PostgreSQL 15** - Database cu suport pentru full-text search
- **Docker** - Containerizare completă (API + PostgreSQL + pgAdmin)
- **Async/Await** - Non-blocking I/O pentru performanță
- **Import Service** - Import automat din CSV/Markdown

## 📁 Project Structure

```
db_service/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependencies (session, pagination)
│   │   └── routes/
│   │       ├── acte.py          # CRUD pentru acte legislative
│   │       └── articole.py      # CRUD pentru articole
│   ├── models/
│   │   ├── act_legislativ.py   # Model ActLegislativ
│   │   └── articol.py           # Model Articol
│   ├── schemas/
│   │   ├── act_schema.py        # Pydantic schemas pentru Act
│   │   └── articol_schema.py    # Pydantic schemas pentru Articol
│   ├── services/
│   │   └── import_service.py    # Import CSV/MD → Database
│   ├── config.py                # Settings cu Pydantic
│   ├── database.py              # AsyncSession setup
│   └── main.py                  # FastAPI app
├── alembic/
│   ├── versions/                # Database migrations
│   └── env.py                   # Alembic config (async)
├── scripts/
│   └── run_import.py            # CLI pentru import
├── docker-compose.yml           # Docker services
├── Dockerfile                   # API container
├── requirements.txt             # Python dependencies
├── alembic.ini                  # Alembic config
├── DEPLOYMENT.md                # Deployment guide
└── README.md                    # This file
```

## 🚀 Quick Start

### 1. Start PostgreSQL

```bash
cd db_service
docker-compose up -d postgres
```

### 2. Run Migrations

```bash
python -m alembic upgrade head
```

### 3. Import Data

```bash
python scripts/run_import.py --dir ../rezultate
```

### 4. Start API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access API

- **Swagger**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## 📚 Full Documentation

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete setup, deployment, and troubleshooting guide.

## 🔌 API Endpoints Summary

### Acts: `/api/v1/acte`
- List, Get, Create, Update, Delete
- **Import from CSV**: `POST /api/v1/acte/import`
- Statistics: `GET /api/v1/acte/{id}/stats`

### Articles: `/api/v1/articole`
- List, Get, Create, Update, Delete
- **Update LLM labels**: `PATCH /api/v1/articole/{id}/labels`
- **Bulk updates**: `POST /api/v1/articole/batch-update-labels`
- **Search**: `GET /api/v1/articole/search/text`

## 📊 Database Schema

- **`acte_legislative`**: Act metadata (17 fields)
- **`articole`**: Articles (20 fields) with FK to acts
- **Relationship**: One-to-Many with CASCADE delete
- **Indexes**: Optimized for common queries

## 🔧 Technology Stack

- **Python 3.11+**
- **FastAPI 0.104** - Web framework
- **SQLAlchemy 2.0** - Async ORM
- **Alembic 1.17** - Migrations
- **Pydantic 2.5** - Validation
- **PostgreSQL 15** - Database
- **asyncpg 0.30** - Async PostgreSQL driver
- **Docker** - Containerization

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

## 🐳 Docker Deployment

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# Import data
docker-compose exec api python scripts/run_import.py

# View logs
docker-compose logs -f api
```

## 🧪 Testing

Open Swagger UI: http://localhost:8000/docs

Try these endpoints:
1. `POST /api/v1/acte/import` - Import CSV files
2. `GET /api/v1/acte` - List acts
3. `GET /api/v1/acte/{id}/stats` - View statistics
4. `GET /api/v1/articole/search/text?q=energie` - Search articles

## 📝 License

MIT

---

**Built with ❤️ using FastAPI, SQLAlchemy, and PostgreSQL**
