# AI API Testing Script

## Overview
Comprehensive test suite for all AI Processing API endpoints.

## Usage

### Test VPS (default)
```powershell
.\scripts\test-ai-endpoints.ps1
```

### Test Local Environment
```powershell
.\scripts\test-ai-endpoints.ps1 -BaseUrl "http://localhost:8000"
```

### Verbose Output
```powershell
.\scripts\test-ai-endpoints.ps1 -Verbose
```

## Tested Endpoints

### 1. Document Retrieval
- ✅ `GET /api/v1/ai/acte/pending` - Get pending acts for AI processing
- ✅ `GET /api/v1/ai/acte/{id}` - Get specific act with full article structure

### 2. Status Management
- ✅ `GET /api/v1/ai/status` - Get overall AI processing statistics
- ✅ `GET /api/v1/ai/pending` - Get pending articles list
- ✅ `GET /api/v1/ai/errors` - Get articles with processing errors

### 3. Status Updates (POST endpoints - informational only)
- `POST /api/v1/ai/articole/{id}/mark-processing`
- `POST /api/v1/ai/articole/{id}/mark-processed`
- `POST /api/v1/ai/articole/{id}/mark-error`
- `POST /api/v1/ai/retry/{id}`
- `POST /api/v1/ai/reset/{id}`

### 4. Processing Triggers
- ✅ `GET /api/v1/ai/process/sync` - Get sync processing stats
- `POST /api/v1/ai/process` - Trigger AI processing (not tested - requires background task)

## Exit Codes
- `0` - All tests passed
- `1` - Some tests failed

## Example Output

```
╔════════════════════════════════════════════════════════════╗
║       AI Processing API Endpoints - Test Suite            ║
╚════════════════════════════════════════════════════════════╝
Testing endpoint: http://109.123.249.228:8000/api/v1

┌─────────────────────────────────────────────────────────┐
│ 1. Document Retrieval Endpoints                        │
└─────────────────────────────────────────────────────────┘
Testing: GET /ai/acte/pending ✓ PASSED
Testing: GET /ai/acte/{id} ✓ PASSED

╔════════════════════════════════════════════════════════════╗
║                     TEST SUMMARY                           ║
╚════════════════════════════════════════════════════════════╝

Total Tests:  6
Passed:       4
Failed:       2

✅ All critical AI endpoints are operational!
```

## Notes

### Known Issues
- Local environment may fail if database is empty
- Some endpoints may require specific test data
- POST endpoints are not tested to avoid modifying data

### Data Requirements
For full test coverage, database should contain:
- At least one act with `ai_status = 'pending'`
- At least one article with `ai_status = 0` (pending)
- Optional: Articles with `ai_status = 3` (error) for error testing

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Test AI Endpoints
  run: |
    .\scripts\test-ai-endpoints.ps1 -BaseUrl "http://localhost:8000"
```

### Jenkins Example
```groovy
stage('Test AI Endpoints') {
    steps {
        powershell '.\scripts\test-ai-endpoints.ps1 -BaseUrl "http://localhost:8000"'
    }
}
```
