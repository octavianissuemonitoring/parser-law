# Deploy Web Interface to VPS
# Usage: .\deploy-web-interface.ps1

param(
    [string]$VpsHost = "77.237.235.158",
    [string]$VpsUser = "root"
)

function Write-Step {
    param([string]$Message)
    Write-Host ">>> $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Magenta
Write-Host "🚀 Web Interface Deployment" -ForegroundColor Magenta
Write-Host "========================================`n" -ForegroundColor Magenta

# 1. Commit changes
Write-Step "Committing changes..."
git add .
$commitMsg = "Add web interface for link management and act visualization"
git commit -m $commitMsg
Write-Success "Changes committed"

# 2. Push to GitHub
Write-Step "Pushing to GitHub..."
git push origin master
Write-Success "Code pushed to GitHub"

# 3. Pull on VPS
Write-Step "Pulling code on VPS..."
ssh "${VpsUser}@${VpsHost}" "cd /opt/parser-law && git pull origin master"
Write-Success "Code pulled on VPS"

# 4. Ensure static directory exists
Write-Step "Creating static directory..."
ssh "${VpsUser}@${VpsHost}" "mkdir -p /opt/parser-law/db_service/app/static"
Write-Success "Static directory ready"

# 5. Restart API container
Write-Step "Restarting API container..."
ssh "${VpsUser}@${VpsHost}" "cd /opt/parser-law/db_service && docker-compose restart legislatie_api"
Write-Success "Container restarted"

# Wait for startup
Write-Step "Waiting for API startup..."
Start-Sleep -Seconds 5

# 6. Verify health
Write-Step "Checking API health..."
$health = ssh "${VpsUser}@${VpsHost}" "curl -s http://localhost:8000/health"
if ($health -match "healthy") {
    Write-Success "API is healthy"
} else {
    Write-Error "Health check failed: $health"
    exit 1
}

# 7. Verify routes
Write-Step "Checking routes..."
$routes = ssh "${VpsUser}@${VpsHost}" "curl -s http://localhost:8000/"
if ($routes -match "links") {
    Write-Success "Links route registered"
} else {
    Write-Error "Links route not found"
}

# 8. Test links endpoint
Write-Step "Testing links endpoint..."
$linksStatus = ssh "${VpsUser}@${VpsHost}" "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/links/stats"
if ($linksStatus -eq "200") {
    Write-Success "Links endpoint responding (HTTP $linksStatus)"
} else {
    Write-Error "Links endpoint returned HTTP $linksStatus"
}

# 9. Summary
Write-Host "`n========================================" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green

Write-Host "📍 Access Points:" -ForegroundColor Yellow
Write-Host "  • Web UI:    https://legislatie.issuemonitoring.ro/" -ForegroundColor White
Write-Host "  • API Docs:  http://${VpsHost}:8000/docs" -ForegroundColor White

Write-Host "`n🔗 API Endpoints:" -ForegroundColor Yellow
Write-Host "  • GET  /api/v1/links/         - List all links" -ForegroundColor White
Write-Host "  • POST /api/v1/links/         - Add new link" -ForegroundColor White
Write-Host "  • GET  /api/v1/links/stats    - Statistics" -ForegroundColor White
Write-Host "  • GET  /api/v1/acte           - List acts" -ForegroundColor White
Write-Host "  • GET  /api/v1/acte/{id}      - Act details" -ForegroundColor White

Write-Host "`n📋 Features:" -ForegroundColor Yellow
Write-Host "  ✓ Link management interface" -ForegroundColor Green
Write-Host "  ✓ Acts list with filters & search" -ForegroundColor Green
Write-Host "  ✓ Structured index view" -ForegroundColor Green
Write-Host "  ✓ Statistics dashboard" -ForegroundColor Green

Write-Host "`n🧪 Test in Browser:" -ForegroundColor Yellow
Write-Host "  Start-Process 'https://legislatie.issuemonitoring.ro/'" -ForegroundColor Cyan

Write-Host "`n========================================`n" -ForegroundColor Green
