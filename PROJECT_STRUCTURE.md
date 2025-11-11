# Project Structure Reorganization - v2.0.0

**Problem**: 16+ `.md` files in root, code scattered, hard to navigate

**Solution**: Modern monorepo structure with clear separation

---

## Current Structure (v1.x - Problematic)

```
parser-law/
├── README.md                          # ✅ Keep
├── ADOPTION_GUIDE.md                  # 📦 Move to docs/
├── AI_PROCESSING_STRATEGY.md          # 📦 Move to docs/
├── ARCHITECTURE_COMPARISON.md         # 📦 Move to docs/
├── CATEGORIES_IMPLEMENTATION.md       # 📦 Move to docs/
├── CODE_REVIEW_AND_REFACTORING.md     # 📦 Move to docs/
├── DATABASE_DOCUMENTATION.md          # 📦 Move to docs/
├── DEPLOYMENT_VPS.md                  # 📦 Move to docs/
├── DEVELOPMENT_GUIDE.md               # 📦 Move to docs/
├── DEVELOPMENT_STRATEGY.md            # 📦 Move to docs/
├── GIT_WORKFLOW.md                    # 📦 Move to docs/
├── LOCAL_DEVELOPMENT.md               # 📦 Move to docs/
├── QUALITY_RULES.md                   # 📦 Move to docs/
├── QUICKSTART_VPS.md                  # 📦 Move to docs/
├── RELEASE_MANAGEMENT.md              # 📦 Move to docs/
├── ROLLBACK_INSTRUCTIONS.md           # 📦 Move to docs/
├── SCHEDULER_README.md                # 📦 Move to docs/
├── WEB_CATEGORIES_UI.md               # 📦 Move to docs/
├── WEB_INTERFACE_README.md            # 📦 Move to docs/
├── BACKUP_SUMMARY.txt                 # 🗑️ Delete (old)
├── CLEANUP_SUMMARY.md                 # 🗑️ Delete (old)
├── scraper_legislatie.py              # 📦 Move to src/
├── html_parser.py                     # 📦 Move to src/
├── hybrid_parser.py                   # 📦 Move to src/
├── metadata_extractor.py              # 📦 Move to src/
├── quality_checker.py                 # 📦 Move to src/
├── scheduler.py                       # 📦 Move to src/
├── config.py                          # 📦 Move to src/
├── cleanup_files.py                   # 📦 Move to scripts/
├── docker-compose.dev.yml             # ✅ Keep
├── docker-compose.scheduler.yml       # ✅ Keep
├── Dockerfile.scheduler               # 📦 Move to docker/
├── .env.example                       # ✅ Keep
├── pyproject.toml                     # ✅ Keep
├── db_service/                        # ✅ Keep (API service)
├── scripts/                           # ✅ Keep
├── infra/                             # ✅ Keep
├── export_csv/                        # 📦 Move to data/
└── rezultate/                         # 📦 Move to data/
```

**Issues**:
- ❌ 18 documentation files in root (cluttered)
- ❌ Python code scattered in root (no `src/` folder)
- ❌ Mixed concerns (code + docs + config)
- ❌ Hard to find what you need
- ❌ Not scalable (adding more features = more clutter)

---

## Proposed Structure (v2.0.0 - Clean)

