# Test AI Processing & Export Features
# Usage: .\test-ai-features.ps1

param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$ApiKey = ""
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Blue
Write-Host "Testing AI Processing & Export Features" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""
Write-Host "API URL: $ApiUrl"
Write-Host ""

# Test 1: Health Check
Write-Host "Test 1: Health Check" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$ApiUrl/health" -Method Get
    Write-Host "✓ Health check passed" -ForegroundColor Green
    Write-Host "  Status: $($response.status)" -ForegroundColor Gray
} catch {
    Write-Host "✗ Health check failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 2: Root endpoint (check routes)
Write-Host "Test 2: Check API Routes" -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "$ApiUrl/" -Method Get
    
    if ($response.endpoints.ai_processing) {
        Write-Host "✓ AI processing routes: $($response.endpoints.ai_processing)" -ForegroundColor Green
    } else {
        Write-Host "✗ AI processing routes not found" -ForegroundColor Red
    }
    
    if ($response.endpoints.export) {
        Write-Host "✓ Export routes: $($response.endpoints.export)" -ForegroundColor Green
    } else {
        Write-Host "✗ Export routes not found" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Failed to fetch routes: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Test 3: AI Status (requires API key)
if ($ApiKey) {
    Write-Host "Test 3: AI Processing Status" -ForegroundColor Cyan
    try {
        $headers = @{
            "X-API-Key" = $ApiKey
            "Content-Type" = "application/json"
        }
        $response = Invoke-RestMethod -Uri "$ApiUrl/api/v1/ai/status" -Method Get -Headers $headers
        Write-Host "✓ AI status retrieved" -ForegroundColor Green
        Write-Host "  Pending: $($response.pending_count)" -ForegroundColor Gray
        Write-Host "  Processing: $($response.processing_count)" -ForegroundColor Gray
        Write-Host "  Completed: $($response.completed_count)" -ForegroundColor Gray
        Write-Host "  Errors: $($response.error_count)" -ForegroundColor Gray
        Write-Host "  Total: $($response.total_count)" -ForegroundColor Gray
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq 401) {
            Write-Host "✗ Unauthorized: API key missing or invalid" -ForegroundColor Red
        } elseif ($statusCode -eq 403) {
            Write-Host "✗ Forbidden: Invalid API key" -ForegroundColor Red
        } else {
            Write-Host "✗ Failed to get AI status: $_" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    
    # Test 4: Export Status
    Write-Host "Test 4: Export Status" -ForegroundColor Cyan
    try {
        $headers = @{
            "X-API-Key" = $ApiKey
            "Content-Type" = "application/json"
        }
        $response = Invoke-RestMethod -Uri "$ApiUrl/api/v1/export/status" -Method Get -Headers $headers
        Write-Host "✓ Export status retrieved" -ForegroundColor Green
        Write-Host "  Pending: $($response.pending_count)" -ForegroundColor Gray
        Write-Host "  Completed: $($response.completed_count)" -ForegroundColor Gray
        Write-Host "  Errors: $($response.error_count)" -ForegroundColor Gray
        Write-Host "  Total AI-processed: $($response.total_acts_with_ai)" -ForegroundColor Gray
    } catch {
        Write-Host "✗ Failed to get export status: $_" -ForegroundColor Red
    }
} else {
    Write-Host "⚠ Skipping authenticated tests (no API key provided)" -ForegroundColor Yellow
    Write-Host "  Run with -ApiKey parameter to test protected endpoints" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host "Tests Complete!" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue

# Examples
Write-Host ""
Write-Host "💡 Examples:" -ForegroundColor Yellow
Write-Host ""
Write-Host "# Test with API key:"
Write-Host '.\test-ai-features.ps1 -ApiKey "your_api_key_here"' -ForegroundColor Gray
Write-Host ""
Write-Host "# Test remote server:"
Write-Host '.\test-ai-features.ps1 -ApiUrl "https://legislatie.issuemonitoring.ro" -ApiKey "your_key"' -ForegroundColor Gray
Write-Host ""
Write-Host "# Trigger AI processing:"
Write-Host 'curl -X POST http://localhost:8000/api/v1/ai/process -H "X-API-Key: YOUR_KEY" -H "Content-Type: application/json" -d "{\"limit\": 5}"' -ForegroundColor Gray
Write-Host ""
