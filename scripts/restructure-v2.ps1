# ============================================================================
# Project Restructure Script - v2.0.0
# ============================================================================
# 
# This script automates the migration to a clean, scalable project structure.
# 
# What it does:
# 1. Creates new folder structure (docs/, src/, tests/, docker/, data/)
# 2. Moves documentation to docs/ with logical grouping
# 3. Moves Python code to src/ with proper modules
# 4. Moves Docker configs to docker/
# 5. Moves runtime data to data/
# 6. Deletes old/obsolete files
# 7. Creates __init__.py files for Python packages
# 8. Creates docs/README.md index
# 
# Usage:
#   .\scripts\restructure-v2.ps1 [-DryRun]
# 
# ============================================================================

param(
    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"
$ColorInfo = "Cyan"

Write-Host "🏗️  Parser Law - Project Restructure v2.0.0" -ForegroundColor $ColorInfo
Write-Host "=============================================" -ForegroundColor $ColorInfo
Write-Host ""

if ($DryRun) {
    Write-Host "⚠️  DRY RUN MODE - No changes will be made" -ForegroundColor $ColorWarning
    Write-Host ""
}

# ============================================================================
# Step 1: Create New Folder Structure
# ============================================================================

Write-Host "📁 Step 1: Creating New Folder Structure" -ForegroundColor $ColorWarning
Write-Host "==========================================" -ForegroundColor $ColorWarning
Write-Host ""

$folders = @(
    # Documentation
    "docs",
    "docs/getting-started",
    "docs/development",
    "docs/architecture",
    "docs/features",
    "docs/operations",
    "docs/adoption",
    
    # Source code
    "src",
    "src/scraper",
    "src/scheduler",
    "src/quality",
    "src/config",
    "src/utils",
    
    # Tests
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",
    
    # Docker
    "docker",
    
    # Data
    "data",
    "data/export",
    "data/rezultate",
    "data/backups"
)

foreach ($folder in $folders) {
    if ($DryRun) {
        Write-Host "[DRY RUN] Would create: $folder" -ForegroundColor $ColorWarning
    } else {
        if (!(Test-Path $folder)) {
            New-Item -ItemType Directory -Path $folder -Force | Out-Null
            Write-Host "✅ Created: $folder" -ForegroundColor $ColorSuccess
        } else {
            Write-Host "⏭️  Exists: $folder" -ForegroundColor Gray
        }
    }
}

Write-Host ""

# ============================================================================
# Step 2: Move Documentation Files
# ============================================================================

Write-Host "📚 Step 2: Moving Documentation Files" -ForegroundColor $ColorWarning
Write-Host "=======================================" -ForegroundColor $ColorWarning
Write-Host ""

$docMoves = @{
    # Getting Started
    "LOCAL_DEVELOPMENT.md" = "docs/getting-started/local-development.md"
    "DEPLOYMENT_VPS.md" = "docs/getting-started/deployment.md"
    "QUICKSTART_VPS.md" = "docs/getting-started/quickstart.md"
    
    # Development
    "DEVELOPMENT_GUIDE.md" = "docs/development/guide.md"
    "GIT_WORKFLOW.md" = "docs/development/git-workflow.md"
    "RELEASE_MANAGEMENT.md" = "docs/development/release-management.md"
    "CODE_REVIEW_AND_REFACTORING.md" = "docs/development/standards.md"
    "QUALITY_RULES.md" = "docs/development/quality.md"
    
    # Architecture
    "DATABASE_DOCUMENTATION.md" = "docs/architecture/database.md"
    "SCHEDULER_README.md" = "docs/architecture/scheduler.md"
    "ARCHITECTURE_COMPARISON.md" = "docs/architecture/comparison.md"
    
    # Features
    "CATEGORIES_IMPLEMENTATION.md" = "docs/features/categories.md"
    "AI_PROCESSING_STRATEGY.md" = "docs/features/ai-processing.md"
    "WEB_CATEGORIES_UI.md" = "docs/features/web-interface.md"
    "WEB_INTERFACE_README.md" = "docs/features/web-ui.md"
    
    # Operations
    "ROLLBACK_INSTRUCTIONS.md" = "docs/operations/rollback.md"
    
    # Adoption
    "ADOPTION_GUIDE.md" = "docs/adoption/guide.md"
    "DEVELOPMENT_STRATEGY.md" = "docs/adoption/strategy.md"
}

foreach ($file in $docMoves.Keys) {
    $destination = $docMoves[$file]
    
    if (Test-Path $file) {
        if ($DryRun) {
            Write-Host "[DRY RUN] Would move: $file → $destination" -ForegroundColor $ColorWarning
        } else {
            git mv $file $destination 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Moved: $file → $destination" -ForegroundColor $ColorSuccess
            } else {
                # Fallback to file system move
                Move-Item $file $destination -Force
                Write-Host "✅ Moved: $file → $destination (filesystem)" -ForegroundColor $ColorSuccess
            }
        }
    } else {
        Write-Host "⏭️  Skip: $file (not found)" -ForegroundColor Gray
    }
}

