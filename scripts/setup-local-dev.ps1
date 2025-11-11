# ============================================================================
# Quick Start Script for Local Development
# ============================================================================
# 
# This script sets up the complete local development environment in 5 minutes.
# 
# Usage: .\scripts\setup-local-dev.ps1
# 
# ============================================================================

Write-Host "🚀 Parser Law - Local Development Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check Prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Host "✅ Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    Write-Host "   Download: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check Docker Compose
try {
    $composeVersion = docker-compose --version
    Write-Host "✅ Docker Compose: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.11+." -ForegroundColor Red
    Write-Host "   Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "📦 Step 1: Environment Configuration" -ForegroundColor Yellow
Write-Host "======================================" -ForegroundColor Yellow

# Create .env if doesn't exist
if (!(Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Cyan
    Copy-Item ".env.example" ".env"
    
    Write-Host "✅ .env file created" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Edit .env file and set your passwords!" -ForegroundColor Yellow
    Write-Host "   Open: .env" -ForegroundColor Yellow
    Write-Host "   Set: POSTGRES_PASSWORD=<your_password>" -ForegroundColor Yellow
    Write-Host ""
    
    $continue = Read-Host "Press Enter when you've edited .env, or 's' to skip"
    if ($continue -eq "s") {
        Write-Host "⚠️  Using default passwords (NOT recommended for production)" -ForegroundColor Yellow
    }
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "🐍 Step 2: Python Virtual Environment" -ForegroundColor Yellow
Write-Host "=======================================" -ForegroundColor Yellow

# Create virtual environment if doesn't exist
if (!(Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Install development tools
Write-Host "Installing development tools..." -ForegroundColor Cyan
pip install black isort flake8 pytest pytest-cov pre-commit --quiet
Write-Host "✅ Development tools installed" -ForegroundColor Green

Write-Host ""
Write-Host "🪝 Step 3: Git Hooks" -ForegroundColor Yellow
Write-Host "=====================" -ForegroundColor Yellow

# Install pre-commit hooks
Write-Host "Installing pre-commit hooks..." -ForegroundColor Cyan
pre-commit install
Write-Host "✅ Pre-commit hooks installed" -ForegroundColor Green

Write-Host ""
Write-Host "🐳 Step 4: Docker Containers" -ForegroundColor Yellow
Write-Host "=============================" -ForegroundColor Yellow

# Start Docker Compose
Write-Host "Starting Docker containers..." -ForegroundColor Cyan
Write-Host "(This may take 2-3 minutes on first run)" -ForegroundColor Gray
docker-compose -f docker-compose.dev.yml up -d

Write-Host ""
Write-Host "Waiting for services to be healthy..." -ForegroundColor Cyan
Start-Sleep -Seconds 30

# Check container status
Write-Host ""
Write-Host "Container Status:" -ForegroundColor Cyan
docker-compose -f docker-compose.dev.yml ps

Write-Host ""
Write-Host "✅ Step 5: Verification" -ForegroundColor Yellow
Write-Host "=======================" -ForegroundColor Yellow

# Test API health
Write-Host "Testing API health..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    if ($response.status -eq "healthy") {
        Write-Host "✅ API is healthy!" -ForegroundColor Green
        Write-Host "   Version: $($response.version)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  API responded but status is: $($response.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ API health check failed. Check logs:" -ForegroundColor Red
    Write-Host "   docker-compose -f docker-compose.dev.yml logs api" -ForegroundColor Yellow
}

# Test database
Write-Host ""
Write-Host "Testing database connection..." -ForegroundColor Cyan
try {
    $dbTest = docker exec parser-law-postgres psql -U parser_user -d monitoring_platform -c "SELECT 1;" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database is connected!" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Database connection issue. Check logs:" -ForegroundColor Yellow
        Write-Host "   docker logs parser-law-postgres" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Database test failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Your local environment is ready:" -ForegroundColor Cyan
Write-Host "   API:         http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "   Health:      http://localhost:8000/health" -ForegroundColor White
Write-Host "   Database:    localhost:5432" -ForegroundColor White
Write-Host ""
Write-Host "📚 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Open browser: http://localhost:8000/docs" -ForegroundColor White
Write-Host "   2. Create feature branch: git checkout -b feature/my-feature" -ForegroundColor White
Write-Host "   3. Edit code in db_service/app/" -ForegroundColor White
Write-Host "   4. Changes reload automatically (hot reload)" -ForegroundColor White
Write-Host "   5. View logs: docker-compose -f docker-compose.dev.yml logs -f api" -ForegroundColor White
Write-Host ""
Write-Host "📖 Documentation:" -ForegroundColor Yellow
Write-Host "   - LOCAL_DEVELOPMENT.md (local dev guide)" -ForegroundColor White
Write-Host "   - GIT_WORKFLOW.md (branching strategy)" -ForegroundColor White
Write-Host "   - DEVELOPMENT_GUIDE.md (coding standards)" -ForegroundColor White
Write-Host ""
Write-Host "🛠️  Common Commands:" -ForegroundColor Yellow
Write-Host "   Stop:    docker-compose -f docker-compose.dev.yml down" -ForegroundColor White
Write-Host "   Logs:    docker-compose -f docker-compose.dev.yml logs -f" -ForegroundColor White
Write-Host "   Restart: docker-compose -f docker-compose.dev.yml restart api" -ForegroundColor White
Write-Host ""
Write-Host "Happy coding! 🚀" -ForegroundColor Cyan