```
parser-law/
│
├── README.md                          # 📖 Main entry point (short, links to docs/)
├── CHANGELOG.md                       # 📝 Version history
├── LICENSE                            # ⚖️ License
│
├── .env.example                       # 🔧 Environment template
├── .gitignore                         # 🚫 Git ignore rules
├── .editorconfig                      # 📝 Editor config
├── .flake8                            # 🔍 Linting config
├── .pre-commit-config.yaml            # 🪝 Git hooks
├── pyproject.toml                     # 📦 Python project config
│
├── docker-compose.yml                 # 🐳 Production compose
├── docker-compose.dev.yml             # 🐳 Development compose
├── docker-compose.scheduler.yml       # 🐳 Scheduler compose
│
├── docs/                              # 📚 ALL DOCUMENTATION HERE
│   ├── README.md                      # Index of all docs
│   │
│   ├── getting-started/               # 🚀 For new users
│   │   ├── quickstart.md              # 5-minute setup
│   │   ├── local-development.md       # LOCAL_DEVELOPMENT.md
│   │   └── deployment.md              # DEPLOYMENT_VPS.md + QUICKSTART_VPS.md
│   │
│   ├── development/                   # 👨‍💻 For developers
│   │   ├── guide.md                   # DEVELOPMENT_GUIDE.md
│   │   ├── standards.md               # CODE_REVIEW_AND_REFACTORING.md + QUALITY_RULES.md
│   │   ├── git-workflow.md            # GIT_WORKFLOW.md
│   │   ├── release-management.md      # RELEASE_MANAGEMENT.md
│   │   └── testing.md                 # Testing strategy
│   │
│   ├── architecture/                  # 🏗️ System design
│   │   ├── overview.md                # High-level architecture
│   │   ├── database.md                # DATABASE_DOCUMENTATION.md
│   │   ├── api.md                     # API design
│   │   ├── scheduler.md               # SCHEDULER_README.md
│   │   └── comparison.md              # ARCHITECTURE_COMPARISON.md
│   │
│   ├── features/                      # ✨ Feature documentation
│   │   ├── categories.md              # CATEGORIES_IMPLEMENTATION.md
│   │   ├── ai-processing.md           # AI_PROCESSING_STRATEGY.md
│   │   └── web-interface.md           # WEB_CATEGORIES_UI.md + WEB_INTERFACE_README.md
│   │
│   ├── operations/                    # 🛠️ DevOps & maintenance
│   │   ├── deployment.md              # DEPLOYMENT_VPS.md
│   │   ├── rollback.md                # ROLLBACK_INSTRUCTIONS.md
│   │   ├── monitoring.md              # Monitoring setup
│   │   └── backup.md                  # Backup strategy
│   │
│   └── adoption/                      # 📈 Process & strategy
│       ├── guide.md                   # ADOPTION_GUIDE.md
│       └── strategy.md                # DEVELOPMENT_STRATEGY.md
│
├── src/                               # 🐍 PYTHON SOURCE CODE
│   ├── __init__.py
│   │
│   ├── scraper/                       # Scraping logic
│   │   ├── __init__.py
│   │   ├── legislatie.py              # scraper_legislatie.py
│   │   ├── html_parser.py             # html_parser.py
│   │   ├── hybrid_parser.py           # hybrid_parser.py
│   │   └── metadata_extractor.py      # metadata_extractor.py
│   │
│   ├── scheduler/                     # Scheduling logic
│   │   ├── __init__.py
│   │   └── scheduler.py               # scheduler.py
│   │
│   ├── quality/                       # Quality checks
│   │   ├── __init__.py
│   │   └── checker.py                 # quality_checker.py
│   │
│   ├── config/                        # Configuration
│   │   ├── __init__.py
│   │   └── settings.py                # config.py
│   │
│   └── utils/                         # Shared utilities
│       ├── __init__.py
│       └── helpers.py
│
├── db_service/                        # 🚀 FastAPI service (existing)
│   ├── app/
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
│
├── tests/                             # 🧪 ALL TESTS HERE
│   ├── __init__.py
│   ├── conftest.py                    # Pytest config
│   │
│   ├── unit/                          # Unit tests
│   │   ├── test_scraper.py
│   │   ├── test_parser.py
│   │   └── test_metadata.py
│   │
│   ├── integration/                   # Integration tests
│   │   ├── test_api.py
│   │   └── test_database.py
│   │
│   └── fixtures/                      # Test data
│       └── sample_html.html
│
├── scripts/                           # 🔧 Automation scripts
│   ├── setup-local-dev.ps1            # Setup automation
│   ├── release.ps1                    # Release automation
│   ├── deploy.sh                      # Deployment script
│   ├── backup.sh                      # Backup script
│   └── cleanup.py                     # cleanup_files.py
│
├── docker/                            # 🐳 Docker configs
│   ├── Dockerfile.api                 # API container
│   ├── Dockerfile.scheduler           # Scheduler container
│   └── nginx.conf                     # nginx.conf.example
│
├── data/                              # 💾 Data files
│   ├── export/                        # export_csv/
│   ├── rezultate/                     # rezultate/
│   └── backups/                       # Backup storage
│
├── infra/                             # ☁️ Infrastructure as Code
│   ├── README.md
│   └── vps-setup.md
│
└── .vscode/                           # VS Code config (existing)
    ├── extensions.json
    ├── settings.json
    ├── launch.json
    └── api-tests.http
```

---

## Benefits of New Structure

### ✅ **Clear Separation of Concerns**

| Folder | Purpose | Who Uses It |
|--------|---------|-------------|
| `docs/` | All documentation | Everyone |
| `src/` | Python source code | Developers |
| `db_service/` | FastAPI API | Backend developers |
| `tests/` | All tests | QA + Developers |
| `scripts/` | Automation | DevOps + Developers |
| `docker/` | Container configs | DevOps |
| `data/` | Runtime data | System (generated) |
| `infra/` | Infrastructure | DevOps |

