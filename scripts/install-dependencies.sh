#!/bin/bash
# Script pentru instalarea tuturor dependențelor necesare pentru parser-law v1.0.0
# Rulează cu: bash scripts/install-dependencies.sh

set -e  # Exit on error

echo "🚀 Parser Law - Instalare Dependențe"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    SUDO=""
else
    SUDO="sudo"
fi

echo -e "${YELLOW}Pas 1: Actualizare sistem${NC}"
$SUDO apt update

echo ""
echo -e "${YELLOW}Pas 2: Instalare Python și pip${NC}"
if ! command -v python3 &> /dev/null; then
    echo "Instalez Python3..."
    $SUDO apt install -y python3
else
    echo "✓ Python3 deja instalat: $(python3 --version)"
fi

if ! command -v pip3 &> /dev/null; then
    echo "Instalez pip3..."
    $SUDO apt install -y python3-pip python3-dev build-essential
else
    echo "✓ pip3 deja instalat: $(pip3 --version)"
fi

echo ""
echo -e "${YELLOW}Pas 3: Instalare dependențe Python pentru scraper${NC}"
if [ -f "requirements-scheduler.txt" ]; then
    echo "Instalez dependențe din requirements-scheduler.txt..."
    pip3 install -r requirements-scheduler.txt --break-system-packages 2>&1 | grep -E "Successfully installed|Requirement already satisfied|Installing" || true
    echo "✓ Dependențe instalate"
else
    echo -e "${RED}✗ Fișierul requirements-scheduler.txt nu a fost găsit${NC}"
    echo "  Rulează din directorul /opt/parser-law"
    exit 1
fi

echo ""
echo -e "${YELLOW}Pas 4: Verificare dependențe${NC}"

# Check pandas
if python3 -c "import pandas" 2>/dev/null; then
    PANDAS_VERSION=$(python3 -c "import pandas; print(pandas.__version__)")
    echo "✓ pandas ${PANDAS_VERSION}"
else
    echo -e "${RED}✗ pandas nu este instalat${NC}"
fi

# Check beautifulsoup4
if python3 -c "import bs4" 2>/dev/null; then
    echo "✓ beautifulsoup4"
else
    echo -e "${RED}✗ beautifulsoup4 nu este instalat${NC}"
fi

# Check requests
if python3 -c "import requests" 2>/dev/null; then
    echo "✓ requests"
else
    echo -e "${RED}✗ requests nu este instalat${NC}"
fi

# Check openpyxl
if python3 -c "import openpyxl" 2>/dev/null; then
    echo "✓ openpyxl"
else
    echo -e "${RED}✗ openpyxl nu este instalat${NC}"
fi

# Check lxml
if python3 -c "import lxml" 2>/dev/null; then
    echo "✓ lxml"
else
    echo -e "${RED}✗ lxml nu este instalat${NC}"
fi

echo ""
echo -e "${YELLOW}Pas 5: Verificare structură directoare${NC}"
if [ ! -d "rezultate" ]; then
    echo "Creez directorul rezultate/..."
    mkdir -p rezultate
    echo "✓ Director rezultate/ creat"
else
    echo "✓ Director rezultate/ există"
fi

if [ ! -f "linkuri_legislatie.txt" ]; then
    echo -e "${YELLOW}⚠ Fișierul linkuri_legislatie.txt nu există${NC}"
    echo "  Scraper-ul va căuta acest fișier pentru a ști ce URL-uri să parseze"
else
    LINK_COUNT=$(grep -c "^https://" linkuri_legislatie.txt || echo "0")
    echo "✓ linkuri_legislatie.txt există cu ${LINK_COUNT} linkuri"
fi

echo ""
echo -e "${GREEN}✅ Instalare completă!${NC}"
echo ""
echo "Următorii pași:"
echo "1. Pornește serviciile Docker:"
echo "   cd /opt/parser-law"
echo "   docker compose -f db_service/docker-compose.yml up -d"
echo ""
echo "2. Creează tabelele în database:"
echo "   docker exec -i legislatie_postgres psql -U legislatie_user -d monitoring_platform < db_service/create_tables.sql"
echo ""
echo "3. Testează scraper-ul:"
echo "   python3 scraper_legislatie.py"
echo ""
echo "4. Verifică fișierele generate:"
echo "   ls -lh rezultate/"
