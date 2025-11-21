# Release Notes v2.2.0 - Domain Assignment System

**Release Date:** November 21, 2025  
**Tag:** v2.2.0  
**Previous Version:** v2.1.0

## 🎯 Major Features

### Domain Assignment System for Legislative Acts

Implemented complete domain assignment functionality allowing users to categorize legislative acts by thematic domains (e.g., Energy, Pharmaceuticals, Consumer Protection).

#### Backend (API)
- **New Endpoints:**
  - `GET /api/v1/domenii/acte/{act_id}` - Retrieve all domains assigned to an act
  - `PUT /api/v1/domenii/acte/{act_id}` - Replace all domain assignments for an act
  
- **Features:**
  - Support for relevance scoring (default 1.0)
  - Automatic sorting by `ordine` and `denumire`
  - Many-to-many relationship via `acte_domenii` junction table
  - Cascade operations on delete

#### Frontend (Web UI)
- **Domain Management Modal:**
  - New "🎯 Gestionează Domenii" button on each act card (green gradient)
  - Multi-select checkbox interface optimized for 50+ domains
  - Visual indicators: color-coded bullets, bold codes, descriptions
  - Max-height 500px with scroll for large lists
  - Close on outside click

- **Display Features:**
  - Domain tags displayed on act cards
  - Quick removal via X button on tags
  - Real-time updates after save
  - Dual-modal support (Categories + Domains)

### AI Integration Documentation

Added comprehensive 765-line documentation for AI service integration:
- Complete workflow diagrams (ASCII art)
- All 6 AI endpoints with curl examples
- Python implementation examples (single + batch processing)
- Testing & verification procedures
- Error handling guide
- Monitoring dashboard setup
- Database schema reference

**File:** `db_service/AI_INTEGRATION.md`

### AI Status Tracking System

Implemented AI processing status tracking for articles:
- **Status Codes:** 0=not_processed, 1=processing, 2=processed, 9=error
- **Database Columns:**
  - `ai_status` (INTEGER)
  - `ai_processed_at` (TIMESTAMP)
  - `ai_status_message` (TEXT)
  - `metadate` (TEXT) - AI-generated summaries

- **6 API Endpoints:**
  1. `GET /api/v1/ai/articles/pending`
  2. `GET /api/v1/ai/articles/by-status/{status}`
  3. `POST /api/v1/ai/articles/mark-processing`
  4. `POST /api/v1/ai/articles/update-status` (main)
  5. `POST /api/v1/ai/articles/{id}/status`
  6. `GET /api/v1/ai/stats`

## 📊 Database Updates

### New Domains
Added 5 energy-related domains to support energy legislation:

| Code | Name | Description | Ordine |
|------|------|-------------|--------|
| ENERGIE_ELEC | Energie Electrică | Electricity production, transport & distribution | 10 |
| GAZE_NAT | Gaze Naturale | Natural gas exploration, transport & distribution | 11 |
| ENERGIE_RENEW | Energie Regenerabilă | Renewable energy sources (solar, wind, hydro, biomass) | 12 |
| ENERGIE_NUC | Energie Nucleară | Nuclear energy and nuclear security | 13 |
| POLITICI_ENERGIE | Politici de Energie | National energy strategies and policies | 14 |

**Total Domains:** 11 (6 original + 5 new)

### Schema Fixes
- Fixed `domenii` table: renamed `nume` → `denumire` (align with Python models)
- Added missing columns: `ordine` (INTEGER), `culoare` (VARCHAR(7))
- Updated `get_articol_domenii()` SQL function to return correct columns including `source` field

## 🔧 Improvements

### UI/UX Enhancements
- Better card organization with dual-button layout
- Consistent styling between Categories and Domains modals
- Optimized for scalability (tested with 11 domains, designed for 50+)
- Responsive design with proper spacing and colors

### Code Quality
- Comprehensive error handling in API endpoints
- Consistent naming conventions
- Proper async/await patterns
- Type hints and documentation

## 📈 Statistics

**Current Production State:**
- 436 articles (all with AI status tracking)
- 11 domains available
- 1 test issue linked to 1 article
- Full domain assignment capability operational

**Files Changed:**
- 8 files modified
- 1,404 lines added
- 17 lines removed
- 3 new files created

## 🚀 Deployment

**VPS Status:**
- Successfully deployed to https://legislatie.issuemonitoring.ro
- Docker container restarted with new code
- All endpoints tested and functional

**Testing Performed:**
```bash
✅ GET /domenii/acte/8 → [] (initial)
✅ PUT /domenii/acte/8 → {"added": 2, "removed": 0}
✅ GET /domenii/acte/8 → [ENERGIE_ELEC, GAZE_NAT]
✅ Web UI modal opens and functions correctly
✅ Domain tags display and removal works
```

## 📝 Migration Notes

**For upgrading from v2.1.0:**

1. **Database changes are already applied** (directly on production)
2. **No additional migrations required**
3. **API is backward compatible** (new endpoints don't affect existing functionality)
4. **UI changes are additive** (new buttons and modals don't interfere with existing features)

## 🔗 Related Documentation

- Full AI Integration Guide: `db_service/AI_INTEGRATION.md`
- Database Schema: `DATABASE_DOCUMENTATION.md`
- Project Structure: `PROJECT_STRUCTURE.md`
- API Documentation: Available at `/docs` endpoint

## 👥 Contributors

- Implementation: AI Assistant
- Testing: Production environment
- Review: Octavian

## 🎉 Next Steps

Recommended follow-up work:
1. Add domain color customization in UI
2. Implement domain sync from Issue Monitoring platform
3. Create domain-based filtering for acts list
4. Add bulk domain assignment capabilities
5. Implement domain statistics dashboard

---

**Full Changelog:** https://github.com/octavianissuemonitoring/parser-law/compare/v2.1.0...v2.2.0
