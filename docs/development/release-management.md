# Release Management & Multi-Version Deployment

**Problem**: Doar ultima versiune poate fi instalată. Nu pot fi mai multe versiuni stabile în producție simultan.

**Solution**: Semantic versioning + Docker tags + multi-environment deployment strategy.

**Use Case**: 
- Client A → rulează v1.2.0 (stabil, testat)
- Client B → rulează v1.3.1 (versiune nouă cu feature-uri extra)
- Staging → rulează v1.4.0-rc.1 (testing pentru release)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ GitHub Repository (octavianissuemonitoring/parser-law)      │
├─────────────────────────────────────────────────────────────┤
│ master branch                                                │
│   └─ v1.2.0 (tag) ──────────> Docker: parser-law:1.2.0     │
│   └─ v1.3.1 (tag) ──────────> Docker: parser-law:1.3.1     │
│   └─ v1.4.0 (tag) ──────────> Docker: parser-law:1.4.0     │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Docker Hub (or GitHub Container Registry)                   │
├─────────────────────────────────────────────────────────────┤
│ octavianissuemonitoring/parser-law:1.2.0                    │
│ octavianissuemonitoring/parser-law:1.3.1                    │
│ octavianissuemonitoring/parser-law:1.4.0                    │
│ octavianissuemonitoring/parser-law:latest → 1.4.0          │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Deployment Environments                                      │
├─────────────────────────────────────────────────────────────┤
│ VPS 1 (Client A) → docker-compose.v1.2.0.yml               │
│   image: parser-law:1.2.0                                   │
│   port: 8000                                                 │
│                                                              │
│ VPS 2 (Client B) → docker-compose.v1.3.1.yml               │
│   image: parser-law:1.3.1                                   │
│   port: 8000                                                 │
│                                                              │
│ VPS 3 (Staging) → docker-compose.v1.4.0.yml                │
│   image: parser-law:1.4.0                                   │
│   port: 8000                                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Semantic Versioning

**Format**: `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`

### Version Components

```
v1.3.2-rc.1+20240312
│ │ │  │      │
│ │ │  │      └─ Build metadata (optional)
│ │ │  └──────── Pre-release (rc, alpha, beta)
│ │ └─────────── PATCH: Bug fixes (backwards compatible)
│ └───────────── MINOR: New features (backwards compatible)
└─────────────── MAJOR: Breaking changes
```

### Version Increments

| Change Type | Example | Version Change |
|-------------|---------|----------------|
| **Breaking API change** | Remove endpoint | 1.2.3 → **2.0.0** |
| **New feature** | Add categories API | 1.2.3 → **1.3.0** |
| **Bug fix** | Fix parser encoding | 1.2.3 → **1.2.4** |
| **Release candidate** | Testing v1.3.0 | 1.2.3 → **1.3.0-rc.1** |
| **Hotfix** | Emergency fix | 1.2.3 → **1.2.4** |

### Examples

```bash
v1.0.0          # First stable release
v1.1.0          # Added categories feature
v1.1.1          # Fixed metadata extraction bug
v1.2.0-rc.1     # Release candidate for v1.2.0
v1.2.0-rc.2     # Second release candidate (fixed issues)
v1.2.0          # Stable release after testing
v2.0.0          # Breaking change: New database schema
```

---

## Docker Image Tagging Strategy

### Build Multiple Tags

Each release gets **3 Docker image tags**:

```bash
# Full version (specific)
docker build -t parser-law:1.3.0 .

# Minor version (rolling)
docker tag parser-law:1.3.0 parser-law:1.3

# Major version (rolling)
docker tag parser-law:1.3.0 parser-law:1

# Latest (rolling)
docker tag parser-law:1.3.0 parser-law:latest
```

### Tag Behavior

| Image Tag | Purpose | Updates When |
|-----------|---------|--------------|
| `parser-law:1.3.0` | **Immutable** - specific version | Never (permanent) |
| `parser-law:1.3` | Rolling minor - latest 1.3.x | New 1.3.x patch |
| `parser-law:1` | Rolling major - latest 1.x.x | New 1.x.0 release |
| `parser-law:latest` | Latest stable | New stable release |

### Use Cases

```yaml
# Production (Client A): Never auto-update
services:
  api:
    image: parser-law:1.2.0  # Stays on 1.2.0 forever
    
# Production (Client B): Auto-update patches only
services:
  api:
    image: parser-law:1.3  # Gets 1.3.1, 1.3.2 automatically

# Staging: Always latest
services:
  api:
    image: parser-law:latest  # Gets every new release
```

