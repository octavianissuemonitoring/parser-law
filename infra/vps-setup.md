# VPS Setup Documentation

Complete step-by-step guide for setting up the Parser Law application on a new VPS server.

**Target OS**: Ubuntu 20.04 LTS or later  
**Architecture**: x86_64  
**Minimum Requirements**: 2GB RAM, 2 CPU cores, 20GB storage  

---

## Table of Contents

1. [Initial Server Setup](#1-initial-server-setup)
2. [Docker Installation](#2-docker-installation)
3. [Nginx Installation](#3-nginx-installation)
4. [Application Deployment](#4-application-deployment)
5. [SSL Certificate Setup](#5-ssl-certificate-setup)
6. [Automated Backups](#6-automated-backups)
7. [Monitoring Setup](#7-monitoring-setup)
8. [Security Hardening](#8-security-hardening)

---

## 1. Initial Server Setup

### 1.1 Connect to VPS

```bash
# From local machine
ssh root@YOUR_VPS_IP

# Update system packages
apt update && apt upgrade -y

# Set timezone
timedatectl set-timezone Europe/Bucharest

# Check timezone
timedatectl
```

### 1.2 Create Application User (Optional)

```bash
# Create non-root user for application
adduser parser-law-admin
usermod -aG sudo parser-law-admin

# Switch to new user
su - parser-law-admin
```

**Note**: For simplicity, current setup uses root. Consider creating dedicated user for production.

### 1.3 Configure Firewall

```bash
# Install UFW (if not installed)
apt install ufw -y

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH
ufw allow 22/tcp

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable

# Check status
ufw status verbose
```

---

## 2. Docker Installation

### 2.1 Install Docker Engine

```bash
# Remove old versions
apt remove docker docker-engine docker.io containerd runc

# Install dependencies
apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt update
apt install -y docker-ce docker-ce-cli containerd.io

# Verify installation
docker --version
```

### 2.2 Install Docker Compose

```bash
# Download Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
chmod +x /usr/local/bin/docker-compose

# Create symlink (optional)
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Verify installation
docker-compose --version
```

### 2.3 Configure Docker

```bash
# Start Docker service
systemctl start docker
systemctl enable docker

# Verify Docker is running
systemctl status docker

# Test Docker
docker run hello-world
```

---

## 3. Nginx Installation

### 3.1 Install Nginx

```bash
# Install Nginx
apt install nginx -y

# Start and enable Nginx
systemctl start nginx
systemctl enable nginx

# Check status
systemctl status nginx

# Verify (should see Nginx welcome page)
curl http://localhost
```

### 3.2 Configure Nginx as Reverse Proxy

```bash
# Create Nginx configuration
nano /etc/nginx/sites-available/parser-law

# Add configuration (see nginx.conf.example in project root)
# Copy content from nginx.conf.example

# Example minimal config:
cat > /etc/nginx/sites-available/parser-law << 'EOF'
server {
    listen 80;
    server_name legislatie.issuemonitoring.ro;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/parser-law /etc/nginx/sites-enabled/

# Remove default site
rm /etc/nginx/sites-enabled/default

# Test configuration
nginx -t

# Reload Nginx
systemctl reload nginx
```

---

## 4. Application Deployment

### 4.1 Prepare Application Directory

```bash
# Create application directory
mkdir -p /opt/parser-law
cd /opt/parser-law

# Create required subdirectories
mkdir -p logs backups/daily export_csv rezultate
```

### 4.2 Clone Repository

```bash
# Install git if needed
apt install git -y

# Clone repository
git clone https://github.com/octavianissuemonitoring/parser-law.git /opt/parser-law

# Set correct permissions
chown -R root:root /opt/parser-law
chmod -R 755 /opt/parser-law
```

### 4.3 Configure Environment

```bash
cd /opt/parser-law

# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env

# Required changes for VPS:
# POSTGRES_HOST=legislatie_postgres  (NOT localhost!)
# POSTGRES_PASSWORD=<strong_password>
# API_HOST=0.0.0.0
# ENVIRONMENT=production
# DEBUG=false
```

**CRITICAL**: Set strong passwords in `.env` file!

### 4.4 Initialize Database

```bash
cd /opt/parser-law/db_service

# Start only database first
docker-compose up -d postgres

# Wait for database to be ready
sleep 10

# Initialize database schema
docker exec -i legislatie_postgres psql -U parser_user -d monitoring_platform < init.sql
docker exec -i legislatie_postgres psql -U parser_user -d monitoring_platform < create_tables.sql

# Verify tables created
docker exec -i legislatie_postgres psql -U parser_user -d monitoring_platform -c "\dt legislatie.*"
```

### 4.5 Start Application

```bash
cd /opt/parser-law

# Build and start all services
docker-compose up -d --build

# Check container status
docker-compose ps

# Check logs
docker-compose logs -f api

# Verify API is running
curl http://localhost:8000/health
# Expected: {"status": "healthy", "version": "1.0.0"}
```

---

## 5. SSL Certificate Setup

### 5.1 Install Certbot

```bash
# Install Certbot for Nginx
apt install certbot python3-certbot-nginx -y
```

### 5.2 Obtain SSL Certificate

```bash
# Obtain and install certificate (interactive)
certbot --nginx -d legislatie.issuemonitoring.ro

# Follow prompts:
# - Enter email address
# - Agree to terms
# - Choose redirect HTTP to HTTPS (recommended)

# Verify certificate
certbot certificates
```

### 5.3 Auto-renewal Setup

```bash
# Test renewal process
certbot renew --dry-run

# Certbot automatically adds cron job for renewal
# Check it's there:
systemctl list-timers | grep certbot

# Manual renewal (if needed)
certbot renew
```

---

## 6. Automated Backups

### 6.1 Create Backup Script

```bash
# Create backup script
cat > /opt/parser-law/scripts/backup-daily.sh << 'EOF'
#!/bin/bash
# Daily database backup script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/parser-law/backups/daily"

# Create backup
docker exec legislatie_postgres pg_dump -U parser_user -d monitoring_platform > "$BACKUP_DIR/db_$DATE.sql"

# Compress backup
gzip "$BACKUP_DIR/db_$DATE.sql"

# Keep only last 7 days
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +7 -delete

# Log backup
echo "$(date): Backup completed - db_$DATE.sql.gz" >> /opt/parser-law/logs/backup.log
EOF

# Make executable
chmod +x /opt/parser-law/scripts/backup-daily.sh
```

### 6.2 Setup Cron Job

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/parser-law/scripts/backup-daily.sh

# Verify cron job
crontab -l
```

### 6.3 Test Backup

```bash
# Run backup manually
/opt/parser-law/scripts/backup-daily.sh

# Check backup created
ls -lh /opt/parser-law/backups/daily/

# Verify backup integrity
gunzip -c /opt/parser-law/backups/daily/db_*.sql.gz | head -20
```

---

## 7. Monitoring Setup

### 7.1 Docker Health Checks

```bash
# Check container health
docker ps
# Look for "healthy" status

# Check specific container
docker inspect legislatie_api | grep -A 10 "Health"

# View health logs
docker inspect legislatie_api --format='{{json .State.Health}}' | jq
```

### 7.2 Log Rotation

```bash
# Create logrotate configuration
cat > /etc/logrotate.d/parser-law << 'EOF'
/opt/parser-law/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF

# Test logrotate
logrotate -d /etc/logrotate.d/parser-law

# Force rotation (test)
logrotate -f /etc/logrotate.d/parser-law
```

### 7.3 Monitoring Script

```bash
# Create monitoring script
cat > /opt/parser-law/scripts/monitor.sh << 'EOF'
#!/bin/bash
# Check application health

API_URL="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL)

if [ "$RESPONSE" != "200" ]; then
    echo "$(date): API unhealthy - HTTP $RESPONSE" >> /opt/parser-law/logs/monitor.log
    # Send alert (email/webhook)
    # curl -X POST https://hooks.slack.com/... -d "API down"
else
    echo "$(date): API healthy" >> /opt/parser-law/logs/monitor.log
fi
EOF

# Make executable
chmod +x /opt/parser-law/scripts/monitor.sh

# Add to cron (every 5 minutes)
crontab -e
# */5 * * * * /opt/parser-law/scripts/monitor.sh
```

---

## 8. Security Hardening

### 8.1 SSH Configuration

```bash
# Edit SSH config
nano /etc/ssh/sshd_config

# Recommended changes:
PermitRootLogin prohibit-password  # Or "no" for even more security
PasswordAuthentication no
PubkeyAuthentication yes
Port 22  # Consider changing to non-standard port

# Restart SSH
systemctl restart sshd
```

### 8.2 Fail2ban Installation

```bash
# Install fail2ban
apt install fail2ban -y

# Create local config
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true
EOF

# Start fail2ban
systemctl start fail2ban
systemctl enable fail2ban

# Check status
fail2ban-client status
```

### 8.3 Docker Security

```bash
# Enable Docker content trust
export DOCKER_CONTENT_TRUST=1

# Restrict container capabilities
# (Already configured in docker-compose.yml with security_opt)

# Regular security updates
apt update && apt upgrade -y

# Set up unattended upgrades
apt install unattended-upgrades -y
dpkg-reconfigure -plow unattended-upgrades
```

### 8.4 Database Security

```bash
# Ensure database is NOT exposed to internet
docker inspect legislatie_postgres | grep HostPort
# Should be empty (no port mapping to host)

# Strong password in .env
# Change default passwords immediately
```

---

## 9. Deployment Checklist

Use this checklist when deploying to a new VPS:

### Pre-deployment

- [ ] VPS provisioned (2GB RAM, 2 CPU, 20GB storage)
- [ ] Ubuntu 20.04+ installed
- [ ] SSH access configured
- [ ] DNS A record points to VPS IP
- [ ] Firewall rules planned

### Initial Setup

- [ ] System updated (`apt update && apt upgrade`)
- [ ] Timezone set (`timedatectl set-timezone Europe/Bucharest`)
- [ ] UFW firewall configured (22, 80, 443)
- [ ] Docker installed and running
- [ ] Docker Compose installed
- [ ] Nginx installed and running

### Application Setup

- [ ] Application directory created (`/opt/parser-law`)
- [ ] Repository cloned
- [ ] `.env` file configured with strong passwords
- [ ] Database initialized (init.sql, create_tables.sql)
- [ ] Docker containers built and started
- [ ] API health check passing (`curl http://localhost:8000/health`)

### Web Setup

- [ ] Nginx reverse proxy configured
- [ ] SSL certificate obtained (Certbot)
- [ ] HTTPS redirect enabled
- [ ] Certificate auto-renewal tested

### Backups & Monitoring

- [ ] Daily backup script created
- [ ] Backup cron job configured
- [ ] Test backup created and verified
- [ ] Monitoring script configured
- [ ] Log rotation configured

### Security

- [ ] SSH hardened (key-only, no password)
- [ ] Fail2ban installed and configured
- [ ] Docker security settings applied
- [ ] Database not exposed to internet
- [ ] Strong passwords set for all services

### Final Verification

- [ ] Public URL accessible (https://legislatie.issuemonitoring.ro)
- [ ] API documentation accessible (`/docs`)
- [ ] Database contains data (if migrated)
- [ ] Docker healthchecks passing
- [ ] Logs being written (`/opt/parser-law/logs/`)
- [ ] Backups being created (`/opt/parser-law/backups/daily/`)

---

## 10. Troubleshooting

### Issue: Cannot connect to database

```bash
# Check container is running
docker ps | grep postgres

# Check logs
docker logs legislatie_postgres

# Verify network
docker network inspect legislatie_network

# Test connection from API container
docker exec legislatie_api psql -h legislatie_postgres -U parser_user -d monitoring_platform -c "SELECT 1;"
```

### Issue: Nginx 502 Bad Gateway

```bash
# Check API container is running
docker ps | grep api

# Check API logs
docker logs legislatie_api

# Test API locally
curl http://localhost:8000/health

# Check Nginx config
nginx -t

# Check Nginx error logs
tail -f /var/log/nginx/error.log
```

### Issue: SSL certificate not renewing

```bash
# Check Certbot timer
systemctl list-timers | grep certbot

# Test renewal manually
certbot renew --dry-run

# Check Certbot logs
cat /var/log/letsencrypt/letsencrypt.log
```

### Issue: Database out of space

```bash
# Check disk usage
df -h

# Check database size
docker exec legislatie_postgres psql -U parser_user -d monitoring_platform -c "SELECT pg_size_pretty(pg_database_size('monitoring_platform'));"

# Clean old backups
find /opt/parser-law/backups/daily -name "db_*.sql.gz" -mtime +7 -delete

# Vacuum database
docker exec legislatie_postgres psql -U parser_user -d monitoring_platform -c "VACUUM FULL;"
```

---

## 11. Maintenance Tasks

### Weekly

- [ ] Check disk space (`df -h`)
- [ ] Review application logs
- [ ] Check Docker container status
- [ ] Verify backups are being created

### Monthly

- [ ] Update system packages (`apt update && apt upgrade`)
- [ ] Review and rotate logs
- [ ] Check SSL certificate expiration
- [ ] Review firewall rules

### Quarterly

- [ ] Full backup and test restore
- [ ] Security audit
- [ ] Update Docker images
- [ ] Review and update documentation

---

## 12. Contacts & Resources

**Admin**: octavian@issuemonitoring.ro  
**VPS IP**: 77.237.235.158  
**Domain**: legislatie.issuemonitoring.ro  

**Documentation**:
- Docker: https://docs.docker.com/
- Nginx: https://nginx.org/en/docs/
- Certbot: https://certbot.eff.org/
- PostgreSQL: https://www.postgresql.org/docs/

**Internal Docs**:
- `DEVELOPMENT_GUIDE.md` - Development standards
- `DATABASE_DOCUMENTATION.md` - Database schema
- `ROLLBACK_INSTRUCTIONS.md` - Emergency procedures

---

**Last Updated**: 2025-11-11  
**Version**: 1.0.0
