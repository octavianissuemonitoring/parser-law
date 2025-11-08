#!/bin/bash

# Quick Setup Script pentru VPS
# Usage: curl -fsSL https://raw.githubusercontent.com/octavianissuemonitoring/parser-law/master/scripts/setup-vps.sh | bash

set -e

echo "🚀 Parser Law - VPS Setup Script"
echo "=================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "📦 Updating system..."
apt update && apt upgrade -y

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    apt install docker-compose-plugin -y
    echo "✅ Docker Compose installed"
else
    echo "✅ Docker Compose already installed"
fi

# Install Nginx
echo "🌐 Installing Nginx..."
if ! command -v nginx &> /dev/null; then
    apt install nginx -y
    systemctl enable nginx
    echo "✅ Nginx installed"
else
    echo "✅ Nginx already installed"
fi

# Install Certbot
echo "🔒 Installing Certbot..."
if ! command -v certbot &> /dev/null; then
    apt install certbot python3-certbot-nginx -y
    echo "✅ Certbot installed"
else
    echo "✅ Certbot already installed"
fi

# Setup firewall
echo "🔥 Configuring firewall..."
ufw --force enable
ufw allow OpenSSH
ufw allow 'Nginx Full'
echo "✅ Firewall configured"

# Clone repository
echo "📥 Cloning repository..."
cd /opt
if [ -d "parser-law" ]; then
    echo "⚠️  Repository already exists, updating..."
    cd parser-law
    git pull
else
    git clone https://github.com/octavianissuemonitoring/parser-law.git
    cd parser-law
fi

# Set permissions
echo "🔑 Setting permissions..."
CURRENT_USER=${SUDO_USER:-$USER}
chown -R $CURRENT_USER:$CURRENT_USER /opt/parser-law

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Configure environment:"
echo "   cd /opt/parser-law/db_service"
echo "   cp .env.example .env"
echo "   nano .env  # Edit database password"
echo ""
echo "2. Start services:"
echo "   docker compose up -d"
echo ""
echo "3. Setup Nginx (see DEPLOYMENT_VPS.md)"
echo ""
echo "4. Get SSL certificate:"
echo "   sudo certbot --nginx -d your-domain.com"
echo ""
echo "📖 Full guide: /opt/parser-law/DEPLOYMENT_VPS.md"
