# 🚀 Quick Start - Deployment pe VPS

## Opțiunea 1: Setup Automat (Recomandat)

```bash
# Conectează-te la VPS
ssh root@your-vps-ip

# Rulează script-ul de setup
curl -fsSL https://raw.githubusercontent.com/octavianissuemonitoring/parser-law/master/scripts/setup-vps.sh | bash

# Configurează environment
cd /opt/parser-law/db_service
cp .env.production .env
nano .env  # Editează password-ul

# Start servicii
docker compose up -d

# Creare tabele
docker exec -i legislatie_postgres psql -U legislatie_user -d monitoring_platform < create_tables.sql
```

## Opțiunea 2: Manual Setup

Vezi ghidul complet: [DEPLOYMENT_VPS.md](./DEPLOYMENT_VPS.md)

## 🔧 Configurare Nginx

```bash
# Copiază configurația
sudo cp nginx.conf.example /etc/nginx/sites-available/parser-law
sudo nano /etc/nginx/sites-available/parser-law  # Editează your-domain.com

# Activează site
sudo ln -s /etc/nginx/sites-available/parser-law /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 🔒 SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com
```

## ✅ Verificare

```bash
# Test API
curl http://your-domain.com/health
curl http://your-domain.com/docs

# Vezi logs
docker compose logs -f api
```

## 📚 Documentație Completă

- **[DEPLOYMENT_VPS.md](./DEPLOYMENT_VPS.md)** - Ghid pas cu pas complet
- **[README.md](./README.md)** - Documentație aplicație
- **[db_service/README.md](./db_service/README.md)** - API documentation

---

**Need help?** Check the troubleshooting section in [DEPLOYMENT_VPS.md](./DEPLOYMENT_VPS.md)
