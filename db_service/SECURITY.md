# Security & Authentication Guide

## Overview

This API implements **3 layers of security** to protect sensitive operations:

1. **API Key Authentication** - For AI processing and export endpoints
2. **IP Whitelisting** - Optional network-level restriction
3. **HTTPS/SSL** - Transport layer encryption (nginx)

---

## 1. API Key Authentication

### Protected Endpoints

**AI Processing:**
- `POST /api/v1/ai/process` - Trigger AI processing
- `POST /api/v1/ai/process/sync` - Sync AI processing
- `GET /api/v1/ai/status` - Get AI status
- `GET /api/v1/ai/pending` - List pending articles
- `GET /api/v1/ai/errors` - List failed articles
- `POST /api/v1/ai/retry/{id}` - Retry processing
- `POST /api/v1/ai/reset/{id}` - Reset article status

**Export:**
- `POST /api/v1/export/to-im` - Export to Issue Monitoring
- `POST /api/v1/export/to-im/sync` - Sync export
- `POST /api/v1/export/sync-updates` - Sync updates
- `GET /api/v1/export/status` - Get export status
- `GET /api/v1/export/pending` - List pending exports
- `GET /api/v1/export/completed` - List completed exports
- `GET /api/v1/export/errors` - List failed exports
- `POST /api/v1/export/retry/{id}` - Retry export
- `GET /api/v1/export/package/{id}` - Preview export package

### Public Endpoints (No Authentication)

- `GET /health` - Health check
- `GET /` - API info
- `GET /api/v1/acte` - List legislative acts
- `GET /api/v1/acte/{id}` - Get act details
- `GET /api/v1/articole` - List articles
- `GET /api/v1/articole/{id}` - Get article details

### How to Use API Key

**1. Generate API Key:**
```bash
# Option 1: OpenSSL
openssl rand -hex 32

# Option 2: Python
python -c "import secrets; print(secrets.token_hex(32))"

# Example output:
# a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

**2. Configure in `.env`:**
```bash
API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

**3. Send Requests with API Key:**

**Using cURL:**
```bash
curl -X POST "https://legislatie.issuemonitoring.ro/api/v1/ai/process" \
  -H "X-API-Key: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

**Using Python requests:**
```python
import requests

headers = {
    "X-API-Key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6",
    "Content-Type": "application/json"
}

response = requests.post(
    "https://legislatie.issuemonitoring.ro/api/v1/ai/process",
    headers=headers,
    json={"limit": 10}
)
```

**Using JavaScript fetch:**
```javascript
const response = await fetch('https://legislatie.issuemonitoring.ro/api/v1/ai/process', {
  method: 'POST',
  headers: {
    'X-API-Key': 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ limit: 10 })
});
```

### Error Responses

**Missing API Key:**
```json
{
  "detail": "API key missing. Provide via X-API-Key header."
}
```
Status: `401 Unauthorized`

**Invalid API Key:**
```json
{
  "detail": "Invalid API key"
}
```
Status: `403 Forbidden`

---

## 2. IP Whitelisting

### Configuration

**Allow all IPs (default):**
```bash
# .env
ALLOWED_IPS=
```

**Restrict to specific IPs:**
```bash
# .env
ALLOWED_IPS=127.0.0.1,192.168.1.100,77.237.235.158
```

### Error Response

**Blocked IP:**
```json
{
  "detail": "Access denied for IP: 203.0.113.42"
}
```
Status: `403 Forbidden`

---

## 3. External API Security

### AI Service (OpenAI/Anthropic)

**Communication Flow:**
```
[Your Server] --HTTPS--> [OpenAI/Anthropic API]
              <--HTTPS--
```

- ✅ **Encrypted:** All communication uses HTTPS/TLS
- ✅ **Authenticated:** Uses API keys from environment variables
- ✅ **Rate Limited:** Built-in delays between requests
- ✅ **Error Handling:** Retry logic with exponential backoff

**Configuration:**
```bash
# .env
OPENAI_API_KEY=sk-proj-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

