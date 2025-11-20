# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.1] - 2025-11-20

### Fixed - Database Schema Consistency

#### Schema Corrections
- **Migration 005** (`1007e30b0c57`): Fixed `metadate` column type from TEXT to JSONB
  - Converted `acte_legislative.metadate` to JSONB for proper JSON handling
  - Converted `articole.metadate` to JSONB for proper JSON handling
  - Migration applied directly on VPS via SQL (alembic connection issues resolved manually)

#### Infrastructure & Tooling
- Fixed Docker build context in `docker-compose.yml` from `.` to `..` (parent directory)
- Created comprehensive database structure comparison script (`compare_db_structures.ps1`)
  - Automated comparison of all 14 tables between LOCAL and VPS
  - Generates HTML + text reports with detailed diff analysis
  - Identifies column type mismatches, missing columns, and structural differences

- Created database export scripts for both environments:
  - `export_local_to_excel.ps1` - Export LOCAL database to Excel (9 tables)
  - `export_vps_to_excel.ps1` - Export VPS database to Excel via SSH
  - Includes combined workbook with all tables + individual sheet files

- Created VPS-to-LOCAL sync script (`sync_vps_to_local.ps1`)
  - Exports VPS articole table as SQL dump
  - Creates backup of LOCAL data before sync
  - Imports 712 missing articles from VPS (1095 total)
  - Verifies data quality after import

#### Verification Results
- ✅ 12/14 tables structurally identical between LOCAL and VPS
- ✅ 2/14 tables (acte_legislative, articole) fixed with metadate JSONB conversion
- ✅ 4 tables with cosmetic differences (column order only, no functional impact)
- ✅ All 1095 articles preserved on VPS during deployment
- ✅ Final status: **100% functional parity** between environments

### Changed
- Docker build process now correctly references parent directory context
- Alembic migrations can be applied via direct SQL when container exec fails

## [2.1.0] - 2025-11-20

### Added - Issues System & Domains (AI Integration)

#### Database Schema
- **Migration 002**: Issues system with 4 junction tables
  - `articole_issues` - Link issues to articles (Tier 1)
  - `acte_issues` - Link issues to acts
  - `anexe_issues` - Link issues to annexes
  - `structure_issues` - Link issues to structures (Tier 2: titlu/capitol/sectiune)
  - 16 indexes for performance optimization
  - Dropped deprecated `articole.issue` TEXT column

- **Migration 003**: Domains/Categories system
  - `domenii` table with 6 seed domains (FARMA, DISP_MED, TUTUN, PROT_CONS, SANATATE, MEDIU)
  - `acte_domenii` - Act-level domain assignment
  - `articole_domenii` - Article-level domain override (optional)
  - `get_articol_domenii()` SQL function for domain inheritance
  - Extended `structure_issues` with `domeniu_id NOT NULL`

- **Migration 004**: AI processing columns
  - Added to `acte_legislative`: `ai_status`, `ai_processed_at`, `ai_error`, `metadate`, `export_status`, etc.
  - Added to `articole`: `ai_status`, `ai_processed_at`, `ai_error`, `metadate`, `issue_monitoring_id`
  - Indexes on `ai_status` for filtering

#### API Endpoints

**New Route: `/api/v1/domenii/`** (9 endpoints)
- `GET /domenii` - List all domains
- `GET/POST/PUT/DELETE /domenii/{id}` - CRUD operations
- `POST /domenii/acte/{act_id}/assign` - Assign domain to act
- `DELETE /domenii/acte/{act_id}/unassign/{domeniu_id}` - Remove domain from act
- `POST /domenii/articole/{articol_id}/assign` - Override domain for article
- `DELETE /domenii/articole/{articol_id}/unassign/{domeniu_id}` - Remove article override

**Extended: `/api/v1/issues/`** (+7 endpoints)
- `POST /issues` - Create new issue
- `PUT /issues/{id}` - Update issue
- `DELETE /issues/{id}` - Delete issue
- `POST /issues/link` - Link issue to document (Tier 1) with mandatory `domeniu_id`
- `DELETE /issues/unlink` - Remove Tier 1 link
- `POST /issues/link-structure` - Link issue to structure (Tier 2: titlu/capitol/sectiune)
- `DELETE /issues/unlink-structure` - Remove Tier 2 link

**Extended: `/api/v1/articole/`**
- `GET /articole/{id}/with-issues?domeniu_id=X` - Get article with Tier 1 issues and effective domains

**Unified: `/api/v1/ai/`** (All AI endpoints now under single prefix)
- `GET /ai/acte/pending` - Get acts needing AI processing (filter by `ai_status`, `has_domenii`)
- `GET /ai/acte/{id}` - **Main endpoint** - Get complete act with ALL articles in hierarchical structure
- `POST /ai/articole/{id}/mark-processing` - Mark article as being processed
- `POST /ai/articole/{id}/mark-processed` - Mark article as successfully processed
- `POST /ai/articole/{id}/mark-error` - Mark article as failed with error message
- Existing: `POST /ai/process`, `GET /ai/status`, `GET /ai/pending`, `GET /ai/errors`, `POST /ai/retry/{id}`

#### Models & Schemas

**New SQLAlchemy Models** (`app/models/`)
- `Domeniu` - Domain/category entity
- `ActDomeniu` - Act-domain junction with relevance score
- `ArticolDomeniu` - Article-domain override junction
- `ArticolIssue` - Article-issue junction (Tier 1)
- `ActIssue` - Act-issue junction
- `AnexaIssue` - Annex-issue junction
- `StructureIssue` - Structure-issue junction (Tier 2)