---

## Release Workflow

### Step 1: Create Release Branch

```powershell
# From develop (after features merged)
git checkout develop
git pull origin develop

# Create release branch
git checkout -b release/1.3.0

# Bump version in files
# - db_service/app/main.py (version string)
# - pyproject.toml (version field)
# - CHANGELOG.md (add release notes)

git add .
git commit -m "chore: Bump version to 1.3.0"
git push origin release/1.3.0
```

### Step 2: Test Release Candidate

```powershell
# Build Docker image with RC tag
cd db_service
docker build -t parser-law:1.3.0-rc.1 .

# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d

# Run tests
pytest tests/
pytest tests/integration/

# Manual testing
# - Check API docs
# - Test all endpoints
# - Verify database migrations
```

### Step 3: Merge to Master & Tag

```powershell
# If tests pass, merge to master
git checkout master
git merge --no-ff release/1.3.0
git tag -a v1.3.0 -m "Release v1.3.0: Add categories feature

Changes:
- Add categories API endpoints
- Improve metadata extraction
- Fix parser encoding issues
- Update database schema

Breaking changes: None
"

git push origin master
git push origin v1.3.0

# Merge back to develop
git checkout develop
git merge --no-ff release/1.3.0
git push origin develop

# Delete release branch
git branch -d release/1.3.0
git push origin --delete release/1.3.0
```

### Step 4: Build & Push Docker Images

```powershell
# Checkout the tag
git checkout v1.3.0

# Build with multiple tags
cd db_service
docker build -t octavianissuemonitoring/parser-law:1.3.0 .
docker tag octavianissuemonitoring/parser-law:1.3.0 octavianissuemonitoring/parser-law:1.3
docker tag octavianissuemonitoring/parser-law:1.3.0 octavianissuemonitoring/parser-law:1
docker tag octavianissuemonitoring/parser-law:1.3.0 octavianissuemonitoring/parser-law:latest

# Push all tags
docker push octavianissuemonitoring/parser-law:1.3.0
docker push octavianissuemonitoring/parser-law:1.3
docker push octavianissuemonitoring/parser-law:1
docker push octavianissuemonitoring/parser-law:latest
```

### Step 5: Deploy to Production

```powershell
# On VPS (choose version)
ssh root@vps-client-a
cd /opt/parser-law

# Update docker-compose.yml to specific version
nano docker-compose.yml
# Change: image: parser-law:1.2.0 → parser-law:1.3.0

# Pull new image
docker-compose pull

# Deploy with zero-downtime
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

---

## Multi-Version Docker Compose

### Client A (Conservative - v1.2.0)

**File**: `docker-compose.client-a.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: legislatie_postgres_clienta
    environment:
      POSTGRES_DB: monitoring_platform
      POSTGRES_USER: legislatie_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data_clienta:/var/lib/postgresql/data

  api:
    image: octavianissuemonitoring/parser-law:1.2.0  # Fixed version
    container_name: legislatie_api_clienta
    environment:
      DATABASE_URL: postgresql://legislatie_user:${DB_PASSWORD}@postgres:5432/monitoring_platform
      API_VERSION: "1.2.0"
    ports:
      - "8000:8000"
    depends_on:
      - postgres

volumes:
  postgres_data_clienta:

networks:
  default:
    name: legislatie_network_clienta
```

### Client B (Latest Stable - v1.3.x)

**File**: `docker-compose.client-b.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: legislatie_postgres_clientb
    environment:
      POSTGRES_DB: monitoring_platform
      POSTGRES_USER: legislatie_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data_clientb:/var/lib/postgresql/data

  api:
    image: octavianissuemonitoring/parser-law:1.3  # Rolling minor version
    container_name: legislatie_api_clientb
    environment:
      DATABASE_URL: postgresql://legislatie_user:${DB_PASSWORD}@postgres:5432/monitoring_platform
      API_VERSION: "1.3.x"
    ports:
      - "8000:8000"
    depends_on:
      - postgres

volumes:
  postgres_data_clientb:

networks:
  default:
    name: legislatie_network_clientb
```

### Staging (Always Latest)

**File**: `docker-compose.staging.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: legislatie_postgres_staging
    environment:
      POSTGRES_DB: monitoring_platform
      POSTGRES_USER: legislatie_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data_staging:/var/lib/postgresql/data

  api:
    image: octavianissuemonitoring/parser-law:latest  # Always latest
    container_name: legislatie_api_staging
    environment:
      DATABASE_URL: postgresql://legislatie_user:${DB_PASSWORD}@postgres:5432/monitoring_platform
      API_VERSION: "latest"
      LOG_LEVEL: DEBUG
    ports:
      - "8000:8000"
    depends_on:
      - postgres

