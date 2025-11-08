#!/bin/bash
# Script automat pentru deployment parser-law pe VPS
# Rulează: bash deploy-vps.sh

set -e  # Oprește scriptul la prima eroare

echo "======================================"
echo "🚀 Parser-Law VPS Deployment Script"
echo "======================================"
echo ""

# Culorare output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# PAS 1: Verifică directorul curent
echo -e "${YELLOW}[1/6] Verificare director curent...${NC}"
cd /opt
pwd
echo ""

# PAS 2: Șterge directorul vechi (dacă există)
if [ -d "parser-law" ]; then
    echo -e "${YELLOW}[2/6] Ștergere director vechi parser-law...${NC}"
    sudo rm -rf parser-law
    echo -e "${GREEN}✓ Director șters cu succes${NC}"
else
    echo -e "${YELLOW}[2/6] Nu există director vechi parser-law${NC}"
fi
echo ""

# PAS 3: Clonează repository
echo -e "${YELLOW}[3/6] Clonare repository din GitHub...${NC}"
git clone https://github.com/octavianissuemonitoring/parser-law.git
echo -e "${GREEN}✓ Repository clonat cu succes${NC}"
echo ""

# PAS 4: Verifică structura
echo -e "${YELLOW}[4/6] Verificare structură repository...${NC}"
cd parser-law
echo "Conținut director parser-law:"
ls -la
echo ""

# Verifică dacă există db_service/
if [ -d "db_service" ]; then
    echo -e "${GREEN}✓ Director db_service/ găsit${NC}"
else
    echo -e "${RED}✗ EROARE: Director db_service/ NU există!${NC}"
    exit 1
fi

# Verifică fișiere cheie
if [ -f "scraper_legislatie.py" ]; then
    echo -e "${GREEN}✓ Fișier scraper_legislatie.py găsit${NC}"
else
    echo -e "${RED}✗ AVERTISMENT: scraper_legislatie.py lipsește${NC}"
fi

if [ -f "db_service/docker-compose.yml" ]; then
    echo -e "${GREEN}✓ Fișier docker-compose.yml găsit${NC}"
else
    echo -e "${RED}✗ EROARE: docker-compose.yml NU există!${NC}"
    exit 1
fi
echo ""

# PAS 5: Setează ownership
echo -e "${YELLOW}[5/6] Setare permisiuni...${NC}"
sudo chown -R $USER:$USER /opt/parser-law
echo -e "${GREEN}✓ Permisiuni setate pentru user: $USER${NC}"
echo ""

# PAS 6: Creează .env dacă nu există
echo -e "${YELLOW}[6/6] Verificare fișier .env...${NC}"
cd db_service

if [ -f ".env" ]; then
    echo -e "${GREEN}✓ Fișier .env deja există${NC}"
else
    if [ -f ".env.production" ]; then
        echo "Creare .env din .env.production..."
        cp .env.production .env
        echo -e "${GREEN}✓ Fișier .env creat din .env.production${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANT: Editează .env și schimbă parolele!${NC}"
    else
        echo -e "${YELLOW}⚠️  .env.production nu există, trebuie să creezi manual .env${NC}"
    fi
fi
echo ""

# Sumar final
echo "======================================"
echo -e "${GREEN}✅ DEPLOYMENT COMPLET!${NC}"
echo "======================================"
echo ""
echo "📂 Locație: /opt/parser-law"
echo "👤 Owner: $USER"
echo ""
echo "📋 Pași următori:"
echo "1. Editează fișierul .env din db_service/:"
echo "   cd /opt/parser-law/db_service"
echo "   nano .env"
echo ""
echo "2. Schimbă parolele (OBLIGATORIU!):"
echo "   - DB_PASSWORD"
echo "   - DATABASE_URL"
echo ""
echo "3. Pornește serviciile Docker:"
echo "   docker compose up -d"
echo ""
echo "4. Verifică status:"
echo "   docker compose ps"
echo "   docker compose logs -f"
echo ""