### ✅ **Easy Navigation**

```bash
# Want to understand the system?
cd docs/getting-started/

# Want to develop a feature?
cd src/scraper/
cd tests/unit/

# Want to deploy?
cd docs/operations/deployment.md
cd scripts/deploy.sh

# Want to see architecture?
cd docs/architecture/
```

### ✅ **Scalability**

```bash
# Add new feature
src/
  └── new_feature/
      ├── __init__.py
      └── logic.py

docs/
  └── features/
      └── new_feature.md

# Add new service
services/
  └── new_service/
      ├── Dockerfile
      └── app/
```

### ✅ **Professional Standard**

Follows industry best practices:
- **Django/Flask**: `src/` for code, `docs/` for documentation
- **Next.js**: `src/`, `public/`, `docs/`
- **Rust**: `src/`, `tests/`, `docs/`
- **Go**: `cmd/`, `pkg/`, `docs/`
- **Google/Microsoft**: Clear folder hierarchy

---

## Migration Plan

### Phase 1: Create New Structure (v2.0.0-alpha)

```powershell
# Create new folders
mkdir docs, src, tests, docker, data

# Move documentation
mkdir docs/getting-started, docs/development, docs/architecture, docs/features, docs/operations, docs/adoption

# Move code
mkdir src/scraper, src/scheduler, src/quality, src/config, src/utils

# Move tests
mkdir tests/unit, tests/integration, tests/fixtures
```

### Phase 2: Move Files (v2.0.0-beta)

```powershell
# Documentation
git mv LOCAL_DEVELOPMENT.md docs/getting-started/local-development.md
git mv DEPLOYMENT_VPS.md docs/getting-started/deployment.md
git mv QUICKSTART_VPS.md docs/getting-started/quickstart.md
git mv DEVELOPMENT_GUIDE.md docs/development/guide.md
git mv GIT_WORKFLOW.md docs/development/git-workflow.md
git mv RELEASE_MANAGEMENT.md docs/development/release-management.md
git mv DATABASE_DOCUMENTATION.md docs/architecture/database.md
git mv CATEGORIES_IMPLEMENTATION.md docs/features/categories.md
git mv ROLLBACK_INSTRUCTIONS.md docs/operations/rollback.md
git mv ADOPTION_GUIDE.md docs/adoption/guide.md

# Code
git mv scraper_legislatie.py src/scraper/legislatie.py
git mv html_parser.py src/scraper/html_parser.py
git mv hybrid_parser.py src/scraper/hybrid_parser.py
git mv metadata_extractor.py src/scraper/metadata_extractor.py
git mv scheduler.py src/scheduler/scheduler.py
git mv quality_checker.py src/quality/checker.py
git mv config.py src/config/settings.py

# Docker
git mv Dockerfile.scheduler docker/Dockerfile.scheduler
git mv nginx.conf.example docker/nginx.conf

# Data
git mv export_csv data/export
git mv rezultate data/rezultate

# Scripts
git mv cleanup_files.py scripts/cleanup.py
```

### Phase 3: Update Imports (v2.0.0-rc.1)

```python
# Old imports
from scraper_legislatie import scrape
from html_parser import parse_html

# New imports
from src.scraper.legislatie import scrape
from src.scraper.html_parser import parse_html
```

Update:
- `scheduler.py` imports
- `db_service/app/` imports
- Test imports
- Script imports

### Phase 4: Update Documentation (v2.0.0-rc.2)

- Update `README.md` with new structure
- Update all doc cross-references
- Update paths in scripts
- Update Docker Compose paths

### Phase 5: Test Everything (v2.0.0-rc.3)

```bash
# Run all tests
pytest tests/

# Test local development
docker-compose -f docker-compose.dev.yml up -d

# Test scheduler
docker-compose -f docker-compose.scheduler.yml up -d

# Test API
curl http://localhost:8000/health
```

### Phase 6: Deploy v2.0.0 (Stable)

```bash
# Tag release
git tag -a v2.0.0 -m "Release v2.0.0: Restructured project

Breaking changes:
- Moved all documentation to docs/
- Moved all code to src/
- Updated imports
- Reorganized folder structure

Migration guide: docs/operations/migration-v2.md
"

# Build Docker images
docker build -t parser-law:2.0.0 .

# Deploy
# See docs/operations/deployment.md
```

---

## README.md (New - Short & Clean)

