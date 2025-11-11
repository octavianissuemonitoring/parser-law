param(
    [switch]$StartScheduler = $false,
    [int]$TimeoutSeconds = 180
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Ok($msg)   { Write-Host "[ OK ] $msg" -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "[ERR ] $msg" -ForegroundColor Red }

function Test-DockerEngine {
    docker info --format '{{.ServerVersion}}' 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { return $true } else { return $false }
}

function Start-DockerEngine {
    Write-Info "Checking Docker engine..."
    if (Test-DockerEngine) { Write-Ok "Docker engine is already running."; return $true }

    # Try Windows service first
    try {
        $svc = Get-Service -Name 'com.docker.service' -ErrorAction Stop
        if ($svc.Status -ne 'Running') {
            Write-Info "Starting Windows service: com.docker.service"
            Start-Service -Name 'com.docker.service'
        }
    } catch {
        Write-Warn "Docker service not found or cannot start as service. Trying Docker Desktop app..."
        $desktopPaths = @(
            "$Env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
            "$Env:LocalAppData\Docker\Docker Desktop.exe"
        )
        $dockerExe = $desktopPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
        if ($null -ne $dockerExe) {
            Write-Info "Launching Docker Desktop: $dockerExe"
            Start-Process -FilePath $dockerExe | Out-Null
        } else {
            Write-Err "Docker Desktop executable not found. Please install/start Docker Desktop."
            return $false
        }
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-DockerEngine) { Write-Ok "Docker engine is now running."; return $true }
        Start-Sleep -Seconds 5
        Write-Info "Waiting for Docker engine to be ready... (ensure Docker Desktop window is open and status shows 'Running')"
    }

    Write-Err "Docker engine did not become ready within $TimeoutSeconds seconds."
    return $false
}

# Ensure running from repo root
Push-Location $PSScriptRoot/..

Write-Info "Starting local dev stack (postgres + api)."

if (-not (Start-DockerEngine)) {
    Write-Err "Cannot continue without Docker. Steps:\n 1. Open Docker Desktop manually from Start Menu\n 2. Wait until it shows 'Docker engine running'\n 3. Re-run: pwsh -File scripts/dev-start.ps1\n"
    Pop-Location
    exit 1
}

# Bring up Postgres
Write-Info "Bringing up Postgres..."
docker compose -f docker-compose.dev.yml up -d postgres 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Err "Failed to start Postgres (Docker engine likely still not ready). Re-check Docker Desktop."
    Pop-Location; exit 1
}

# Wait for Postgres healthy
$pgContainer = 'parser-law-postgres'
$deadline = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $deadline) {
    try {
        $status = docker inspect --format '{{json .State.Health.Status}}' $pgContainer 2>$null
        if ($status -and $status -match 'healthy') { Write-Ok "Postgres is healthy."; break }
    } catch { }
    Write-Info "Waiting for Postgres health..."
    Start-Sleep -Seconds 5
}

# Bring up API
Write-Info "Bringing up API..."
docker compose -f docker-compose.dev.yml up -d api 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Err "Failed to start API container. Check Postgres health & Docker engine, then re-run."; Pop-Location; exit 1
}

# Wait for API health
$deadline = (Get-Date).AddSeconds(90)
$healthOk = $false
while ((Get-Date) -lt $deadline) {
    try {
        $res = Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 5
        if ($res.StatusCode -eq 200) { $healthOk = $true; break }
    } catch { }
    Write-Info "Waiting for API health on http://localhost:8000/health ..."
    Start-Sleep -Seconds 5
}

if ($healthOk) {
    Write-Ok "API is healthy at http://localhost:8000"
} else {
    Write-Warn "API health endpoint not responding yet. Check logs: docker compose -f docker-compose.dev.yml logs -f api"
}

# Optionally run scheduler once
if ($StartScheduler) {
    Write-Info "Running scheduler once (--now)..."
    try {
        docker compose -f docker-compose.dev.yml exec -T scheduler python -m src.scheduler.scheduler --now
        Write-Ok "Scheduler run completed."
    } catch {
        Write-Warn "Scheduler execution failed: $($_.Exception.Message)"
    }
}

Write-Ok "Local dev stack initialized."
Write-Host "\nEndpoints:" -ForegroundColor Gray
Write-Host "  • API docs:   http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "  • Health:      http://localhost:8000/health" -ForegroundColor Gray

Pop-Location
