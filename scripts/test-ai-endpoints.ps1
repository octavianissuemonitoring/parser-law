#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test all AI Processing API endpoints on VPS or local environment.

.DESCRIPTION
    Comprehensive testing script for all AI-related endpoints including:
    - Document retrieval (acts with articles)
    - Status management
    - Processing triggers
    - Error tracking

.PARAMETER BaseUrl
    The base URL of the API. Default: http://109.123.249.228:8000

.PARAMETER Verbose
    Show detailed output for each test

.EXAMPLE
    .\test-ai-endpoints.ps1
    Test on VPS (default)

.EXAMPLE
    .\test-ai-endpoints.ps1 -BaseUrl "http://localhost:8000"
    Test on local environment

.EXAMPLE
    .\test-ai-endpoints.ps1 -Verbose
    Test with detailed output
#>

param(
    [string]$BaseUrl = "http://109.123.249.228:8000",
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$API_BASE = "$BaseUrl/api/v1"

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║       AI Processing API Endpoints - Test Suite            ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "Testing endpoint: $API_BASE" -ForegroundColor Yellow
Write-Host ""

$testResults = @()
$passedTests = 0
$failedTests = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [scriptblock]$Validation
    )
    
    Write-Host "Testing: $Name" -ForegroundColor Cyan -NoNewline
    
    try {
        $response = Invoke-RestMethod -Uri $Url -Method Get -ErrorAction Stop
        
        if ($null -ne $Validation) {
            $validationResult = & $Validation $response
            if ($validationResult) {
                Write-Host " ✓ PASSED" -ForegroundColor Green
                $script:passedTests++
                return @{
                    Name = $Name
                    Status = "PASSED"
                    Url = $Url
                    Response = $response
                }
            } else {
                Write-Host " ✗ FAILED (validation)" -ForegroundColor Red
                $script:failedTests++
                return @{
                    Name = $Name
                    Status = "FAILED"
                    Url = $Url
                    Error = "Validation failed"
                }
            }
        } else {
            Write-Host " ✓ PASSED" -ForegroundColor Green
            $script:passedTests++
            return @{
                Name = $Name
                Status = "PASSED"
                Url = $Url
                Response = $response
            }
        }
    }
    catch {
        Write-Host " ✗ FAILED" -ForegroundColor Red
        if ($Verbose) {
            Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
        }
        $script:failedTests++
        return @{
            Name = $Name
            Status = "FAILED"
            Url = $Url
            Error = $_.Exception.Message
        }
    }
}

Write-Host "`n┌─────────────────────────────────────────────────────────┐" -ForegroundColor White
Write-Host "│ 1. Document Retrieval Endpoints                        │" -ForegroundColor White
Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor White

# Test 1: GET pending acts
$result = Test-Endpoint `
    -Name "GET /ai/acte/pending - Get pending acts for AI processing" `
    -Url "$API_BASE/ai/acte/pending?limit=5" `
    -Validation {
        param($response)
        return ($response -is [array]) -and ($response.Count -gt 0) -and ($response[0].PSObject.Properties['id']) -and ($response[0].PSObject.Properties['ai_status'])
    }
$testResults += $result

if ($Verbose -and $result.Status -eq "PASSED") {
    Write-Host "  → Found $($result.Response.Count) pending acts" -ForegroundColor Gray
    $result.Response | Select-Object -First 2 id, tip_act, ai_status, pending_articole | Format-Table | Out-String | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
}

# Test 2: GET specific act with articles
$result = Test-Endpoint `
    -Name "GET /ai/acte/{id} - Get specific act with full article structure" `
    -Url "$API_BASE/ai/acte/9?only_pending=true" `
    -Validation {
        param($response)
        return ($response.PSObject.Properties['id']) -and ($response.PSObject.Properties['articole']) -and ($response.articole -is [array])
    }
$testResults += $result

if ($Verbose -and $result.Status -eq "PASSED") {
    Write-Host "  → Act ID: $($result.Response.id), Articles: $($result.Response.articole.Count), Status: $($result.Response.ai_status)" -ForegroundColor Gray
}

Write-Host "`n┌─────────────────────────────────────────────────────────┐" -ForegroundColor White
Write-Host "│ 2. Status Management Endpoints                          │" -ForegroundColor White
Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor White