volumes:
  postgres_data_staging:

networks:
  default:
    name: legislatie_network_staging
```

---

## Version Management in Code

### Update Version String

**File**: `db_service/app/main.py`

```python
from fastapi import FastAPI

# Version management
__version__ = "1.3.0"  # Update this on each release

app = FastAPI(
    title="Legislație România API",
    description="API pentru monitorizare și analiză legislație",
    version=__version__,  # Displayed in /docs
)

@app.get("/health")
async def health_check():
    """Health check endpoint with version info"""
    return {
        "status": "healthy",
        "version": __version__,
        "build": "20240312-1500",  # Optional: CI/CD build number
    }

@app.get("/version")
async def version_info():
    """Detailed version information"""
    return {
        "api_version": __version__,
        "python_version": "3.11",
        "database_schema_version": "20240312",  # Alembic migration
        "changelog": f"https://github.com/octavianissuemonitoring/parser-law/releases/tag/v{__version__}",
    }
```

### Update pyproject.toml

```toml
[tool.poetry]
name = "parser-law"
version = "1.3.0"  # Update this on each release
description = "Parser și API pentru legislație România"
```

---

## Database Schema Versioning

### Alembic Migrations with Versions

```powershell
# Create migration for v1.3.0
cd db_service
alembic revision -m "v1.3.0: Add categories table"

# Edit migration file
# migrations/versions/20240312_v1.3.0_add_categories.py
```

**Migration Template**:

```python
"""v1.3.0: Add categories table

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2024-03-12 15:00:00

"""
from alembic import op
import sqlalchemy as sa

# version identifiers
revision = 'abc123def456'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None
version = '1.3.0'  # Track version in migration

def upgrade():
    """Upgrade to v1.3.0"""
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        schema='legislatie'
    )

def downgrade():
    """Downgrade from v1.3.0"""
    op.drop_table('categories', schema='legislatie')
```

### Migration Version Table

```sql
-- Check current schema version
SELECT version_num, description 
FROM alembic_version;

-- Example output:
-- version_num        | description
-- -------------------|----------------------------------
-- abc123def456       | v1.3.0: Add categories table
```

---

## Rollback Strategy

### Rollback to Previous Version

```powershell
# On VPS
ssh root@vps
cd /opt/parser-law

# Stop current version
docker-compose down

# Update to previous version
nano docker-compose.yml
# Change: image: parser-law:1.3.0 → parser-law:1.2.0

# Pull old image (if not cached)
docker-compose pull

# Start old version
docker-compose up -d

# Rollback database migrations (if needed)
docker exec legislatie_api alembic downgrade abc123def456  # Previous migration
```

### Database Rollback

```powershell
# Check current migration
docker exec legislatie_api alembic current

# Downgrade one version
docker exec legislatie_api alembic downgrade -1

# Downgrade to specific version
docker exec legislatie_api alembic downgrade abc123def456

# Verify
docker exec legislatie_api alembic current
```

---

## GitHub Releases

### Create Release on GitHub

1. **Go to Releases**: https://github.com/octavianissuemonitoring/parser-law/releases
2. **Click "Create a new release"**
3. **Choose tag**: v1.3.0
4. **Release title**: v1.3.0 - Categories Feature
5. **Description** (Markdown):

```markdown
## 🚀 Features

- ✅ Add categories API endpoints (`/api/v1/categories`)
- ✅ Category assignment to legal documents
- ✅ Hierarchical category structure support

## 🐛 Bug Fixes

- Fix parser encoding issues with special characters
- Improve metadata extraction reliability
- Fix database connection pool exhaustion

## 📊 Performance

- 30% faster document parsing
- Reduced memory usage by 20%
- Database query optimization

## 🔄 Database Migrations

- Migration `abc123def456`: Add categories table
- **Breaking**: None
- **Rollback**: Supported

## 📦 Docker Images

```bash
docker pull octavianissuemonitoring/parser-law:1.3.0
docker pull octavianissuemonitoring/parser-law:1.3
docker pull octavianissuemonitoring/parser-law:latest
```

## 📖 Documentation