```markdown
# Parser Law - Legislație România 🇷🇴

> Modern API and scraper for Romanian legislation monitoring

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/octavianissuemonitoring/parser-law/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/octavianissuemonitoring/parser-law.git
cd parser-law

# 2. Setup environment
cp .env.example .env
# Edit .env with your settings

# 3. Start services
docker-compose up -d

# 4. Access API
open http://localhost:8000/docs
```

**⏱️ Setup time: 5 minutes**

## 📚 Documentation

- **[Getting Started](docs/getting-started/)** - Setup, local development, deployment
- **[Development](docs/development/)** - Coding standards, Git workflow, testing
- **[Architecture](docs/architecture/)** - System design, database, API
- **[Features](docs/features/)** - Categories, AI processing, web interface
- **[Operations](docs/operations/)** - Deployment, rollback, monitoring

## 🏗️ Project Structure

```
parser-law/
├── docs/              # 📚 All documentation
├── src/               # 🐍 Python source code
├── db_service/        # 🚀 FastAPI service
├── tests/             # 🧪 All tests
├── scripts/           # 🔧 Automation
├── docker/            # 🐳 Docker configs
└── data/              # 💾 Runtime data
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for details.

## 🛠️ Tech Stack

- **API**: FastAPI 0.104+ (Python 3.11)
- **Database**: PostgreSQL 15
- **Scraping**: BeautifulSoup4, Requests
- **Scheduler**: APScheduler
- **Testing**: Pytest, Coverage
- **CI/CD**: GitHub Actions
- **Deployment**: Docker Compose

## 📦 Features

- ✅ Scrape legislation from legislatie.just.ro
- ✅ Parse HTML and extract metadata
- ✅ REST API with full CRUD operations
- ✅ Category management and assignment
- ✅ Scheduled updates (daily/weekly)
- ✅ Quality checks and validation
- ✅ Export to CSV/JSON
- ✅ Full-text search
- ✅ Database migrations (Alembic)

## 🤝 Contributing

See [docs/development/guide.md](docs/development/guide.md)

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🔗 Links

- **API Docs**: http://legislatie.issuemonitoring.ro/docs
- **GitHub**: https://github.com/octavianissuemonitoring/parser-law
- **Issues**: https://github.com/octavianissuemonitoring/parser-law/issues
```

---

## Automated Migration Script

**File**: `scripts/restructure-v2.ps1`

```powershell
# Automate folder structure migration
# Usage: .\scripts\restructure-v2.ps1

Write-Host "🏗️ Restructuring Project for v2.0.0" -ForegroundColor Cyan

# Create folders
New-Item -ItemType Directory -Path "docs/getting-started" -Force
New-Item -ItemType Directory -Path "docs/development" -Force
New-Item -ItemType Directory -Path "docs/architecture" -Force
New-Item -ItemType Directory -Path "docs/features" -Force
New-Item -ItemType Directory -Path "docs/operations" -Force
New-Item -ItemType Directory -Path "docs/adoption" -Force
New-Item -ItemType Directory -Path "src/scraper" -Force
New-Item -ItemType Directory -Path "src/scheduler" -Force
New-Item -ItemType Directory -Path "src/quality" -Force
New-Item -ItemType Directory -Path "src/config" -Force
New-Item -ItemType Directory -Path "src/utils" -Force
New-Item -ItemType Directory -Path "tests/unit" -Force
New-Item -ItemType Directory -Path "tests/integration" -Force
New-Item -ItemType Directory -Path "tests/fixtures" -Force
New-Item -ItemType Directory -Path "docker" -Force
New-Item -ItemType Directory -Path "data/export" -Force
New-Item -ItemType Directory -Path "data/rezultate" -Force

# Move documentation
git mv LOCAL_DEVELOPMENT.md docs/getting-started/local-development.md
git mv DEPLOYMENT_VPS.md docs/getting-started/deployment.md
git mv QUICKSTART_VPS.md docs/getting-started/quickstart.md
git mv DEVELOPMENT_GUIDE.md docs/development/guide.md
git mv GIT_WORKFLOW.md docs/development/git-workflow.md
git mv RELEASE_MANAGEMENT.md docs/development/release-management.md
git mv CODE_REVIEW_AND_REFACTORING.md docs/development/standards.md
git mv QUALITY_RULES.md docs/development/quality.md
git mv DATABASE_DOCUMENTATION.md docs/architecture/database.md
git mv SCHEDULER_README.md docs/architecture/scheduler.md
git mv ARCHITECTURE_COMPARISON.md docs/architecture/comparison.md
git mv CATEGORIES_IMPLEMENTATION.md docs/features/categories.md
git mv AI_PROCESSING_STRATEGY.md docs/features/ai-processing.md
git mv WEB_CATEGORIES_UI.md docs/features/web-interface.md
git mv ROLLBACK_INSTRUCTIONS.md docs/operations/rollback.md
git mv ADOPTION_GUIDE.md docs/adoption/guide.md
git mv DEVELOPMENT_STRATEGY.md docs/adoption/strategy.md

# Move code
git mv scraper_legislatie.py src/scraper/legislatie.py
git mv html_parser.py src/scraper/html_parser.py
git mv hybrid_parser.py src/scraper/hybrid_parser.py
git mv metadata_extractor.py src/scraper/metadata_extractor.py
git mv scheduler.py src/scheduler/scheduler.py
git mv quality_checker.py src/quality/checker.py
git mv config.py src/config/settings.py

# Move Docker
git mv Dockerfile.scheduler docker/Dockerfile.scheduler
git mv nginx.conf.example docker/nginx.conf

# Move data
git mv export_csv/* data/export/
git mv rezultate/* data/rezultate/

# Move scripts
git mv cleanup_files.py scripts/cleanup.py

# Delete old files
Remove-Item "BACKUP_SUMMARY.txt" -Force
Remove-Item "CLEANUP_SUMMARY.md" -Force
Remove-Item "export_csv" -Recurse -Force
Remove-Item "rezultate" -Recurse -Force

Write-Host "✅ Restructure complete!" -ForegroundColor Green
Write-Host "Next: Update imports and test" -ForegroundColor Yellow
```

