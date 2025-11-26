# Deployment Plan: AI Status API Unification

**Date:** November 26, 2025  
**Change Type:** API Enhancement (Backward Compatible)  
**Impact:** LOW (Old endpoints still functional)

---

## 📋 Summary

Implemented a new unified endpoint for AI status management that consolidates 3 separate endpoints into one flexible API.

### Changes Made:

1. **New Endpoint:** `POST /api/v1/ai/articles/update-status`
2. **Deprecated (but still functional):**
   - `POST /api/v1/ai/articole/{id}/mark-processing`
   - `POST /api/v1/ai/articole/{id}/mark-processed`
   - `POST /api/v1/ai/articole/{id}/mark-error`

---

## 🎯 New Features

### Unified Status Update API

**Endpoint:** `POST /api/v1/ai/articles/update-status`

**Request:**
```json
{
  "article_id": 1234,
  "status": 2,  // 0=pending, 1=processing, 2=completed, 3=error, 9=skipped
  "explanation": "Optional text explanation"
}
```

**Response:**
```json
{
  "success": true,
  "article_id": 1234,
  "previous_status": 1,
  "new_status": 2,
  "updated_at": "2025-11-26T12:34:56.789Z"
}
```

### Supported Status Values:
- `0` = **pending** - Reset article to unprocessed
- `1` = **processing** - Currently being analyzed
- `2` = **completed** - Successfully processed
- `3` = **error** - Processing failed
- `9` = **skipped** - Intentionally skipped (new)

---

## 📁 Files Modified

1. **`db_service/app/api/routes/ai_processing.py`**
   - Added `AI_STATUS_SKIPPED = 9` constant
   - Added `VALID_AI_STATUSES` set for validation
   - Added `UpdateStatusRequest` and `UpdateStatusResponse` Pydantic models
   - Added new unified endpoint `POST /articles/update-status`
   - Marked old endpoints as `deprecated=True`
   - Updated docstrings with migration instructions

2. **`db_service/AI_PROCESSING_API.md`**
   - Added comprehensive documentation for new endpoint
   - Added migration guide with code examples
   - Moved old endpoints to "DEPRECATED" section with collapsible details
   - Updated usage examples throughout the document
   - Added quick reference table for migration

---

## 🚀 Deployment Steps (VPS)

### 1. Backup Current State
```bash
ssh root@legislatie.issuemonitoring.ro
cd /root/parser-law
git stash  # Save any local changes
cp db_service/app/api/routes/ai_processing.py db_service/app/api/routes/ai_processing.py.backup
```

### 2. Pull Latest Changes
```bash
git pull origin main
```

### 3. Restart API Service
```bash
cd /root/parser-law
docker-compose restart api
```

### 4. Verify Deployment
```bash
# Check API is running
docker-compose ps

# Check logs
docker-compose logs -f api --tail=50

# Test new endpoint
curl -X POST https://legislatie.issuemonitoring.ro/api/v1/ai/articles/update-status \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"article_id": 1, "status": 1}'
```

### 5. Test Old Endpoints (Should Still Work)
```bash
# Test deprecated endpoint
curl -X POST https://legislatie.issuemonitoring.ro/api/v1/ai/articole/1/mark-processing \
  -H "X-API-Key: YOUR_KEY"
```

---

## ✅ Verification Checklist

- [ ] API service restarted successfully
- [ ] No errors in logs
- [ ] New endpoint `/articles/update-status` responds correctly
- [ ] Old endpoints still work (with deprecation warnings in OpenAPI docs)
- [ ] OpenAPI documentation updated at `/docs`
- [ ] All status values (0,1,2,3,9) work correctly
- [ ] `explanation` field is optional and stored properly

---

## 🔄 Rollback Plan

If issues occur:

```bash
# Restore backup
cd /root/parser-law/db_service/app/api/routes
cp ai_processing.py.backup ai_processing.py

# Restart
cd /root/parser-law
docker-compose restart api
```

Or revert git commit:
```bash
git log --oneline  # Find commit hash
git revert <commit-hash>
docker-compose restart api
```

---

## 📊 Migration Timeline

**Phase 1 (Now):**
- ✅ New API deployed alongside old endpoints
- ✅ Documentation updated
- Old endpoints marked as deprecated in OpenAPI

**Phase 2 (2 weeks from now):**
- Notify all AI service consumers
- Update any internal scripts to use new API

**Phase 3 (1 month from now):**
- Remove old endpoints completely
- Update documentation to remove deprecation notices

---

## 🧪 Test Commands

### Test New Unified API

```bash
API_KEY="your-api-key-here"
BASE_URL="https://legislatie.issuemonitoring.ro/api/v1"

# 1. Mark as processing
curl -X POST "$BASE_URL/ai/articles/update-status" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"article_id": 1, "status": 1}'

# 2. Mark as completed
curl -X POST "$BASE_URL/ai/articles/update-status" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"article_id": 1, "status": 2}'

# 3. Mark as error with explanation
curl -X POST "$BASE_URL/ai/articles/update-status" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"article_id": 1, "status": 3, "explanation": "Test error message"}'

# 4. Reset to pending
curl -X POST "$BASE_URL/ai/articles/update-status" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"article_id": 1, "status": 0}'

# 5. Mark as skipped
curl -X POST "$BASE_URL/ai/articles/update-status" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"article_id": 1, "status": 9, "explanation": "Article too short"}'
```

### Verify Database Updates

```bash
# SSH to VPS
ssh root@legislatie.issuemonitoring.ro

# Connect to database
docker exec -it parser-law-postgres psql -U parser_user -d monitoring_platform

# Check article status
SELECT id, articol_nr, ai_status, ai_error, ai_processed_at 
FROM legislatie.articole 
WHERE id = 1;
```

---

## 📞 Support

**Issues?** Contact the development team or check logs:
```bash
docker-compose logs -f api --tail=100
```

**API Documentation:** https://legislatie.issuemonitoring.ro/docs