**Where it runs:**
- AI processing runs **on your VPS server**
- Sends requests **to OpenAI/Anthropic cloud APIs**
- **No user data** exposed to unauthorized parties

### Issue Monitoring Export

**Communication Flow:**
```
[Your Server] --HTTPS--> [Issue Monitoring API]
              <--HTTPS--
```

- ✅ **Encrypted:** HTTPS/TLS
- ✅ **Authenticated:** Bearer token authentication
- ✅ **Retry Logic:** Handles transient failures

**Configuration:**
```bash
# .env
ISSUE_MONITORING_API_URL=https://api.issuemonitoring.ro/v1
ISSUE_MONITORING_API_KEY=your_key_here
```

---

## Security Best Practices

### Development Environment

```bash
# .env (local)
API_KEY=  # Empty = no authentication required
ALLOWED_IPS=  # Empty = allow all IPs
LOG_LEVEL=DEBUG
```

### Production Environment

```bash
# .env.production
API_KEY=<strong-random-key-64-chars>
ALLOWED_IPS=127.0.0.1,<scheduler-ip>,<admin-ip>
LOG_LEVEL=INFO
API_RELOAD=false
```

### Key Management

1. **Never commit `.env` files to git**
   - Already in `.gitignore`
   - Use `.env.example` as template

2. **Rotate keys regularly**
   - Generate new API key every 90 days
   - Update in `.env` and restart service

3. **Use different keys for different environments**
   - Development: `dev_key_xxx`
   - Staging: `staging_key_xxx`
   - Production: `prod_key_xxx`

4. **Store keys securely**
   - Use environment variables (not hardcoded)
   - Consider using secrets management (HashiCorp Vault, AWS Secrets Manager)

### Nginx Configuration (HTTPS)

```nginx
server {
    listen 443 ssl http2;
    server_name legislatie.issuemonitoring.ro;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/legislatie.issuemonitoring.ro/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/legislatie.issuemonitoring.ro/privkey.pem;
    
    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Proxy to FastAPI
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name legislatie.issuemonitoring.ro;
    return 301 https://$server_name$request_uri;
}
```

---

## Monitoring & Logging

### Check API Access Logs

```bash
# View recent API requests
tail -f /var/log/nginx/access.log

# Filter for AI endpoints
tail -f /var/log/nginx/access.log | grep "/api/v1/ai"

# Filter for failed auth attempts
tail -f /var/log/nginx/access.log | grep "401\|403"
```

### Application Logs

```bash
# View API logs
docker logs -f legislatie_api

# Filter for security events
docker logs legislatie_api | grep "Unauthorized\|Forbidden"
```

---

## Testing Authentication

### Test with Valid API Key

```bash
curl -X GET "http://localhost:8000/api/v1/ai/status" \
  -H "X-API-Key: your_key_here"
```

Expected: `200 OK` with status data

### Test without API Key

```bash
curl -X GET "http://localhost:8000/api/v1/ai/status"
```

Expected: `401 Unauthorized`

### Test with Invalid API Key

```bash
curl -X GET "http://localhost:8000/api/v1/ai/status" \
  -H "X-API-Key: wrong_key"
```

Expected: `403 Forbidden`

---

## FAQ

### Q: Can anyone see the legislation data?
**A:** Public endpoints (GET /acte, GET /articole) are open. AI/Export operations require API key.

### Q: Is data encrypted in transit?
**A:** Yes, when using HTTPS (nginx). Always use HTTPS in production.

### Q: Where do AI API calls happen?
**A:** On your VPS server → OpenAI/Anthropic cloud. Your API key authenticates these calls.

### Q: Can I disable authentication for testing?
**A:** Yes, set `API_KEY=` (empty) in `.env`. **Never do this in production!**

### Q: How do I change the API key?
**A:** 
1. Generate new key: `openssl rand -hex 32`
2. Update `.env`: `API_KEY=new_key`
3. Restart: `docker-compose restart legislatie_api`
4. Update scheduler/client applications with new key

### Q: What if API key is leaked?
**A:** 
1. Generate new key immediately
2. Update `.env` and restart service
3. Check logs for unauthorized access
4. Consider enabling IP whitelist
