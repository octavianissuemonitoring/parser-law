# Deployment pe VPS - Parser Law

## 📋 Prezentare Generală

Ghid complet pentru deployment-ul aplicației Parser Law pe VPS Ubuntu/Debian.

**Arhitectură:**
- **Subdomain:** legislatie.issuemonitoring.ro
- **Services:** PostgreSQL Database, FastAPI Backend, Scheduler
- **Reverse Proxy:** Nginx cu SSL/HTTPS (Let's Encrypt)
- **VPS:** Ubuntu 22.04 LTS

---

## 📋 Cerințe VPS

### Minime
- **RAM:** 2 GB (4 GB recomandat)
- **CPU:** 2 cores
- **Storage:** 20 GB SSD
- **OS:** Ubuntu 22.04 LTS sau Debian 12
- **Network:** Port 8000 (API), 5432 (PostgreSQL - opțional extern)

### Software Necesar
- Docker 24.x
- Docker Compose 2.x
- Git
- Nginx (pentru reverse proxy)
- Certbot (pentru SSL/HTTPS)

---

## 🔧 Pas 1: Pregătire VPS

### 1.1. Conectare SSH
```bash
ssh root@your-vps-ip
# sau
ssh username@your-vps-ip
```

### 1.2. Update sistem
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.3. Instalare Docker
```bash
# Instalare Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Adăugare user la docker group
sudo usermod -aG docker $USER

# Restart pentru aplicare permisiuni
exit
# Reconectează SSH
```

### 1.4. Instalare Docker Compose
```bash
sudo apt install docker-compose-plugin -y
# sau
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 1.5. Verificare instalare
```bash
docker --version
docker compose version
```

---

## 📦 Pas 2: Deployment Aplicație

### 2.1. Clone repository
```bash
cd /opt
sudo git clone https://github.com/octavianissuemonitoring/parser-law.git
cd parser-law
sudo chown -R $USER:$USER /opt/parser-law
```

### 2.2. Configurare environment
```bash
# Database Service
cd db_service
cp .env.example .env
nano .env
```

Configurează `.env`:
```env
DATABASE_URL=postgresql://legislatie_user:STRONG_PASSWORD_HERE@postgres:5432/monitoring_platform
DB_PASSWORD=STRONG_PASSWORD_HERE
DB_SCHEMA=legislatie
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### 2.3. Configurare Scheduler
```bash
cd ..
cp .env.scheduler.example .env.scheduler
nano .env.scheduler
```

Configurează `.env.scheduler`:
```env
SCRAPER_SCHEDULE=0 2 * * *
CLEANUP_SCHEDULE=0 3 * * 0
QUALITY_CHECK=true
LOG_LEVEL=INFO
```

---

## 🐳 Pas 3: Start Servicii Docker

### 3.1. Configurare Build Context

**IMPORTANT:** Dockerfile-ul necesită fișiere din directorul principal, trebuie să actualizăm build context-ul.

```bash
cd /opt/parser-law/db_service

# Actualizează docker-compose.yml pentru build context corect
sed -i 's|context: \.|context: ..|g' docker-compose.yml
sed -i 's|dockerfile: Dockerfile|dockerfile: db_service/Dockerfile|g' docker-compose.yml

# Actualizează Dockerfile pentru path-uri corecte
sed -i 's|COPY requirements.txt \.|COPY db_service/requirements.txt .|g' Dockerfile
sed -i 's|COPY \./app /app/app|COPY db_service/app /app/app|g' Dockerfile
sed -i 's|COPY \./alembic /app/alembic|COPY db_service/alembic /app/alembic|g' Dockerfile
sed -i 's|COPY alembic.ini /app/|COPY db_service/alembic.ini /app/|g' Dockerfile
```

### 3.2. Configurare Environment

```bash
# Verifică și configurează .env
cd /opt/parser-law/db_service
ls -la .env

# Dacă nu există, creează-l
cp .env.example .env

# Editează parolele (OBLIGATORIU pentru producție!)
nano .env

# Actualizează DATABASE_URL cu parola corectă
sed -i 's/CHANGE_THIS_PASSWORD/your_password_here/g' .env
```

### 3.3. Start Database + API

```bash
# Pornește serviciile din directorul principal (build context corect)
cd /opt/parser-law
docker compose -f db_service/docker-compose.yml up -d --build
```

### 3.4. Verificare servicii

```bash
# Verifică status servicii
cd /opt/parser-law
docker compose -f db_service/docker-compose.yml ps

# Trebuie să vezi ambele servicii ca healthy:
# ✅ legislatie_postgres    Up X seconds (healthy)
# ✅ legislatie_api         Up X seconds (healthy)

# Vezi logs pentru debugging
docker compose -f db_service/docker-compose.yml logs -f api
docker compose -f db_service/docker-compose.yml logs -f postgres
```

### 3.5. Creare tabele database

```bash
# Așteaptă ca PostgreSQL să fie complet pornit
sleep 10

# Creează tabelele din SQL
cd /opt/parser-law/db_service
docker exec -i legislatie_postgres psql -U legislatie_user -d monitoring_platform < create_tables.sql

# Adaugă coloanele lipsă pentru AI și export features
cat > /tmp/add_columns.sql << 'EOF'
ALTER TABLE legislatie.acte_legislative 
ADD COLUMN IF NOT EXISTS ai_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS ai_processed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS ai_error TEXT,
ADD COLUMN IF NOT EXISTS metadate JSONB,
ADD COLUMN IF NOT EXISTS export_status VARCHAR(20),
ADD COLUMN IF NOT EXISTS export_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS export_error TEXT,
ADD COLUMN IF NOT EXISTS issue_monitoring_id INTEGER;
EOF

docker exec -i legislatie_postgres psql -U legislatie_user -d monitoring_platform < /tmp/add_columns.sql

# Verificare tabele create (trebuie să vezi 7 tabele: acte_legislative, acte_modificari, articole, articole_modificari, linkuri_legislatie, issues, anexe)
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\dt legislatie.*"
```

### 3.6. Start Scheduler (opțional)

```bash
# Înapoi în directorul principal
cd /opt/parser-law

# Pornește scheduler-ul
docker compose -f docker-compose.scheduler.yml up -d

# Verificare
docker compose -f docker-compose.scheduler.yml ps

# Vezi logs
docker compose -f docker-compose.scheduler.yml logs -f
```

---

## 🌐 Pas 4: Configurare Nginx (Reverse Proxy)

### 4.1. Instalare Nginx
```bash
sudo apt install nginx -y
```

### 4.2. Configurare site pentru subdomain

```bash
# Copiază configurația exemplu și adaptează pentru domeniul tău
cd /opt/parser-law
sudo cp nginx.conf.example /etc/nginx/sites-available/parser-law

# Actualizează domain name
sudo sed -i 's/your-domain.com www.your-domain.com/legislatie.issuemonitoring.ro/g' /etc/nginx/sites-available/parser-law
```

**Sau creează manual** `/etc/nginx/sites-available/parser-law`:
```nginx
server {
    listen 80;
    server_name legislatie.issuemonitoring.ro;

    # Dimensiune maximă pentru file uploads
    client_max_body_size 10M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/parser-law-access.log;
    error_log /var/log/nginx/parser-law-error.log;

    # API Backend
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts pentru long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Swagger UI Documentation
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # OpenAPI JSON
    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_set_header Host $host;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

### 4.3. Activare site și dezactivare default

```bash
# Dezactivează site-ul default care ar putea intercepta traficul
sudo rm -f /etc/nginx/sites-enabled/default

# Activează configurația parser-law
sudo ln -s /etc/nginx/sites-available/parser-law /etc/nginx/sites-enabled/

# Verifică configurația
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## 🔒 Pas 5: Configurare SSL/HTTPS (Certbot)

### 5.1. Instalare Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 5.2. Obținere certificat SSL pentru subdomain

**Important:** Asigură-te că DNS-ul este configurat corect înainte!

```bash
# Verifică DNS
nslookup legislatie.issuemonitoring.ro
# Trebuie să returneze IP-ul VPS-ului (109.123.249.228)

# Obține certificat SSL automat (non-interactive)
sudo certbot --nginx -d legislatie.issuemonitoring.ro \
  --non-interactive \
  --agree-tos \
  --email your-email@domain.com \
  --redirect

# SAU interactiv (recomandat pentru prima instalare):
sudo certbot --nginx -d legislatie.issuemonitoring.ro

# Urmează instrucțiunile:
# - Introdu email pentru notificări
# - Acceptă Terms of Service
# - Alege dacă vrei redirect HTTP -> HTTPS (recomandat: Yes)
```

### 5.3. Auto-renewal
```bash
sudo systemctl status certbot.timer
# Certbot configurează automat renewal
```

---

## 🔥 Pas 6: Configurare Firewall

### 6.1. Setup UFW (Ubuntu Firewall)
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### 6.2. Reguli firewall
```bash
# Permite doar ce e necesar
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# NU expune direct porturile Docker
# sudo ufw deny 8000/tcp  # API (doar prin Nginx)
# sudo ufw deny 5432/tcp  # PostgreSQL (doar intern)
```

---

## 📊 Pas 7: Monitoring & Logs

### 7.1. Verificare status servicii
```bash
# Docker services
docker compose ps
docker compose logs -f api
docker compose logs -f postgres

# Nginx
sudo systemctl status nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 7.2. Monitoring disk space
```bash
df -h
docker system df
```

### 7.3. Cleanup periodic
```bash
# Cleanup Docker
docker system prune -a --volumes -f

# Logs rotation
sudo nano /etc/logrotate.d/docker-containers
```

---

## 🔄 Pas 8: Update & Maintenance

### 8.1. Update aplicație
```bash
cd /opt/parser-law
git pull origin master
cd db_service
docker compose down
docker compose up -d --build
```

### 8.2. Backup database
```bash
# Backup
docker exec legislatie_postgres pg_dump -U legislatie_user monitoring_platform > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i legislatie_postgres psql -U legislatie_user -d monitoring_platform < backup_20251108.sql
```

### 8.3. Restart servicii
```bash
# Restart API
cd /opt/parser-law/db_service
docker compose restart api

# Restart Scheduler
cd /opt/parser-law
docker compose -f docker-compose.scheduler.yml restart
```

---

## 📋 Pas 9: Verificare Deployment

### 9.1. Test API
```bash
# Health check
curl https://legislatie.issuemonitoring.ro/health

# API documentation
curl https://legislatie.issuemonitoring.ro/docs

# Test import (după rulare scraper)
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/acte/import?rezultate_dir=/data/rezultate"

# List acte
curl https://legislatie.issuemonitoring.ro/api/v1/acte
```

### 9.2. Verificare în browser
- **API Health:** https://legislatie.issuemonitoring.ro/health
- **Swagger Docs:** https://legislatie.issuemonitoring.ro/docs
- **API Endpoints:** https://legislatie.issuemonitoring.ro/api/v1/acte

### 9.2. Test Scheduler
```bash
# Vezi logs
docker compose -f docker-compose.scheduler.yml logs -f

# Verifică cron jobs
docker exec parser-law-scheduler crontab -l
```

---

## 🎯 Pas 10: Rulare Inițială

### 10.1. Import date inițial
```bash
# Rulează scraper manual prima dată
docker compose -f docker-compose.scheduler.yml exec scheduler python scraper_legislatie.py

# Verifică rezultate
docker compose -f docker-compose.scheduler.yml exec scheduler ls -lh rezultate/

# Import în database
curl -X POST "http://localhost:8000/api/v1/acte/import?rezultate_dir=/data/rezultate"
```

### 10.2. Verificare date în DB
```bash
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "SELECT COUNT(*) FROM legislatie.acte_legislative;"
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "SELECT COUNT(*) FROM legislatie.articole;"
```

---

## 🔧 Troubleshooting

### Problema: API nu răspunde
```bash
# Verifică logs
docker compose logs api

# Verifică port
sudo netstat -tulpn | grep 8000

# Restart
docker compose restart api
```

### Problema: Database connection error
```bash
# Verifică PostgreSQL
docker compose ps postgres
docker compose logs postgres

# Test connection
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "SELECT 1;"
```

### Problema: Nginx 502 Bad Gateway
```bash
# Verifică backend
curl http://localhost:8000

# Verifică Nginx config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Problema: Disk full
```bash
# Check space
df -h

# Cleanup Docker
docker system prune -a --volumes -f

# Cleanup logs
sudo journalctl --vacuum-time=7d
```

---

## 🎉 Deployment Complet!

**Access Points:**
- **API:** https://legislatie.issuemonitoring.ro
- **Swagger UI:** https://legislatie.issuemonitoring.ro/docs
- **Health Check:** https://legislatie.issuemonitoring.ro/health

**Servicii Active:**
- ✅ PostgreSQL Database (legislatie_postgres)
- ✅ FastAPI Backend (legislatie_api)
- ✅ Nginx Reverse Proxy cu SSL
- ✅ Scheduler (scraping automat)
- ✅ Auto-renewal SSL (Certbot)

**Monitoring:**
```bash
# Status servicii Docker
cd /opt/parser-law/db_service
docker compose ps

# Status Nginx
sudo systemctl status nginx

# Logs aplicație
docker compose logs -f api

# Logs Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

---

## 📚 Resurse Utile

- **API Documentation:** https://legislatie.issuemonitoring.ro/docs
- **GitHub Repository:** https://github.com/octavianissuemonitoring/parser-law
- **Issue Tracker:** https://github.com/octavianissuemonitoring/parser-law/issues

---

## ⚠️ Common Issues & Solutions

### Issue: Docker build fails with "file not found"
**Cauză:** Build context incorect - Dockerfile-ul caută fișiere în directorul greșit.
**Soluție:** Asigură-te că rulezi `docker compose` din directorul principal cu flag `-f db_service/docker-compose.yml` și că build context este setat la `..` (parent directory).

### Issue: API returns 500 error on /api/v1/acte
**Cauză:** Coloanele AI și export lipsesc din tabelul `acte_legislative`.
**Soluție:** Rulează script-ul SQL pentru adăugare coloane (Pasul 3.5).

### Issue: Site nu este accesibil prin domeniu
**Cauză:** Site-ul default Nginx interceptează traficul.
**Soluție:** `sudo rm /etc/nginx/sites-enabled/default && sudo systemctl reload nginx`

### Issue: "Connection refused" la accesare site
**Cauză:** API-ul nu rulează sau Nginx nu este configurat corect.
**Verificare:**
```bash
# Test local API
curl http://localhost:8000/health

# Verifică Docker
docker compose -f db_service/docker-compose.yml ps

# Verifică Nginx
sudo systemctl status nginx
sudo nginx -t
```

---

## 📚 Resurse Utile

- **API Documentation:** https://legislatie.issuemonitoring.ro/docs
- **GitHub Repository:** https://github.com/octavianissuemonitoring/parser-law
- **Issue Tracker:** https://github.com/octavianissuemonitoring/parser-law/issues

---

**Domain:** legislatie.issuemonitoring.ro  
**Deployment date:** 14 noiembrie 2025  
**Version:** 2.0.0  
**VPS IP:** 109.123.249.228
