# 📂 Parser-Law Path Configuration

## Standard Deployment Paths

All scripts and documentation use these **standardized paths** to avoid confusion:

### Primary Paths
```bash
DEPLOY_DIR="/opt/parser-law"           # Main application directory
BACKUP_DIR="/opt/parser-law-backups"   # Backup storage
LOG_DIR="/var/log/parser-law"          # Application logs (if needed)
```

### Database Configuration
```bash
DB_NAME="legislatie_db"
DB_USER="legislatie_user"
DB_SCHEMA="legislatie"
```

### Docker Compose Files
```bash
COMPOSE_DB_SERVICE="/opt/parser-law/db_service/docker-compose.yml"
COMPOSE_SCHEDULER="/opt/parser-law/docker-compose.scheduler.yml"
```

---

## ✅ Updated Scripts

All scripts now source `scripts/common-config.sh` for consistency:

### Bash Scripts (VPS)
- ✅ `scripts/common-config.sh` - Central configuration (NEW)
- ✅ `scripts/deploy.sh` - Uses `/opt/parser-law`
- ✅ `scripts/rollback.sh` - Uses `/opt/parser-law`
- ✅ `scripts/test-migration.sh` - Uses `/opt/parser-law` (UPDATED)
- ✅ `scripts/setup-vps.sh` - Deploys to `/opt/parser-law`
- ✅ `scripts/deploy-vps.sh` - Initial setup to `/opt/parser-law`

### PowerShell Helpers (Windows)
- ✅ `scripts/deploy-helpers.ps1` - SSH to `/opt/parser-law`

---

## 🔧 Usage

### From VPS (SSH)
```bash
# All scripts expect to be in /opt/parser-law
cd /opt/parser-law

# Run any script
./scripts/deploy.sh
./scripts/rollback.sh
./scripts/test-migration.sh
```

### From Windows (PowerShell)
```powershell
# Helpers automatically use correct paths
deploy              # Deploys to /opt/parser-law
status              # Checks /opt/parser-law containers
logs                # Tails /opt/parser-law logs
rollback [backup]   # Rollback /opt/parser-law
```

---

## 🚫 Deprecated Paths

**DO NOT USE** these paths (legacy references removed):
- ❌ `/root/parser-law` - **NEVER** use this
- ❌ `~/parser-law` - **NEVER** use this
- ❌ Relative paths without `$DEPLOY_DIR` - **AVOID**

---

## 📝 Adding New Scripts

When creating new scripts, always:

1. **Source the common config:**
```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common-config.sh"

# Now use variables
cd $DEPLOY_DIR
echo "Working in: $DEPLOY_DIR"
```

2. **Use helper functions:**
```bash
log_info "Starting process..."
log_success "Process completed!"
log_error "Something went wrong!"
ensure_deploy_dir  # Ensures we're in /opt/parser-law
```

3. **Reference files with $DEPLOY_DIR:**
```bash
# Good ✅
docker-compose -f $DEPLOY_DIR/db_service/docker-compose.yml up -d

# Bad ❌
docker-compose -f db_service/docker-compose.yml up -d
docker-compose -f /root/parser-law/db_service/docker-compose.yml up -d
```

---

## 🔍 Verification

To verify all paths are correct:

```bash
# On VPS
cd /opt/parser-law
grep -r "/root/parser-law" scripts/ || echo "✅ No legacy paths found"
grep -r "DEPLOY_DIR" scripts/ | grep -v "/opt/parser-law" || echo "✅ All paths correct"
```

---

## 🎯 Why This Matters

**Consistency prevents:**
- ❌ Scripts failing with "directory not found"
- ❌ Confusion between development and production paths
- ❌ Backup/restore targeting wrong directories
- ❌ Docker compose files not found
- ❌ Database connections failing

**Centralized config provides:**
- ✅ Single source of truth
- ✅ Easy updates (change once in `common-config.sh`)
- ✅ Consistent error messages
- ✅ Predictable script behavior
- ✅ Easy onboarding for new developers