Write-Host ""

# ============================================================================
# Step 3: Move Python Source Code
# ============================================================================

Write-Host "🐍 Step 3: Moving Python Source Code" -ForegroundColor $ColorWarning
Write-Host "======================================" -ForegroundColor $ColorWarning
Write-Host ""

$codeMoves = @{
    # Scraper
    "scraper_legislatie.py" = "src/scraper/legislatie.py"
    "html_parser.py" = "src/scraper/html_parser.py"
    "hybrid_parser.py" = "src/scraper/hybrid_parser.py"
    "metadata_extractor.py" = "src/scraper/metadata_extractor.py"
    
    # Scheduler
    "scheduler.py" = "src/scheduler/scheduler.py"
    
    # Quality
    "quality_checker.py" = "src/quality/checker.py"
    
    # Config
    "config.py" = "src/config/settings.py"
}

foreach ($file in $codeMoves.Keys) {
    $destination = $codeMoves[$file]
    
    if (Test-Path $file) {
        if ($DryRun) {
            Write-Host "[DRY RUN] Would move: $file → $destination" -ForegroundColor $ColorWarning
        } else {
            git mv $file $destination 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Moved: $file → $destination" -ForegroundColor $ColorSuccess
            } else {
                Move-Item $file $destination -Force
                Write-Host "✅ Moved: $file → $destination (filesystem)" -ForegroundColor $ColorSuccess
            }
        }
    } else {
        Write-Host "⏭️  Skip: $file (not found)" -ForegroundColor Gray
    }
}

Write-Host ""

# ============================================================================
# Step 4: Move Docker Configs
# ============================================================================

Write-Host "🐳 Step 4: Moving Docker Configs" -ForegroundColor $ColorWarning
Write-Host "==================================" -ForegroundColor $ColorWarning
Write-Host ""

$dockerMoves = @{
    "Dockerfile.scheduler" = "docker/Dockerfile.scheduler"
    "nginx.conf.example" = "docker/nginx.conf"
}

foreach ($file in $dockerMoves.Keys) {
    $destination = $dockerMoves[$file]
    
    if (Test-Path $file) {
        if ($DryRun) {
            Write-Host "[DRY RUN] Would move: $file → $destination" -ForegroundColor $ColorWarning
        } else {
            git mv $file $destination 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Moved: $file → $destination" -ForegroundColor $ColorSuccess
            } else {
                Move-Item $file $destination -Force
                Write-Host "✅ Moved: $file → $destination (filesystem)" -ForegroundColor $ColorSuccess
            }
        }
    } else {
        Write-Host "⏭️  Skip: $file (not found)" -ForegroundColor Gray
    }
}

Write-Host ""

# ============================================================================
# Step 5: Move Data Files
# ============================================================================

Write-Host "💾 Step 5: Moving Data Files" -ForegroundColor $ColorWarning
Write-Host "==============================" -ForegroundColor $ColorWarning
Write-Host ""

# Move export_csv/* to data/export/
if (Test-Path "export_csv") {
    if ($DryRun) {
        Write-Host "[DRY RUN] Would move: export_csv/* → data/export/" -ForegroundColor $ColorWarning
    } else {
        Get-ChildItem "export_csv" | ForEach-Object {
            Move-Item $_.FullName "data/export/" -Force
        }
        Write-Host "✅ Moved: export_csv/* → data/export/" -ForegroundColor $ColorSuccess
    }
}