**New Pydantic Schemas** (`app/schemas/`)
- `domeniu_schema.py`: 9 schemas (DomeniuCreate/Update/Response, ActDomeniuAssign, ArticolDomeniuAssign, DomeniuWithSource, etc.)
- `issue_schema.py`: 14 schemas (IssueCreate/Update/Response, IssueLinkCreate, StructureIssueLinkCreate, IssueWithContext, etc.)
- Extended `articol_schema.py`: ArticolWithIssues, ArticolWithFullContext
- AI processing schemas: `ActForAI`, `ArticolForAI`, `ActListItemForAI`

#### Architecture Changes

**Domain Context Rules**
- All issues **MUST** have domain context (`domeniu_id NOT NULL`)
- Domain inheritance: Act → Article (with optional article-level override)
- `get_articol_domenii()` function returns effective domains with source indicator

**Issue Tiers**
- **Tier 1** (Direct): Issues linked directly to documents (articol/act/anexa)
- **Tier 2** (Structure): Issues linked to structural elements (titlu/capitol/sectiune) for UI tree display

**AI Workflow**
1. GET `/ai/acte/pending` - Find acts with `ai_status=pending` and domains assigned
2. GET `/ai/acte/{id}` - Retrieve complete act with all articles (text, hierarchy, status)
3. POST `/ai/articole/{id}/mark-processing` - Mark as in-progress
4. Analyze article text with AI
5. POST `/issues` - Create issues
6. POST `/issues/link` - Link issues to articles (Tier 1) with domain and relevance score
7. POST `/issues/link-structure` - Link issues to structures (Tier 2) if applicable
8. POST `/ai/articole/{id}/mark-processed` - Mark as completed

#### Documentation
- `docs/features/AI_INTEGRATION.md` - Complete AI integration guide with:
  - Architecture flow diagrams
  - All endpoint specifications with examples
  - Python sample code for complete processing loop
  - Domain context rules and inheritance logic
  - Error handling and retry strategies
  - Testing procedures

### Changed
- Removed deprecated `articole.issue` TEXT field (replaced by junction table)
- Unified all AI endpoints under `/api/v1/ai/` prefix (was `/api/v1/ai-integration/`)
- Extended `Articol`, `ActLegislativ`, `Anexa` models with relationships to new junction tables

### Technical Details
- **Database**: 4 new junction tables, 3 domain tables, 25+ new columns, 20+ indexes
- **API**: 23+ new endpoints across 3 route files
- **Schemas**: 32 new Pydantic models
- **Models**: 7 new SQLAlchemy models
- **Functions**: 1 PostgreSQL helper function
- **Seed Data**: 6 domains with colors and ordering

---

## [2.0.0] - 2025-11-XX (Skipped - should have been baseline)

### Note
Version 2.0.0 was skipped. The work done between 1.0.0 and 2.1.0 should have been labeled as 2.0.0 (major version bump for breaking changes), but was developed directly as 2.1.0.

---

## [1.0.0] - 2025-XX-XX

### Initial Release

#### Core Features
- Legislative acts scraping and parsing
- PostgreSQL database with `legislatie` schema
- FastAPI REST API
- Complete CRUD operations for acts and articles
- Hierarchical structure support (titluri, capitole, sectiuni)

#### Database Schema
- `acte_legislative` - Legislative acts
- `articole` - Articles
- `anexe` - Annexes
- `acte_modificari` - Act modifications
- Basic relationships and indexes

#### API Endpoints
- `/api/v1/acte/` - Acts management
- `/api/v1/articole/` - Articles management
- `/api/v1/stats/` - Statistics
- `/api/v1/export/` - Export functionality
- `/api/v1/links/` - Link management
- `/api/v1/categories/` - Categories

#### Features
- Scraping from legislatie.just.ro
- HTML content parsing
- Search and filtering
- Pagination
- Export to various formats
- Basic AI processing placeholder

---

## Version Strategy

### Semantic Versioning (MAJOR.MINOR.PATCH)

- **MAJOR** (X.0.0): Breaking changes, major architecture redesign
  - Database schema breaking changes
  - API endpoint removals or incompatible changes
  - Major feature overhauls

- **MINOR** (x.Y.0): New features, backwards-compatible additions
  - New API endpoints
  - New database tables (non-breaking)
  - New functionality additions
  - Schema extensions (adding columns with defaults)

- **PATCH** (x.y.Z): Bug fixes, minor improvements
  - Bug fixes
  - Performance improvements
  - Documentation updates
  - Small refactorings

### Release Process

1. **Development**: Work on `main` branch or feature branches
2. **Version Update**: Update version in:
   - `pyproject.toml`
   - `db_service/app/config.py` (`api_version`)
3. **Changelog**: Document changes in `CHANGELOG.md`
4. **Git Tag**: Create annotated tag with version
   ```bash
   git tag -a v2.1.0 -m "Release v2.1.0 - Issues System & AI Integration"
   git push origin v2.1.0
   ```
5. **Deploy**: Deploy to VPS using deployment scripts

### Git Tags

Use annotated tags for releases:
- Format: `vMAJOR.MINOR.PATCH` (e.g., `v2.1.0`)
- Include release notes in tag message
- Push tags to GitHub: `git push origin --tags`

### Deployment Versioning

API returns version in:
- `/health` endpoint: `{"version": "2.1.0"}`
- `/` root endpoint: `{"version": "2.1.0"}`
- OpenAPI spec: `"version": "2.1.0"`