- [API Documentation](http://legislatie.issuemonitoring.ro/docs)
- [Migration Guide](MIGRATION_v1.3.0.md)
- [Changelog](CHANGELOG.md)

## 🔗 Links

- **Docker Hub**: https://hub.docker.com/r/octavianissuemonitoring/parser-law
- **API Health**: http://legislatie.issuemonitoring.ro/health
- **Version Info**: http://legislatie.issuemonitoring.ro/version

## ⚠️ Known Issues

- None

## 📅 Release Date

March 12, 2024
```

6. **Attach files** (optional):
   - `CHANGELOG.md`
   - `MIGRATION_v1.3.0.md`
   - Docker Compose examples

7. **Publish release**

---

## Automated Release with GitHub Actions

### GitHub Actions Workflow

**File**: `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    tags:
      - 'v*.*.*'  # Trigger on version tags

jobs:
  build-and-release:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      
    - name: Extract version
      id: version
      run: |
        echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT
        
    - name: Build Docker image
      run: |
        cd db_service
        docker build -t octavianissuemonitoring/parser-law:${{ steps.version.outputs.VERSION }} .
        docker tag octavianissuemonitoring/parser-law:${{ steps.version.outputs.VERSION }} \
                   octavianissuemonitoring/parser-law:latest
        
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
        
    - name: Push Docker images
      run: |
        docker push octavianissuemonitoring/parser-law:${{ steps.version.outputs.VERSION }}
        docker push octavianissuemonitoring/parser-law:latest
        
    - name: Create GitHub Release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ steps.version.outputs.VERSION }}
        body_path: CHANGELOG.md
        draft: false
        prerelease: false
```

---

## CHANGELOG Format

### Keep a Changelog

**File**: `CHANGELOG.md`

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Work in progress...

## [1.3.0] - 2024-03-12

### Added
- Categories API endpoints
- Category assignment functionality
- Hierarchical category support
- API versioning in `/version` endpoint

### Changed
- Improved metadata extraction reliability
- Optimized database queries (30% faster)

### Fixed
- Parser encoding issues with special characters
- Database connection pool exhaustion
- Memory leaks in long-running processes

### Security
- Updated dependencies (no vulnerabilities)

## [1.2.0] - 2024-02-15

### Added
- Search endpoint with full-text search
- Export functionality for CSV/JSON
- Batch processing support

### Fixed
- Parser crash on malformed HTML
- Database transaction rollback issues

## [1.1.0] - 2024-01-20

### Added
- Initial categories structure
- Basic metadata extraction

### Changed
- Database schema optimization

## [1.0.0] - 2024-01-01

### Added
- Initial stable release
- FastAPI REST API
- PostgreSQL database
- Basic CRUD operations
- Health check endpoint

[Unreleased]: https://github.com/octavianissuemonitoring/parser-law/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/octavianissuemonitoring/parser-law/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/octavianissuemonitoring/parser-law/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/octavianissuemonitoring/parser-law/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/octavianissuemonitoring/parser-law/releases/tag/v1.0.0
```

---

## Version Upgrade Strategy for Clients

### Conservative Client (Upgrade v1.2.0 → v1.3.0)

```powershell
# 1. Backup current database
ssh root@vps-client-a
cd /opt/parser-law
docker exec legislatie_postgres pg_dump -U legislatie_user monitoring_platform > backup_v1.2.0.sql

# 2. Test new version in staging
docker pull octavianissuemonitoring/parser-law:1.3.0
docker run -d --name test_api \
  -e DATABASE_URL=postgresql://... \
  -p 8001:8000 \
  octavianissuemonitoring/parser-law:1.3.0

# Test endpoints
curl http://localhost:8001/health
curl http://localhost:8001/docs

# 3. If tests pass, update production
nano docker-compose.yml
# Change: image: parser-law:1.2.0 → parser-law:1.3.0

docker-compose pull
docker-compose up -d

# 4. Verify
curl http://localhost:8000/health
# Should return: {"status": "healthy", "version": "1.3.0"}

# 5. If issues, rollback
docker-compose down
nano docker-compose.yml  # Revert to 1.2.0
docker-compose up -d
```

### Aggressive Client (Always Latest)

```yaml
# docker-compose.yml
services:
  api:
    image: octavianissuemonitoring/parser-law:latest
    restart: unless-stopped
```

```bash
# Auto-update cron job
# /etc/cron.d/parser-law-update
0 2 * * 0 cd /opt/parser-law && docker-compose pull && docker-compose up -d
```

---

## Version Compatibility Matrix