# Move rezultate/* to data/rezultate/
if (Test-Path "rezultate") {
    if ($DryRun) {
        Write-Host "[DRY RUN] Would move: rezultate/* → data/rezultate/" -ForegroundColor $ColorWarning
    } else {
        Get-ChildItem "rezultate" | ForEach-Object {
            Move-Item $_.FullName "data/rezultate/" -Force
        }
        Write-Host "✅ Moved: rezultate/* → data/rezultate/" -ForegroundColor $ColorSuccess
    }
}

Write-Host ""

# ============================================================================
# Step 6: Move Scripts
# ============================================================================

Write-Host "🔧 Step 6: Moving Scripts" -ForegroundColor $ColorWarning
Write-Host "==========================" -ForegroundColor $ColorWarning
Write-Host ""

$scriptMoves = @{
    "cleanup_files.py" = "scripts/cleanup.py"
}

foreach ($file in $scriptMoves.Keys) {
    $destination = $scriptMoves[$file]
    
    if (Test-Path $file) {
        if ($DryRun) {
            Write-Host "[DRY RUN] Would move: $file → $destination" -ForegroundColor $ColorWarning
        } else {
            git mv $file $destination 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Moved: $file → $destination" -ForegroundColor $ColorSuccess
            } else {
                Move-Item $file $destination -Force
                Write-Host "✅ Moved: $file → $destination (filesystem)" -ForegroundColor $ColorSuccess
            }
        }
    } else {
        Write-Host "⏭️  Skip: $file (not found)" -ForegroundColor Gray
    }
}

Write-Host ""

# ============================================================================
# Step 7: Delete Old/Obsolete Files
# ============================================================================

Write-Host "🗑️  Step 7: Deleting Old/Obsolete Files" -ForegroundColor $ColorWarning
Write-Host "=========================================" -ForegroundColor $ColorWarning
Write-Host ""

$deleteFiles = @(
    "BACKUP_SUMMARY.txt",
    "CLEANUP_SUMMARY.md"
)

foreach ($file in $deleteFiles) {
    if (Test-Path $file) {
        if ($DryRun) {
            Write-Host "[DRY RUN] Would delete: $file" -ForegroundColor $ColorWarning
        } else {
            Remove-Item $file -Force
            Write-Host "✅ Deleted: $file" -ForegroundColor $ColorSuccess
        }
    } else {
        Write-Host "⏭️  Skip: $file (not found)" -ForegroundColor Gray
    }
}

# Delete empty folders
$emptyFolders = @("export_csv", "rezultate")
foreach ($folder in $emptyFolders) {
    if ((Test-Path $folder) -and ((Get-ChildItem $folder).Count -eq 0)) {
        if ($DryRun) {
            Write-Host "[DRY RUN] Would delete empty folder: $folder" -ForegroundColor $ColorWarning
        } else {
            Remove-Item $folder -Recurse -Force
            Write-Host "✅ Deleted empty folder: $folder" -ForegroundColor $ColorSuccess
        }
    }
}

Write-Host ""

# ============================================================================
# Step 8: Create __init__.py Files
# ============================================================================

Write-Host "📦 Step 8: Creating Python Package Files" -ForegroundColor $ColorWarning
Write-Host "===========================================" -ForegroundColor $ColorWarning
Write-Host ""

$initFiles = @(
    "src/__init__.py",
    "src/scraper/__init__.py",
    "src/scheduler/__init__.py",
    "src/quality/__init__.py",
    "src/config/__init__.py",
    "src/utils/__init__.py",
    "tests/__init__.py",
    "tests/unit/__init__.py",
    "tests/integration/__init__.py"
)

foreach ($file in $initFiles) {
    if ($DryRun) {
        Write-Host "[DRY RUN] Would create: $file" -ForegroundColor $ColorWarning
    } else {
        if (!(Test-Path $file)) {
            New-Item -ItemType File -Path $file -Force | Out-Null
            Write-Host "✅ Created: $file" -ForegroundColor $ColorSuccess
        } else {
            Write-Host "⏭️  Exists: $file" -ForegroundColor Gray
        }
    }
}

Write-Host ""

# ============================================================================
# Step 9: Create Documentation Index
# ============================================================================

