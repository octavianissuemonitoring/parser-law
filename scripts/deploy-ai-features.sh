#!/bin/bash
#
# Deploy AI Processing & Export features to production VPS
#
# Usage: ./deploy-ai-features.sh
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common-config.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

log_step() {
    echo -e "${GREEN}▶ $1${NC}"
}

log_warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Check if on VPS
check_vps() {
    if [[ ! -f "/opt/parser-law/.git/config" ]]; then
        log_error "Not on VPS or repository not found at /opt/parser-law"
        exit 1
    fi
}

# Main deployment
main() {
    log_header "Deploy AI Processing & Export Features"
    
    echo "Target: legislatie.issuemonitoring.ro"
    echo "Deploy Dir: ${DEPLOY_DIR}"
    echo "Database: ${DB_NAME}"
    echo ""
    
    # Confirm
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warn "Deployment cancelled"
        exit 0
    fi
    
    # Step 1: Pull latest code
    log_header "Step 1: Pull Latest Code"
    cd "${DEPLOY_DIR}"
    log_step "Fetching from GitHub..."
    git fetch origin
    log_step "Pulling master branch..."
    git pull origin master
    log_success "Code updated"
    
    # Step 2: Install new dependencies
    log_header "Step 2: Install Dependencies"
    cd "${DEPLOY_DIR}/db_service"
    log_step "Installing Python packages..."
    pip install -q -r requirements.txt
    log_success "Dependencies installed"
    
    # Step 3: Verify imports
    log_header "Step 3: Verify Code"
    log_step "Testing imports..."
    python3 -c "from app.services.ai_service import AIService; print('✓ AIService')"
    python3 -c "from app.services.export_service import ExportService; print('✓ ExportService')"
    python3 -c "from app.api.routes.ai_processing import router; print('✓ AI Routes')"
    python3 -c "from app.api.routes.export import router; print('✓ Export Routes')"
    log_success "All imports successful"
    
    # Step 4: Update environment variables
    log_header "Step 4: Configure Environment"
    
    if [[ ! -f "${DEPLOY_DIR}/db_service/.env" ]]; then
        log_warn ".env file not found, copying from .env.example"
        cp "${DEPLOY_DIR}/db_service/.env.example" "${DEPLOY_DIR}/db_service/.env"
        log_error "IMPORTANT: Edit ${DEPLOY_DIR}/db_service/.env with your API keys:"
        echo "  - OPENAI_API_KEY"
        echo "  - ANTHROPIC_API_KEY"
        echo "  - ISSUE_MONITORING_API_KEY"
        echo "  - API_KEY (for endpoint authentication)"
        echo ""
        read -p "Press Enter after editing .env file..."
    fi
    
    # Check if API keys are configured
    if grep -q "sk-proj-xxxxx" "${DEPLOY_DIR}/db_service/.env" 2>/dev/null; then
        log_warn "OpenAI API key not configured (still has placeholder)"
    fi
    
    if grep -q "API_KEY=" "${DEPLOY_DIR}/db_service/.env" 2>/dev/null; then
        log_success "API key configured"
    else
        log_warn "API_KEY not found in .env - add it for endpoint authentication"
    fi
    
    # Step 5: Restart services
    log_header "Step 5: Restart Services"
    
    log_step "Restarting legislatie_api container..."
    docker restart legislatie_api
    
    log_step "Waiting for API to start..."
    sleep 5
    
    # Check if container is running
    if docker ps | grep -q legislatie_api; then
        log_success "legislatie_api container is running"
    else
        log_error "legislatie_api container failed to start"
        log_warn "Check logs: docker logs legislatie_api"
        exit 1
    fi
    
    # Step 6: Verify API endpoints
    log_header "Step 6: Verify API Endpoints"
    
    log_step "Testing health endpoint..."
    if curl -s -f http://localhost:8000/health > /dev/null; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
    
    log_step "Checking API routes..."
    response=$(curl -s http://localhost:8000/)
    if echo "$response" | grep -q "ai_processing"; then
        log_success "AI processing routes registered"
    else
        log_warn "AI processing routes may not be registered"
    fi
    
    if echo "$response" | grep -q "export"; then
        log_success "Export routes registered"
    else
        log_warn "Export routes may not be registered"
    fi
    
    # Step 7: Update scheduler (if running)
    log_header "Step 7: Update Scheduler"
    
    if docker ps | grep -q legislatie_scheduler; then
        log_step "Restarting scheduler container..."
        docker restart legislatie_scheduler
        log_success "Scheduler restarted"
    else
        log_warn "Scheduler container not running"
        log_info "To enable AI/Export automation:"
        echo "  1. Configure environment variables in scheduler"
        echo "  2. Start scheduler: docker-compose -f docker-compose.scheduler.yml up -d"
    fi
    
    # Step 8: Show status
    log_header "Deployment Complete!"
    
    echo ""
    echo "📊 Service Status:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep legislatie || true
    
    echo ""
    echo "📝 Next Steps:"
    echo ""
    echo "1. Configure API keys in ${DEPLOY_DIR}/db_service/.env:"
    echo "   - OPENAI_API_KEY=sk-proj-xxxxx"
    echo "   - ANTHROPIC_API_KEY=sk-ant-xxxxx"
    echo "   - ISSUE_MONITORING_API_KEY=your_key"
    echo "   - API_KEY=<generate with: openssl rand -hex 32>"
    echo ""
    echo "2. Restart API after config:"
    echo "   docker restart legislatie_api"
    echo ""
    echo "3. Test AI processing:"
    echo "   curl -H 'X-API-Key: YOUR_KEY' http://localhost:8000/api/v1/ai/status"
    echo ""
    echo "4. Test export status:"
    echo "   curl -H 'X-API-Key: YOUR_KEY' http://localhost:8000/api/v1/export/status"
    echo ""
    echo "5. View logs:"
    echo "   docker logs -f legislatie_api"
    echo ""
    echo "6. Enable scheduler automation (optional):"
    echo "   docker-compose -f docker-compose.scheduler.yml up -d"
    echo ""
    
    log_success "Deployment finished successfully! 🚀"
}

# Run main
main "$@"
