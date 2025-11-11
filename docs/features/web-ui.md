# Web Interface - Legislation Management

## Overview

User-friendly web interface for managing legislation sources and viewing normative acts.

## Features

### 1. 🔗 **Link Management**
- Add new legislation URLs via form
- View all registered sources
- Statistics: acts count per source
- Automatic validation

### 2. 📋 **Acts List**
- Grid/List view toggle
- Real-time search (title, number, year)
- Filters by type (LEGE, OUG, HG, etc.)
- Sort by date/number
- Click to view full details

### 3. 📑 **Structured Index**
- Select act from dropdown
- View organized structure:
  - Chapters
  - Articles with titles
  - Click to view article content
- Navigate hierarchy

### 4. 📊 **Statistics Dashboard**
- Total acts count
- Unique sources count
- Top sources by acts count
- Visual statistics cards

## Access

**Production:** https://legislatie.issuemonitoring.ro/static/index.html

**API Documentation:** https://legislatie.issuemonitoring.ro/docs

## API Endpoints

### Links Management

```bash
# Get statistics
GET /api/v1/links/stats

# List all links with acts count
GET /api/v1/links/

# Add new link
POST /api/v1/links/
Content-Type: application/json
{
  "url": "https://legislatie.just.ro/...",
  "description": "Optional description"
}
```

### Acts

```bash
# List acts with filters
GET /api/v1/acte?limit=50&search=fiscal&tip=LEGE

# Get act details
GET /api/v1/acte/{id}

# Get articles
GET /api/v1/articole?act_id={id}
```

## Usage Examples

### 1. Add Legislation Link

```bash
curl -X POST https://legislatie.issuemonitoring.ro/api/v1/links/ \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://legislatie.just.ro/Public/DetaliiDocument/123456",
    "description": "Legea nr. 227/2015 - Codul Fiscal"
  }'
```

### 2. Get Statistics

```bash
curl https://legislatie.issuemonitoring.ro/api/v1/links/stats
```

Response:
```json
{
  "total_acts": 1250,
  "total_unique_links": 45,
  "top_sources": [
    {
      "url": "https://legislatie.just.ro/...",
      "acts_count": 235
    }
  ]
}
```

### 3. Search Acts

```bash
curl "https://legislatie.issuemonitoring.ro/api/v1/acte?search=codul%20fiscal&limit=10"
```

## Technology Stack

**Frontend:**
- Pure HTML5/CSS3/JavaScript
- No external dependencies
- Responsive design
- Modern UI with gradients

**Backend:**
- FastAPI (Python)
- PostgreSQL database
- RESTful API
- Async operations

## Deployment

### Quick Deploy

```bash
# Using PowerShell (Windows)
.\scripts\deploy-web-interface.ps1

# Using Bash (Linux/Mac)
./scripts/deploy-web-interface.sh
```

### Manual Deploy

```bash
# 1. Commit and push
git add .
git commit -m "Add web interface"
git push origin master

# 2. Deploy to VPS
ssh root@77.237.235.158
cd /opt/parser-law
git pull origin master

# 3. Restart container
cd db_service
docker-compose restart legislatie_api

# 4. Verify
curl http://localhost:8000/api/v1/links/stats
```

## File Structure

```
db_service/
├── app/
│   ├── main.py                      # FastAPI app with routes + static files
│   ├── static/
│   │   └── index.html               # Web interface (570 lines)
│   └── api/
│       └── routes/
│           └── links.py             # Links management API (137 lines)
├── scripts/
│   ├── deploy-web-interface.sh      # Bash deployment script
│   └── deploy-web-interface.ps1     # PowerShell deployment script
└── WEB_INTERFACE_README.md          # This file
```

## UI Screenshots

### Links Tab
- Form: URL input + description
- List: All registered sources with acts count
- Add button with validation

### Acts Tab
- Search bar + filters (type, sort)
- Grid/List toggle
- Cards with metadata (number, year, type, emitent)
- Click to view details

### Index Tab
- Dropdown: Select act
- Tree view: Chapters → Articles
- Click to expand/view content

### Stats Tab
- Statistics cards (total acts, sources)
- Top sources list with counts

## Troubleshooting

### Static files not serving

**Problem:** 404 on `/static/index.html`

**Solution:**
```bash
# Ensure directory exists
mkdir -p /opt/parser-law/db_service/app/static

# Check file is present
ls -la /opt/parser-law/db_service/app/static/index.html

# Restart container
cd /opt/parser-law/db_service
docker-compose restart legislatie_api
```

### Links endpoint not responding

**Problem:** 404 on `/api/v1/links/`

**Solution:**
```bash
# Verify route registered
curl http://localhost:8000/ | grep links

# Check logs
docker logs legislatie_api | grep links

# Restart
docker-compose restart legislatie_api
```

### CORS errors in browser

**Problem:** Browser blocks API calls

**Solution:** Check `config.py`:
```python
cors_origins: list[str] = ["*"]  # Allow all origins
cors_allow_credentials: bool = True
cors_allow_methods: list[str] = ["*"]
cors_allow_headers: list[str] = ["*"]
```

## Development

### Local Testing

```bash
# 1. Install dependencies
cd db_service
pip install -r requirements.txt

# 2. Create static directory
mkdir -p app/static

# 3. Copy index.html
cp path/to/index.html app/static/

# 4. Run locally
python -m app.main
# or
uvicorn app.main:app --reload

# 5. Open browser
open http://localhost:8000/static/index.html
```

### Adding New Features

1. **New API Endpoint:** Add to `app/api/routes/links.py`
2. **New UI Tab:** Edit `app/static/index.html`
3. **New Styles:** Add to `<style>` section in index.html
4. **New JS Function:** Add to `<script>` section

## Security

- API calls from browser use CORS (configured in `config.py`)
- No authentication required for read operations (GET)
- Write operations (POST) available to all (consider adding auth)
- Input validation on backend via Pydantic schemas

## Performance

- **Frontend:** Single HTML file, no external dependencies → fast load
- **Backend:** Async FastAPI → handles concurrent requests
- **Database:** PostgreSQL with indexes → fast queries
- **Caching:** Browser caches static files

## Future Enhancements

1. **Authentication:** Add user accounts for write operations
2. **WebSockets:** Real-time updates when new acts scraped
3. **Export:** Download acts as PDF/DOCX
4. **Advanced Search:** Full-text search in articles
5. **Bookmarks:** Save favorite acts
6. **Dark Mode:** Theme toggle
7. **Mobile App:** PWA support

## Support

**Documentation:** https://github.com/yourusername/parser-law/blob/master/WEB_INTERFACE_README.md

**API Docs:** https://legislatie.issuemonitoring.ro/docs

**Issues:** Check logs with `docker logs legislatie_api`

## License

Same as main project.