Write-Host "📖 Step 9: Creating Documentation Index" -ForegroundColor $ColorWarning
Write-Host "=========================================" -ForegroundColor $ColorWarning
Write-Host ""

$docsReadme = @"
# Documentation Index

Welcome to Parser Law documentation! 📚

## 🚀 Getting Started

New to the project? Start here:

- **[Quick Start](getting-started/quickstart.md)** - Get up and running in 5 minutes
- **[Local Development](getting-started/local-development.md)** - Set up your dev environment
- **[Deployment Guide](getting-started/deployment.md)** - Deploy to production

## 👨‍💻 Development

For developers working on the project:

- **[Development Guide](development/guide.md)** - Coding standards and best practices
- **[Git Workflow](development/git-workflow.md)** - Branching strategy and version control
- **[Release Management](development/release-management.md)** - How to release new versions
- **[Code Standards](development/standards.md)** - Code review checklist
- **[Quality Rules](development/quality.md)** - Quality checks and metrics

## 🏗️ Architecture

Understanding the system:

- **[Database Schema](architecture/database.md)** - Database design and migrations
- **[API Design](architecture/api.md)** - API endpoints and contracts
- **[Scheduler](architecture/scheduler.md)** - Background job scheduling
- **[Comparison](architecture/comparison.md)** - Architecture alternatives

## ✨ Features

Detailed feature documentation:

- **[Categories](features/categories.md)** - Category management system
- **[AI Processing](features/ai-processing.md)** - AI-powered analysis
- **[Web Interface](features/web-interface.md)** - Web UI components

## 🛠️ Operations

DevOps and maintenance:

- **[Deployment](operations/deployment.md)** - Production deployment
- **[Rollback](operations/rollback.md)** - Rollback procedures
- **[Monitoring](operations/monitoring.md)** - System monitoring
- **[Backup](operations/backup.md)** - Backup and restore

## 📈 Adoption

Process and strategy:

- **[Adoption Guide](adoption/guide.md)** - How to adopt these practices
- **[Development Strategy](adoption/strategy.md)** - Long-term development strategy

## 🔍 Quick Links

- [Main README](../README.md)
- [Project Structure](../PROJECT_STRUCTURE.md)
- [Changelog](../CHANGELOG.md)
- [GitHub Repository](https://github.com/octavianissuemonitoring/parser-law)

## 📝 Contributing

See [Development Guide](development/guide.md) for contribution guidelines.
"@

if ($DryRun) {
    Write-Host "[DRY RUN] Would create: docs/README.md" -ForegroundColor $ColorWarning
} else {
    Set-Content "docs/README.md" -Value $docsReadme
    Write-Host "✅ Created: docs/README.md" -ForegroundColor $ColorSuccess
}

Write-Host ""

# ============================================================================
# Step 10: Update Root README.md
# ============================================================================

Write-Host "📝 Step 10: Updating Root README.md" -ForegroundColor $ColorWarning
Write-Host "====================================" -ForegroundColor $ColorWarning
Write-Host ""

$newReadme = @"
# Parser Law - Legislație România 🇷🇴

> Modern API and scraper for Romanian legislation monitoring

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/octavianissuemonitoring/parser-law/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)

## 🚀 Quick Start

``````bash
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
``````

**⏱️ Setup time: 5 minutes**

For detailed instructions, see [Getting Started](docs/getting-started/).

## 📚 Documentation

- **[Getting Started](docs/getting-started/)** - Setup, local development, deployment
- **[Development](docs/development/)** - Coding standards, Git workflow, testing
- **[Architecture](docs/architecture/)** - System design, database, API
- **[Features](docs/features/)** - Categories, AI processing, web interface
- **[Operations](docs/operations/)** - Deployment, rollback, monitoring

[📖 Full Documentation Index](docs/README.md)

## 🏗️ Project Structure

``````
parser-law/
├── docs/              # 📚 All documentation
├── src/               # 🐍 Python source code
│   ├── scraper/       # Scraping logic
│   ├── scheduler/     # Background jobs
│   ├── quality/       # Quality checks
│   └── config/        # Configuration
├── db_service/        # 🚀 FastAPI service
├── tests/             # 🧪 All tests
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── scripts/           # 🔧 Automation scripts
├── docker/            # 🐳 Docker configs
└── data/              # 💾 Runtime data
``````

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