---

## Breaking Changes in v2.0.0

### Import Paths Changed

```python
# ❌ Old (v1.x)
from scraper_legislatie import scrape
from html_parser import parse_html
from metadata_extractor import extract_metadata

# ✅ New (v2.0.0)
from src.scraper.legislatie import scrape
from src.scraper.html_parser import parse_html
from src.scraper.metadata_extractor import extract_metadata
```

### Documentation Paths Changed

```markdown
# ❌ Old (v1.x)
See [LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md)
See [GIT_WORKFLOW.md](GIT_WORKFLOW.md)

# ✅ New (v2.0.0)
See [Local Development](docs/getting-started/local-development.md)
See [Git Workflow](docs/development/git-workflow.md)
```

### Docker Paths Changed

```yaml
# ❌ Old (v1.x)
volumes:
  - ./export_csv:/app/export
  - ./rezultate:/app/rezultate

# ✅ New (v2.0.0)
volumes:
  - ./data/export:/app/export
  - ./data/rezultate:/app/rezultate
```

---

## Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| **Alpha** | 1 day | Create folders, move files |
| **Beta** | 2-3 days | Update imports, fix references |
| **RC.1** | 1 week | Test everything, fix bugs |
| **Stable** | Deploy | v2.0.0 release |

---

## Rollback Plan

If v2.0.0 has issues:

```bash
# Quick rollback to v1.x
git checkout v1.2.0  # Last stable v1.x
docker-compose up -d

# Or Docker image
docker pull parser-law:1.2.0
```

---

## Decision: Should We Do This?

### ✅ Pros

1. **Professional structure** - Industry standard
2. **Scalable** - Easy to add features
3. **Clean root** - Only essential files visible
4. **Better navigation** - Logical folder hierarchy
5. **Team-friendly** - New developers find things easily
6. **Tooling support** - IDEs, linters recognize standard structure

### ⚠️ Cons

1. **Breaking changes** - Imports need updating
2. **Migration effort** - 1-2 days work
3. **Learning curve** - Team needs to learn new paths (minimal)
4. **Existing bookmarks** - Documentation links break

### 🎯 Recommendation

**YES** - Do it now while project is young. Benefits outweigh costs.

- Current: ~50 commits, 2-3 developers
- Future: 500+ commits, 10+ developers

Better to restructure at 50 commits than 500.

---

## Next Steps

1. **Review this plan** - Confirm structure makes sense
2. **Create feature branch**: `git checkout -b feature/v2-restructure`
3. **Run migration script**: `.\scripts\restructure-v2.ps1`
4. **Update imports**: Fix Python import paths
5. **Test everything**: `pytest tests/`
6. **Update docs**: Fix cross-references
7. **Create PR**: Merge to `develop`
8. **Test in staging**: Deploy and verify
9. **Release v2.0.0**: Tag and deploy to production

**Time estimate**: 2-3 days for complete migration

---

## Questions?

- **Will old docs still work?** - Yes, via redirects or 404 with new path suggestion
- **Do clients need to change?** - No, Docker images work the same
- **Will API change?** - No, API endpoints stay identical
- **Can we rollback?** - Yes, use v1.x tag

Ready to start? 🚀
