# Parser Law - Legislație România 🇷🇴

> Modern API and scraper for Romanian legislation monitoring

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/octavianissuemonitoring/parser-law/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)

## 📋 Prerequisites

- **Python 3.11+** with pip
- **Docker 24.x** and Docker Compose 2.x
- **PostgreSQL 15** (via Docker)
- **Git**

Optional for VPS deployment:
- **Nginx** (reverse proxy)
- **Certbot** (SSL certificates)

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/octavianissuemonitoring/parser-law.git
cd parser-law

# 2. Install Python dependencies (for scraper)
pip3 install -r requirements-scheduler.txt

# 3. Setup environment
cp .env.example .env
# Edit .env with your settings

# 4. Start services
docker-compose up -d

# 5. Test scraper
python3 scraper_legislatie.py

# 6. Access API
open http://localhost:8000/docs
```

⏱️ Setup time: 5 minutes

For detailed instructions, see Getting Started in docs/getting-started/.

## 📚 Documentation

- Getting Started (docs/getting-started/) — Setup, local development, deployment
- Development (docs/development/) — Coding standards, Git workflow, testing
- Architecture (docs/architecture/) — System design, database, API
- Features (docs/features/) — Categories, AI processing, web interface
- Operations (docs/operations/) — Deployment, rollback, monitoring

Full documentation index: docs/README.md

## 🏗️ Project Structure

```
parser-law/
├── docs/              # All documentation
├── src/               # Python source code
│   ├── scraper/       # Scraping logic
│   ├── scheduler/     # Background jobs
│   ├── quality/       # Quality checks
│   └── config/        # Configuration
├── db_service/        # FastAPI service
├── tests/             # All tests
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── scripts/           # Automation scripts
├── docker/            # Docker configs
└── data/              # Runtime data
```

See PROJECT_STRUCTURE.md for details.

## 🛠️ Tech Stack

- API: FastAPI 0.104+ (Python 3.11)
- Database: PostgreSQL 15
- Scraping: BeautifulSoup4, Requests
- Scheduler: APScheduler
- Testing: Pytest, Coverage
- CI/CD: GitHub Actions
- Deployment: Docker Compose

## 📦 Features

- Scrape legislation from legislatie.just.ro
- Parse HTML and extract metadata
- REST API with full CRUD operations
- Category management and assignment
- Scheduled updates (daily/weekly)
- Quality checks and validation
- Export to CSV/JSON
- Full-text search
- Database migrations (Alembic)

## 🤝 Contributing

We welcome contributions! See Development Guide at docs/development/guide.md for:

- Code standards and best practices
- Git workflow (feature branches, PRs)
- Testing requirements
- Release process

## 📝 License

MIT License — see LICENSE

## 🔗 Links

- API Docs: http://legislatie.issuemonitoring.ro/docs
- Health Check: http://legislatie.issuemonitoring.ro/health
- GitHub: https://github.com/octavianissuemonitoring/parser-law
- Issues: https://github.com/octavianissuemonitoring/parser-law/issues

## 📞 Support

- Create an Issue at https://github.com/octavianissuemonitoring/parser-law/issues
- See Documentation in docs/
- Check FAQ at docs/getting-started/quickstart.md#faq

---

Made with ❤️ for Romanian legislation transparency
