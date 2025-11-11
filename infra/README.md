# Infrastructure Documentation

This directory contains infrastructure-as-code documentation and configuration for the Parser Law application.

## Directory Structure

```
infra/
├── README.md                 # This file
├── vps-setup.md             # Complete VPS setup documentation
├── ansible/                 # Ansible playbooks (future)
│   ├── playbook.yml
│   └── inventory.yml
└── terraform/               # Terraform configs (future)
    ├── main.tf
    └── variables.tf
```

## Current VPS Setup

**Provider**: DigitalOcean / Custom VPS  
**IP**: 77.237.235.158  
**OS**: Ubuntu 20.04 LTS  
**User**: root  

### Installed Components

1. **Docker & Docker Compose**
   - Docker Engine 24.0+
   - Docker Compose v2.20+

2. **Nginx**
   - Version: 1.18+
   - Configured as reverse proxy
   - SSL/TLS with Let's Encrypt (certbot)

3. **PostgreSQL**
   - Version: 15-alpine (containerized)
   - Database: monitoring_platform
   - Schema: legislatie

4. **Application**
   - FastAPI application (containerized)
   - Scheduler (containerized)
   - Path: /opt/parser-law

### Network Configuration

- **Public Port 80**: HTTP → HTTPS redirect
- **Public Port 443**: HTTPS → Nginx → Container 8000
- **Container Network**: parser-law-network (bridge)

### File Locations

```
/opt/parser-law/              # Application root
├── db_service/               # API code
├── docker-compose.yml        # Production compose file
├── .env                      # Environment variables (secret)
├── logs/                     # Application logs
├── backups/                  # Database backups
│   ├── daily/               # Automated daily backups
│   └── v1.0-stable/         # Tagged version backups
└── nginx.conf               # Nginx configuration
```

## Setup Instructions

See: `vps-setup.md` for detailed setup steps.

## Automation (Future)

- **Ansible Playbooks**: Automated VPS provisioning
- **Terraform**: Infrastructure definition as code
- **CI/CD**: GitHub Actions for automated deployment

## Security

- SSH key authentication only (password auth disabled)
- Firewall (ufw) configured:
  - Allow 22 (SSH)
  - Allow 80 (HTTP)
  - Allow 443 (HTTPS)
  - Deny all other incoming
- Docker containers isolated in bridge network
- Database not exposed to public internet

## Monitoring

- Docker healthchecks
- Application logs: /opt/parser-law/logs/
- Database logs: docker logs legislatie_postgres
- Nginx logs: /var/log/nginx/

## Backup Strategy

- **Daily**: Automated database backup (cron)
- **Pre-deployment**: Manual backup with tag
- **Retention**: 7 days for daily, indefinite for tagged
- **Location**: /opt/parser-law/backups/

## Disaster Recovery

See: `ROLLBACK_INSTRUCTIONS.md` in project root.

**RTO** (Recovery Time Objective): 5 minutes  
**RPO** (Recovery Point Objective): 24 hours (last daily backup)