| Version | Database Schema | Breaking Changes | Recommended For |
|---------|----------------|------------------|-----------------|
| **1.0.0** | v1.0 | N/A | Initial deployment |
| **1.1.0** | v1.1 | None | Stable production |
| **1.2.0** | v1.2 | None | Current stable |
| **1.3.0** | v1.3 | None | New features |
| **2.0.0** | v2.0 | **Yes** (API changes) | Future major update |

### Breaking Changes in v2.0.0 (Example)

```markdown
## Migration from v1.x to v2.0

### API Endpoint Changes

- ❌ Removed: `/api/acte` → Use `/api/v1/documents` instead
- ✅ Added: `/api/v2/documents` with pagination
- ⚠️ Changed: `/health` response format

### Database Schema Changes

- Renamed table: `acte_legislative` → `documents`
- Added required column: `documents.category_id`
- Migration path: Run `alembic upgrade head`

### Configuration Changes

- Renamed env var: `DB_HOST` → `DATABASE_HOST`
- New required var: `API_VERSION=2.0`

### Migration Steps

1. Backup database: `pg_dump ...`
2. Update docker-compose.yml
3. Run migrations: `alembic upgrade head`
4. Update API clients to use `/api/v2/...`
5. Test all endpoints
```

---

## Quick Reference

### Release Checklist

- [ ] Create release branch: `release/x.y.z`
- [ ] Bump version in code (`main.py`, `pyproject.toml`)
- [ ] Update `CHANGELOG.md`
- [ ] Create database migrations (if needed)
- [ ] Test release candidate: `x.y.z-rc.1`
- [ ] Merge to `master` and tag: `git tag -a vx.y.z`
- [ ] Build Docker images with multiple tags
- [ ] Push to Docker Hub / GitHub Container Registry
- [ ] Create GitHub Release with notes
- [ ] Deploy to staging and verify
- [ ] Notify clients about new version
- [ ] Update production environments (gradual rollout)
- [ ] Monitor logs and errors
- [ ] Merge back to `develop`

### Version Deployment Commands

```powershell
# Deploy specific version
docker pull octavianissuemonitoring/parser-law:1.3.0
docker-compose up -d

# Deploy latest stable
docker pull octavianissuemonitoring/parser-law:latest
docker-compose up -d

# Check running version
curl http://localhost:8000/version

# Rollback to previous
docker-compose down
# Edit docker-compose.yml to previous version
docker-compose up -d
```

### Docker Hub vs GitHub Container Registry

**Docker Hub** (Recommended for public images):
```bash
docker login
docker push octavianissuemonitoring/parser-law:1.3.0
```

**GitHub Container Registry** (Recommended for private or integrated):
```bash
echo $CR_PAT | docker login ghcr.io -u USERNAME --password-stdin
docker tag parser-law:1.3.0 ghcr.io/octavianissuemonitoring/parser-law:1.3.0
docker push ghcr.io/octavianissuemonitoring/parser-law:1.3.0
```

---

## Benefits

✅ **Multiple clients on different versions** - Client A stays on v1.2.0, Client B upgrades to v1.3.0

✅ **Independent deployments** - Each VPS pulls specific Docker image version

✅ **Easy rollback** - Change image tag in docker-compose.yml, restart

✅ **Semantic versioning** - Clear what changed (MAJOR.MINOR.PATCH)

✅ **Immutable releases** - v1.3.0 Docker image never changes

✅ **Rolling updates** - Use `1.3` tag for automatic patch updates

✅ **Safe testing** - Test new versions in staging before production

✅ **Zero-downtime updates** - Docker Compose recreates containers smoothly

✅ **Version tracking** - `/version` endpoint shows running version

✅ **Database migrations** - Alembic tracks schema versions

---

## Next Steps

1. **Create first release**: Tag current master as `v1.0.0`
2. **Setup Docker Hub**: Create repository `octavianissuemonitoring/parser-law`
3. **Build initial image**: `docker build -t parser-law:1.0.0 db_service/`
4. **Push to registry**: `docker push octavianissuemonitoring/parser-law:1.0.0`
5. **Update VPS**: Change `docker-compose.yml` to use `image: parser-law:1.0.0`
6. **Test rollout**: Deploy to staging, verify, deploy to production
7. **Document versions**: Create `CHANGELOG.md` with version history
8. **Automate releases**: Setup GitHub Actions for CI/CD

**Result**: Multiple versions deployable, each client chooses their version, easy rollback, professional release management! 🚀