We welcome contributions! See [Development Guide](docs/development/guide.md) for:

- Code standards and best practices
- Git workflow (feature branches, PRs)
- Testing requirements
- Release process

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🔗 Links

- **API Docs**: http://legislatie.issuemonitoring.ro/docs
- **Health Check**: http://legislatie.issuemonitoring.ro/health
- **GitHub**: https://github.com/octavianissuemonitoring/parser-law
- **Issues**: https://github.com/octavianissuemonitoring/parser-law/issues

## 📞 Support

- Create an [Issue](https://github.com/octavianissuemonitoring/parser-law/issues)
- See [Documentation](docs/)
- Check [FAQ](docs/getting-started/quickstart.md#faq)

---

**Made with ❤️ for Romanian legislation transparency**
"@

if ($DryRun) {
    Write-Host "[DRY RUN] Would update: README.md" -ForegroundColor $ColorWarning
} else {
    # Backup old README
    if (Test-Path "README.md") {
        Copy-Item "README.md" "README.md.v1.backup" -Force
        Write-Host "📄 Backed up old README.md → README.md.v1.backup" -ForegroundColor $ColorInfo
    }
    
    Set-Content "README.md" -Value $newReadme
    Write-Host "✅ Updated: README.md" -ForegroundColor $ColorSuccess
}

Write-Host ""

# ============================================================================
# Step 11: Summary
# ============================================================================

Write-Host "🎉 Restructure Complete!" -ForegroundColor $ColorSuccess
Write-Host "=========================" -ForegroundColor $ColorSuccess
Write-Host ""

Write-Host "📊 Summary:" -ForegroundColor $ColorInfo
Write-Host "   - Created new folder structure (docs/, src/, tests/, docker/, data/)" -ForegroundColor White
Write-Host "   - Moved 18 documentation files to docs/" -ForegroundColor White
Write-Host "   - Moved 7 Python files to src/" -ForegroundColor White
Write-Host "   - Moved 2 Docker configs to docker/" -ForegroundColor White
Write-Host "   - Moved runtime data to data/" -ForegroundColor White
Write-Host "   - Created Python package structure (__init__.py files)" -ForegroundColor White
Write-Host "   - Created documentation index (docs/README.md)" -ForegroundColor White
Write-Host "   - Updated root README.md" -ForegroundColor White
Write-Host ""

Write-Host "⚠️  IMPORTANT: Next Steps" -ForegroundColor $ColorWarning
Write-Host "=========================" -ForegroundColor $ColorWarning
Write-Host ""
Write-Host "1. Update Python imports in:" -ForegroundColor White
Write-Host "   - src/scheduler/scheduler.py" -ForegroundColor Gray
Write-Host "   - db_service/app/*.py" -ForegroundColor Gray
Write-Host "   - scripts/*.py" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Update Docker Compose paths:" -ForegroundColor White
Write-Host "   - docker-compose.yml" -ForegroundColor Gray
Write-Host "   - docker-compose.dev.yml" -ForegroundColor Gray
Write-Host "   - docker-compose.scheduler.yml" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Update documentation cross-references:" -ForegroundColor White
Write-Host "   - Fix internal links in docs/" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Test everything:" -ForegroundColor White
Write-Host "   pytest tests/" -ForegroundColor Gray
Write-Host "   docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Commit changes:" -ForegroundColor White
Write-Host "   git add -A" -ForegroundColor Gray
Write-Host "   git commit -m 'refactor: Restructure project for v2.0.0'" -ForegroundColor Gray
Write-Host ""

if ($DryRun) {
    Write-Host "This was a DRY RUN - no changes were made." -ForegroundColor $ColorWarning
    Write-Host "Run without -DryRun flag to apply changes." -ForegroundColor $ColorWarning
}

Write-Host ""
Write-Host "Need help? See PROJECT_STRUCTURE.md" -ForegroundColor $ColorInfo
Write-Host ""
"@

Set-Content "scripts/restructure-v2.ps1" -Value $newReadme
Write-Host "✅ Created: scripts/restructure-v2.ps1" -ForegroundColor $ColorSuccess