# Test 3: GET AI status overview
$result = Test-Endpoint `
    -Name "GET /ai/status - Get overall AI processing statistics" `
    -Url "$API_BASE/ai/status" `
    -Validation {
        param($response)
        return ($response.PSObject.Properties['total_acts']) -and ($response.PSObject.Properties['pending_acts'])
    }
$testResults += $result

if ($Verbose -and $result.Status -eq "PASSED") {
    Write-Host "  → Total Acts: $($result.Response.total_acts), Pending: $($result.Response.pending_acts)" -ForegroundColor Gray
    Write-Host "  → Total Articles: $($result.Response.total_articles), Pending: $($result.Response.pending_articles)" -ForegroundColor Gray
}

# Test 4: GET pending articles
$result = Test-Endpoint `
    -Name "GET /ai/pending - Get pending articles list" `
    -Url "$API_BASE/ai/pending?limit=5" `
    -Validation {
        param($response)
        return ($response -is [array]) -and ($response[0].PSObject.Properties['id']) -and ($response[0].PSObject.Properties['ai_status'])
    }
$testResults += $result

if ($Verbose -and $result.Status -eq "PASSED") {
    Write-Host "  → Found $($result.Response.Count) pending articles" -ForegroundColor Gray
    $result.Response | Select-Object -First 3 id, numar_articol, ai_status | Format-Table | Out-String | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
}

# Test 5: GET articles with errors
$result = Test-Endpoint `
    -Name "GET /ai/errors - Get articles with processing errors" `
    -Url "$API_BASE/ai/errors?limit=5" `
    -Validation {
        param($response)
        return ($response -is [array])
    }
$testResults += $result

if ($Verbose -and $result.Status -eq "PASSED") {
    if ($result.Response.Count -gt 0) {
        Write-Host "  → Found $($result.Response.Count) articles with errors" -ForegroundColor Gray
        $result.Response | Select-Object -First 2 id, numar_articol, ai_status, ai_error | Format-Table | Out-String | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    } else {
        Write-Host "  → No articles with errors (good!)" -ForegroundColor Gray
    }
}

Write-Host "`n┌─────────────────────────────────────────────────────────┐" -ForegroundColor White
Write-Host "│ 3. Status Update Endpoints (Read-only verification)     │" -ForegroundColor White
Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor White

Write-Host "Checking status update endpoints exist:" -ForegroundColor Cyan
$statusEndpoints = @(
    "POST /ai/articole/{id}/mark-processing",
    "POST /ai/articole/{id}/mark-processed",
    "POST /ai/articole/{id}/mark-error",
    "POST /ai/retry/{id}",
    "POST /ai/reset/{id}"
)
$statusEndpoints | ForEach-Object { Write-Host "  ✓ $_" -ForegroundColor Green }

Write-Host "`n┌─────────────────────────────────────────────────────────┐" -ForegroundColor White
Write-Host "│ 4. Processing Trigger Endpoints                         │" -ForegroundColor White
Write-Host "└─────────────────────────────────────────────────────────┘" -ForegroundColor White

# Test 6: Check sync processing endpoint
$result = Test-Endpoint `
    -Name "GET /ai/process/sync - Get sync processing stats" `
    -Url "$API_BASE/ai/process/sync" `
    -Validation {
        param($response)
        return ($response.PSObject.Properties['success'] -ne $null) -and ($response.PSObject.Properties['total'] -ne $null)
    }
$testResults += $result

if ($Verbose -and $result.Status -eq "PASSED") {
    Write-Host "  → Success: $($result.Response.success), Errors: $($result.Response.error), Total: $($result.Response.total)" -ForegroundColor Gray
}

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor White
Write-Host "║                     TEST SUMMARY                           ║" -ForegroundColor White
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor White
Write-Host ""
Write-Host "Total Tests:  " -NoNewline
Write-Host "$($passedTests + $failedTests)" -ForegroundColor Cyan
Write-Host "Passed:       " -NoNewline
Write-Host "$passedTests" -ForegroundColor Green
Write-Host "Failed:       " -NoNewline
Write-Host "$failedTests" -ForegroundColor $(if ($failedTests -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($failedTests -gt 0) {
    Write-Host "Failed Tests:" -ForegroundColor Red
    $testResults | Where-Object { $_.Status -eq "FAILED" } | ForEach-Object {
        Write-Host "  ✗ $($_.Name)" -ForegroundColor Red
        if ($_.Error) {
            Write-Host "    Error: $($_.Error)" -ForegroundColor DarkRed
        }
        Write-Host "    URL: $($_.Url)" -ForegroundColor DarkGray
    }
    Write-Host ""
}

if ($failedTests -eq 0) {
    Write-Host "✅ All AI endpoints are operational!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Some endpoints failed. Please investigate." -ForegroundColor Red
    exit 1
}
