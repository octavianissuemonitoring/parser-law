#!/bin/bash
# Deploy Web Interface for Links Management
# Usage: ./deploy-web-interface.sh

set -e

# Source common config
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common-config.sh"

log_info "🚀 Starting Web Interface Deployment..."

# Check VPS connection
log_info "Checking VPS connection..."
if ! ssh "$VPS_USER@$VPS_HOST" "echo 'Connected'"; then
    log_error "Cannot connect to VPS. Check SSH connection."
    exit 1
fi
log_success "✓ VPS connection OK"

# Pull latest code
log_info "Pulling latest code from repository..."
ssh "$VPS_USER@$VPS_HOST" "cd $DEPLOY_DIR && git pull origin master"
log_success "✓ Code updated"

# Create static directory if not exists
log_info "Ensuring static directory exists..."
ssh "$VPS_USER@$VPS_HOST" "mkdir -p $DEPLOY_DIR/db_service/app/static"
log_success "✓ Static directory ready"

# Restart containers to pick up new routes
log_info "Restarting containers..."
ssh "$VPS_USER@$VPS_HOST" "cd $DEPLOY_DIR/db_service && docker-compose restart legislatie_api"
log_success "✓ Containers restarted"

# Wait for API to be ready
log_info "Waiting for API to be ready..."
sleep 5

# Verify health
log_info "Verifying API health..."
HEALTH=$(ssh "$VPS_USER@$VPS_HOST" "curl -s http://localhost:8000/health")
if echo "$HEALTH" | grep -q "healthy"; then
    log_success "✓ API is healthy"
else
    log_error "API health check failed: $HEALTH"
    exit 1
fi

# Verify routes
log_info "Verifying routes..."
ROUTES=$(ssh "$VPS_USER@$VPS_HOST" "curl -s http://localhost:8000/")
if echo "$ROUTES" | grep -q "links"; then
    log_success "✓ Links route registered"
else
    log_error "Links route not found in routes: $ROUTES"
    exit 1
fi

# Test links endpoint
log_info "Testing links endpoint..."
LINKS_TEST=$(ssh "$VPS_USER@$VPS_HOST" "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/v1/links/stats")
if [ "$LINKS_TEST" = "200" ]; then
    log_success "✓ Links endpoint responding"
else
    log_error "Links endpoint returned: $LINKS_TEST"
fi

# Check nginx configuration
log_info "Checking nginx configuration..."
NGINX_STATUS=$(ssh "$VPS_USER@$VPS_HOST" "systemctl is-active nginx" || echo "inactive")
if [ "$NGINX_STATUS" = "active" ]; then
    log_success "✓ Nginx is running"
    log_info "Web interface available at: https://legislatie.issuemonitoring.ro/"
else
    log_info "⚠ Nginx not active - interface available at: http://$VPS_HOST:8000/"
fi

# Show deployment summary
log_info ""
log_info "═══════════════════════════════════════════════════════════"
log_info "✅ WEB INTERFACE DEPLOYMENT COMPLETE"
log_info "═══════════════════════════════════════════════════════════"
log_info ""
log_info "📍 Access Points:"
if [ "$NGINX_STATUS" = "active" ]; then
    log_info "  • Web UI: https://legislatie.issuemonitoring.ro/"
else
    log_info "  • Web UI: http://$VPS_HOST:8000/"
fi
log_info "  • API Docs: http://$VPS_HOST:8000/docs"
log_info ""
log_info "🔗 Available Endpoints:"
log_info "  • GET  /api/v1/links/           - List all links"
log_info "  • POST /api/v1/links/           - Add new link"
log_info "  • GET  /api/v1/links/stats      - Statistics"
log_info "  • GET  /api/v1/acte             - List acts"
log_info "  • GET  /api/v1/acte/{id}        - Act details"
log_info ""
log_info "📋 Features:"
log_info "  • 🔗 Link management with form submission"
log_info "  • 📋 Acts list with search and filters"
log_info "  • 📑 Structured index (chapters & articles)"
log_info "  • 📊 Statistics dashboard"
log_info ""
log_info "🧪 Test Commands:"
log_info "  # View in browser:"
if [ "$NGINX_STATUS" = "active" ]; then
    log_info "  open https://legislatie.issuemonitoring.ro/"
else
    log_info "  open http://$VPS_HOST:8000/"
fi
log_info ""
log_info "  # Test API:"
log_info "  curl http://$VPS_HOST:8000/api/v1/links/stats"
log_info ""
log_info "═══════════════════════════════════════════════════════════"
