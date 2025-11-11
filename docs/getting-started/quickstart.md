# 🚀 Quick Start - Deployment pe VPS

## Deployment Rapid

```bash
# 1. Conectează-te la VPS
ssh root@your-vps-ip

# 2. Rulează script-ul de setup automat
curl -fsSL https://raw.githubusercontent.com/octavianissuemonitoring/parser-law/master/scripts/setup-vps.sh | bash

# 3. Configurează environment (în directorul db_service!)
cd /opt/parser-law/db_service
cp .env.example .env
nano .env  # Editează DB_PASSWORD și alte valori sensibile

# 4. Start servicii
docker compose up -d

# 5. Verificare
docker compose ps

# 6. Creare tabele database
docker exec -i legislatie_postgres psql -U legislatie_user -d monitoring_platform < create_tables.sql

# 7. Verificare tabele
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "\dt legislatie.*"
```

## 🔧 Configurare Nginx cu Subdomain

```bash
# Copiază și editează configurația
sudo cp nginx.conf.example /etc/nginx/sites-available/parser-law
sudo nano /etc/nginx/sites-available/parser-law

# Schimbă server_name în:
# server_name legislatie.issuemonitoring.ro;

# Activează site
sudo ln -s /etc/nginx/sites-available/parser-law /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔒 SSL Certificate

**Important:** Asigură-te că DNS-ul pentru `legislatie.issuemonitoring.ro` pointează la IP-ul VPS-ului!

```bash
# Verifică DNS
nslookup legislatie.issuemonitoring.ro

# Instalează Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obține certificat SSL
sudo certbot --nginx -d legislatie.issuemonitoring.ro
```

## ✅ Verificare Finală

```bash
# Test health check
curl https://legislatie.issuemonitoring.ro/health

# Accesează în browser
# https://legislatie.issuemonitoring.ro/docs
```

## 📚 Documentație Completă

Pentru deployment detaliat cu troubleshooting: **[DEPLOYMENT_VPS.md](./DEPLOYMENT_VPS.md)**
```

## ✅ Verificare

```bash
# Verificare containere
cd /opt/parser-law/db_service
docker compose ps

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Vezi logs
docker compose logs -f api

# Check database
docker exec legislatie_postgres psql -U legislatie_user -d monitoring_platform -c "SELECT COUNT(*) FROM legislatie.acte_legislative;"
```

## 📚 Documentație Completă

- **[DEPLOYMENT_VPS.md](./DEPLOYMENT_VPS.md)** - Ghid pas cu pas complet
- **[README.md](./README.md)** - Documentație aplicație
- **[db_service/README.md](./db_service/README.md)** - API documentation

---

**Need help?** Check the troubleshooting section in [DEPLOYMENT_VPS.md](./DEPLOYMENT_VPS.md)
