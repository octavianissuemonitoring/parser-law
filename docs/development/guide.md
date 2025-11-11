# Development Guide - Parser Law

> **Goal**: Enable multiple developers to work on this codebase without configuration surprises or inconsistencies.

Last Updated: 2025-11-11  
Version: 1.0.0

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Setup](#environment-setup)
3. [Architecture Overview](#architecture-overview)
4. [Coding Standards](#coding-standards)
5. [Database Conventions](#database-conventions)
6. [API Conventions](#api-conventions)
7. [Deployment Standards](#deployment-standards)
8. [Testing Requirements](#testing-requirements)
9. [Troubleshooting](#troubleshooting)

---

## 1. Quick Start

### Prerequisites

```powershell
# Required tools
python --version  # 3.11+
docker --version  # 20.10+
git --version     # 2.30+
```

### First Time Setup (5 minutes)

```powershell
# 1. Clone repository
git clone https://github.com/octavianissuemonitoring/parser-law.git
cd parser-law

# 2. Copy environment template
cp .env.example .env
# Edit .env with your local credentials

# 3. Start local development environment
docker-compose -f docker-compose.dev.yml up -d

# 4. Install Python dependencies
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 5. Initialize database
docker exec -i parser-law-postgres psql -U parser_user -d monitoring_platform < db_service/init.sql

# 6. Verify setup
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "1.0.0"}
```

---

## 2. Environment Setup

### 2.1 Environment Variables

**CRITICAL**: Always use `.env` file, never hardcode credentials.

Create `.env` from `.env.example`:

```bash
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=monitoring_platform
POSTGRES_USER=parser_user
POSTGRES_PASSWORD=your_secure_password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_VERSION=1.0.0
LOG_LEVEL=INFO

# VPS Configuration (production only)
VPS_HOST=77.237.235.158
VPS_USER=root
VPS_PATH=/opt/parser-law

# Docker Container Names (must match docker-compose.yml)
CONTAINER_API=legislatie_api
CONTAINER_DB=legislatie_postgres
CONTAINER_SCHEDULER=legislatie_scheduler
```

### 2.2 Local vs VPS Environment

| Aspect | Local Dev | VPS Production |
|--------|-----------|----------------|
| **Database Host** | `localhost` | `legislatie_postgres` (container name) |
| **Database Port** | `5432` | `5432` (internal) |
| **API Port** | `8000` | `8000` (nginx → 80) |
| **Paths** | `./` (relative) | `/opt/parser-law` (absolute) |
| **Logs** | `./logs/` | `/opt/parser-law/logs/` |
| **Backups** | `./backups/` | `/opt/parser-law/backups/` |

**Rule**: Code must work in BOTH environments without changes.

### 2.3 Docker Compose Standards

**Local Development**: `docker-compose.dev.yml`
```yaml
version: '3.8'
services:
  postgres:
    container_name: parser-law-postgres
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db_service/init.sql:/docker-entrypoint-initdb.d/init.sql

  api:
    container_name: parser-law-api
    build:
      context: ./db_service
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    depends_on:
      - postgres
    volumes:
      - ./db_service/app:/app/app  # Hot reload

volumes:
  postgres_data:
```

**VPS Production**: `docker-compose.yml` (already exists)
- Same structure but with production-specific configs
- No hot reload volumes
- Nginx reverse proxy included

---

## 3. Architecture Overview

### 3.1 Project Structure (Standard Layout)

```
parser-law/
├── .env.example              # Environment template (NEVER commit .env)
├── .gitignore                # Must include .env, __pycache__, logs/
├── requirements.txt          # Python dependencies (pinned versions)
├── docker-compose.dev.yml    # Local development
├── docker-compose.yml        # VPS production
│
├── db_service/               # API & Database Layer
│   ├── app/
│   │   ├── main.py           # FastAPI app entry
│   │   ├── config.py         # Settings (from env vars)
│   │   ├── models/           # SQLAlchemy models
│   │   ├── routes/           # API endpoints
│   │   ├── services/         # Business logic
│   │   └── utils/            # Helpers
│   ├── alembic/              # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
│
├── scripts/                  # Deployment & automation
│   ├── deploy-vps.sh
│   ├── backup-db.sh
│   └── restore-db.sh
│
├── tests/                    # Unit & integration tests
│   ├── test_parsers.py
│   ├── test_api.py
│   └── test_services.py
│
├── docs/                     # Documentation
│   ├── API_DOCUMENTATION.md
│   ├── DATABASE_DOCUMENTATION.md
│   └── DEPLOYMENT.md
│
└── logs/                     # Application logs (gitignored)
```

### 3.2 Database Schema (PostgreSQL)

**Schema**: `legislatie` (NOT public!)

**Tables** (12 total):
```sql
legislatie.acte_legislative       -- Main legal acts
legislatie.articole               -- Articles (hierarchical)
legislatie.categories             -- Categories (soft-delete)
legislatie.acte_categories        -- M:N junction
legislatie.issues                 -- Quality issues
legislatie.acte_issues            -- Act issues junction
legislatie.articole_issues        -- Article issues junction
legislatie.linkuri_legislatie     -- Source links
legislatie.diffs                  -- Version tracking
legislatie.diff_sections          -- Diff details
legislatie.ai_labeling_queue      -- AI processing queue
legislatie.ai_labeling_results    -- AI results
```

**Important**: ALL queries must use `legislatie.table_name`, NOT `public.table_name`.

### 3.3 API Layer (FastAPI)

**Base URL**: `http://localhost:8000` (dev) or `http://legislatie.issuemonitoring.ro` (prod)

**Endpoint Structure**:
```
/health                           # Health check
/api/v1/acte                      # Acts CRUD
/api/v1/articole                  # Articles CRUD
/api/v1/categories                # Categories management
/api/v1/ai                        # AI processing
/api/v1/export                    # Data export
```

**Rule**: Every route file must import from `app.config` for DB connection.

---

## 4. Coding Standards

### 4.1 Python Style (PEP 8 + Extensions)

**Use Black formatter** (line length 100):
```powershell
pip install black
black --line-length 100 .
```

**Use isort for imports**:
```powershell
pip install isort
isort --profile black .
```

**Use Flake8 for linting**:
```powershell
pip install flake8
flake8 --max-line-length 100 --extend-ignore E203,W503 .
```

### 4.2 Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| **Files** | snake_case | `metadata_extractor.py` |
| **Classes** | PascalCase | `ActeLegislative`, `MetadataExtractor` |
| **Functions** | snake_case | `extract_metadata()`, `parse_html()` |
| **Variables** | snake_case | `act_id`, `total_count` |
| **Constants** | UPPER_SNAKE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| **Database Tables** | snake_case | `acte_legislative`, `articole` |
| **Database Columns** | snake_case | `created_at`, `is_deleted` |
| **API Endpoints** | kebab-case | `/acte-legislative`, `/export-for-analysis` |

### 4.3 Import Order (isort profile)

```python
# 1. Standard library
import json
import logging
from datetime import datetime
from typing import Optional, List

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

# 3. Local application
from app.config import get_db
from app.models.acte import ActeLegislative
from app.services.metadata_extractor import MetadataExtractor
```

### 4.4 Documentation Standards

**Every function must have docstring**:
```python
def extract_metadata(html_content: str) -> ActMetadata:
    """
    Extract metadata from HTML content of a legal act.
    
    Args:
        html_content: Raw HTML string from MOF website
        
    Returns:
        ActMetadata: Parsed metadata (tip_act, numar, an, data_publicarii)
        
    Raises:
        ValueError: If required metadata cannot be extracted
        
    Example:
        >>> html = '<div class="article">LEGE nr. 123...</div>'
        >>> metadata = extract_metadata(html)
        >>> metadata.tip_act
        'LEGE'
    """
    # Implementation...
```

**Every API endpoint must have OpenAPI schema**:
```python
@router.get("/acte/{act_id}", response_model=ActeResponse)
async def get_act(
    act_id: int,
    include_articole: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get a single legal act by ID.
    
    - **act_id**: Database ID of the act
    - **include_articole**: Include nested articles (default: False)
    
    Returns the act with all metadata and optionally articles.
    """
```

### 4.5 Error Handling Standards

**Use custom exceptions**:
```python
# app/utils/exceptions.py
class ParserError(Exception):
    """Base exception for parsing errors"""
    pass

class MetadataExtractionError(ParserError):
    """Failed to extract required metadata"""
    pass

class DatabaseConnectionError(Exception):
    """Failed to connect to database"""
    pass
```

**Use logging, not print()**:
```python
import logging

logger = logging.getLogger(__name__)

# Good
logger.info(f"Processing act {act_id}")
logger.error(f"Failed to parse: {error}", exc_info=True)

# Bad
print(f"Processing act {act_id}")  # Never use print()
```

### 4.6 Configuration Management

**ALL settings in config.py**:
```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "monitoring_platform"
    postgres_user: str
    postgres_password: str
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton"""
    return Settings()

# Usage in code
from app.config import get_settings

settings = get_settings()
DATABASE_URL = f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
```

**NEVER hardcode**:
```python
# BAD - Hardcoded
DATABASE_URL = "postgresql://parser_user:password@localhost:5432/monitoring_platform"

# GOOD - From config
from app.config import get_settings
settings = get_settings()
DATABASE_URL = f"postgresql://{settings.postgres_user}:..."
```

---

## 5. Database Conventions

### 5.1 Connection Standards

**Always use schema prefix**:
```python
# GOOD
result = db.execute(text("SELECT * FROM legislatie.acte_legislative WHERE id = :id"), {"id": act_id})

# BAD - Will fail if search_path is not set
result = db.execute(text("SELECT * FROM acte_legislative WHERE id = :id"), {"id": act_id})
```

**Set search_path in connection string**:
```python
DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db}?options=-c%20search_path=legislatie,public"
```

### 5.2 Migration Standards (Alembic)

**Always use Alembic for schema changes**:
```powershell
# Create new migration
cd db_service
alembic revision --autogenerate -m "Add categories table"

# Review generated migration in alembic/versions/
# Edit if needed

# Apply migration locally
alembic upgrade head

# Test thoroughly, then apply on VPS
ssh root@77.237.235.158
cd /opt/parser-law/db_service
docker exec legislatie_api alembic upgrade head
```

**Migration naming**:
- `add_table_name` - New table
- `alter_column_name` - Column modification
- `add_index_name` - Index creation
- `drop_constraint_name` - Constraint removal

### 5.3 Query Standards

**Use SQLAlchemy ORM (preferred)**:
```python
from sqlalchemy.orm import Session
from app.models.acte import ActeLegislative

def get_act_by_id(db: Session, act_id: int) -> ActeLegislative:
    return db.query(ActeLegislative).filter(ActeLegislative.id == act_id).first()
```

**Use raw SQL only for complex queries**:
```python
from sqlalchemy import text

def get_acts_with_stats(db: Session, limit: int = 10):
    query = text("""
        SELECT 
            a.id, 
            a.titlu, 
            COUNT(art.id) as articole_count
        FROM legislatie.acte_legislative a
        LEFT JOIN legislatie.articole art ON art.act_id = a.id
        GROUP BY a.id, a.titlu
        LIMIT :limit
    """)
    return db.execute(query, {"limit": limit}).fetchall()
```

### 5.4 Backup Standards

**Daily automated backups** (cron on VPS):
```bash
# /opt/parser-law/scripts/backup-db.sh
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/parser-law/backups/daily"
docker exec legislatie_postgres pg_dump -U parser_user -d monitoring_platform > "$BACKUP_DIR/db_$DATE.sql"

# Keep only last 7 days
find "$BACKUP_DIR" -name "db_*.sql" -mtime +7 -delete
```

**Before major changes** (manual):
```bash
# Create tagged backup
TAG="v1.0-stable"
BACKUP_DIR="/opt/parser-law/backups/$TAG"
mkdir -p "$BACKUP_DIR"
docker exec legislatie_postgres pg_dump -U parser_user -d monitoring_platform > "$BACKUP_DIR/database_backup.sql"
```

---

## 6. API Conventions

### 6.1 Endpoint Design

**RESTful structure**:
```
GET    /api/v1/acte              # List all acts
GET    /api/v1/acte/{id}         # Get single act
POST   /api/v1/acte              # Create act
PUT    /api/v1/acte/{id}         # Update act (full)
PATCH  /api/v1/acte/{id}         # Update act (partial)
DELETE /api/v1/acte/{id}         # Delete act
```

**Query parameters for filtering**:
```
GET /api/v1/acte?tip_act=LEGE&an=2024&limit=50&offset=0
GET /api/v1/acte/{id}?include=articole,categories&format=json
```

### 6.2 Response Standards

**Success response (200)**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "titlu": "LEGE nr. 123/2024",
    "created_at": "2024-11-10T15:30:00Z"
  },
  "metadata": {
    "total_count": 1,
    "page": 1,
    "limit": 50
  }
}
```

**Error response (4xx/5xx)**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid act_id parameter",
    "details": {
      "field": "act_id",
      "expected": "integer",
      "received": "string"
    }
  }
}
```

### 6.3 Versioning

**URL versioning** (current: v1):
```
/api/v1/acte  # Current version
/api/v2/acte  # Future breaking changes
```

**Deprecation policy**:
- Announce 3 months before removal
- Add `X-Deprecated` header
- Provide migration guide

---

## 7. Deployment Standards

### 7.1 Git Workflow

**Branch strategy**:
```
master          # Production-ready code (protected)
develop         # Integration branch
feature/xyz     # New features
bugfix/xyz      # Bug fixes
hotfix/xyz      # Urgent production fixes
```

**Commit message format**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance (dependencies, config)

**Example**:
```
feat(categories): Add soft-delete sync strategy

Implement category soft-delete handling to prevent
cascade deletion of junctions when category is deleted.

Closes #42
```

### 7.2 Deployment Checklist

**Before deployment**:
```powershell
# 1. Run tests
pytest tests/ -v

# 2. Check linting
flake8 .

# 3. Format code
black --check .

# 4. Update version
# Edit app/config.py: API_VERSION = "1.1.0"

# 5. Create migration (if DB changes)
alembic revision --autogenerate -m "Description"

# 6. Commit and tag
git add .
git commit -m "release: v1.1.0"
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin master --tags
```

**VPS deployment**:
```bash
# SSH to VPS
ssh root@77.237.235.158

# Navigate to app directory
cd /opt/parser-law

# Pull latest code
git fetch --all
git checkout v1.1.0

# Apply migrations
cd db_service
docker exec legislatie_api alembic upgrade head

# Restart services
docker-compose restart api

# Verify health
curl http://localhost:8000/health
```

### 7.3 Rollback Procedure

**Fast rollback** (< 5 minutes):
```bash
# 1. Checkout previous version
cd /opt/parser-law
git checkout v1.0-stable

# 2. Restore database
bash backups/v1.0-stable/restore.sh

# 3. Restart services
docker-compose restart

# 4. Verify
curl http://localhost:8000/health
```

See: `ROLLBACK_INSTRUCTIONS.md`

---

## 8. Testing Requirements

### 8.1 Test Structure

```
tests/
├── conftest.py              # Pytest fixtures
├── test_parsers/
│   ├── test_metadata_extractor.py
│   ├── test_html_parser.py
│   └── test_hybrid_parser.py
├── test_api/
│   ├── test_acte_endpoints.py
│   ├── test_categories_endpoints.py
│   └── test_health.py
└── test_services/
    ├── test_import_service.py
    └── test_query_builder.py
```

### 8.2 Test Coverage Requirements

**Minimum coverage**: 80% for new code

```powershell
# Run tests with coverage
pytest --cov=app --cov-report=html tests/

# View coverage report
# Open htmlcov/index.html
```

### 8.3 Test Examples

**Unit test (metadata extraction)**:
```python
# tests/test_parsers/test_metadata_extractor.py
import pytest
from metadata_extractor import MetadataExtractor, ActMetadata

def test_extract_lege_metadata():
    """Test extraction of LEGE metadata"""
    html = """
    <div class="article">
        <h1>LEGE nr. 123 din 15 octombrie 2024</h1>
        <p>Publicat în M. Of. nr. 1000 din 20 octombrie 2024</p>
    </div>
    """
    
    extractor = MetadataExtractor()
    metadata = extractor.extract(html)
    
    assert metadata.tip_act == "LEGE"
    assert metadata.numar == "123"
    assert metadata.an == 2024
    assert metadata.data_publicarii.year == 2024
    assert metadata.data_publicarii.month == 10
    assert metadata.data_publicarii.day == 20
```

**Integration test (API endpoint)**:
```python
# tests/test_api/test_acte_endpoints.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_acte_list():
    """Test GET /api/v1/acte returns list"""
    response = client.get("/api/v1/acte?limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 10
```

---

## 9. Troubleshooting

### 9.1 Common Issues

**Issue**: `relation "acte_legislative" does not exist`  
**Cause**: Missing schema prefix or search_path not set  
**Fix**:
```python
# Add schema prefix
db.execute(text("SELECT * FROM legislatie.acte_legislative"))

# OR set search_path in connection string
DATABASE_URL += "?options=-c%20search_path=legislatie,public"
```

---

**Issue**: Docker container cannot connect to database  
**Cause**: Using `localhost` instead of container name  
**Fix**:
```yaml
# docker-compose.yml
environment:
  # BAD
  DATABASE_HOST: localhost
  
  # GOOD
  DATABASE_HOST: legislatie_postgres  # Container name
```

---

**Issue**: VPS deployment fails with permission error  
**Cause**: Incorrect file ownership or permissions  
**Fix**:
```bash
# Set correct ownership
chown -R root:root /opt/parser-law

# Set correct permissions
chmod -R 755 /opt/parser-law
chmod 600 /opt/parser-law/.env  # Sensitive files
```

---

**Issue**: Alembic migration fails with "target database is not up to date"  
**Cause**: Migration history mismatch  
**Fix**:
```bash
# Check current version
alembic current

# Show migration history
alembic history

# Stamp database to specific version (use with caution)
alembic stamp head
```

---

**Issue**: API returns 500 with "connection refused"  
**Cause**: Database container not running or wrong credentials  
**Fix**:
```bash
# Check container status
docker ps | grep postgres

# Check logs
docker logs legislatie_postgres

# Verify credentials in .env match docker-compose.yml
cat .env | grep POSTGRES
```

---

### 9.2 Debug Mode

**Enable debug logging**:
```python
# app/config.py
LOG_LEVEL = "DEBUG"  # In .env

# app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Enable SQL query logging**:
```python
# app/database.py
engine = create_engine(
    DATABASE_URL,
    echo=True  # Print all SQL queries
)
```

---

## 10. Resources

### Internal Documentation
- `DATABASE_DOCUMENTATION.md` - Complete schema reference
- `CODE_REVIEW_AND_REFACTORING.md` - Code analysis and refactoring plan
- `ARCHITECTURE_COMPARISON.md` - Before/After architecture
- `ROLLBACK_INSTRUCTIONS.md` - Emergency rollback procedures
- `API_DOCUMENTATION.md` - Full API reference (in db_service/)

### External Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/en/latest/)
- [PostgreSQL 15 Docs](https://www.postgresql.org/docs/15/)
- [Docker Compose](https://docs.docker.com/compose/)

### Team Communication
- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code review required before merge
- **Slack/Discord**: Real-time discussions (if available)
- **Weekly Sync**: Architecture decisions and planning

---

## 11. Contributing

### Pull Request Process

1. **Create feature branch**: `git checkout -b feature/your-feature`
2. **Write tests**: Achieve 80%+ coverage
3. **Format code**: Run Black and isort
4. **Update docs**: If API or schema changes
5. **Commit**: Follow commit message format
6. **Push**: `git push origin feature/your-feature`
7. **Create PR**: Add description and link to issue
8. **Code review**: Address feedback
9. **Merge**: Squash and merge to develop

### Code Review Checklist

- [ ] Tests pass (`pytest tests/`)
- [ ] Linting passes (`flake8 .`)
- [ ] Code formatted (`black --check .`)
- [ ] Documentation updated
- [ ] No hardcoded credentials
- [ ] Schema prefix used (`legislatie.table_name`)
- [ ] Error handling implemented
- [ ] Logging added (not print)
- [ ] Environment variables in `.env.example`

---

## Appendix: Configuration Files Reference

### `.env.example`
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=monitoring_platform
POSTGRES_USER=parser_user
POSTGRES_PASSWORD=change_me_in_production

# API
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# VPS (production only)
VPS_HOST=77.237.235.158
VPS_USER=root
VPS_PATH=/opt/parser-law
```

### `.editorconfig`
```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4
max_line_length = 100

[*.{yml,yaml}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
```

### `pyproject.toml` (Black + isort config)
```toml
[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100
```

### `.flake8`
```ini
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    venv,
    alembic/versions
```

---

**Last Updated**: 2025-11-11  
**Maintainer**: octavian@issuemonitoring.ro  
**Version**: 1.0.0

---

✅ **Next Steps After Reading This Guide**:
1. Run Quick Start setup (5 min)
2. Read `DATABASE_DOCUMENTATION.md` for schema understanding
3. Review `CODE_REVIEW_AND_REFACTORING.md` for current architecture
4. Set up local development environment with `docker-compose.dev.yml`
5. Make your first commit following the standards!
