# Deployment Guide - Gunicorn & Systemd

Production deployment untuk Context API menggunakan **Gunicorn** (application server) dan **Systemd** (service manager).

## 📋 Prerequisites

- Linux server (Ubuntu/Debian/RHEL)
- Python 3.8+
- sudo/root access
- Domain name (optional, untuk production)

## 🚀 Deployment Steps

---

## Phase 1: Server Preparation

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv curl git
```

### 1.2 Create Application User
```bash
# Create non-root user untuk running app
sudo useradd -m -s /bin/bash contextapi

# Set home directory
export APP_USER=contextapi
export APP_HOME=/home/contextapi/rag-ai-cli
```

### 1.3 Setup Project Directory
```bash
sudo mkdir -p $APP_HOME
sudo chown -R $APP_USER:$APP_USER $APP_HOME
cd $APP_HOME
sudo -u $APP_USER git clone <your-repo-url> . 
# atau copy manual
```

---

## Phase 2: Application Setup

### 2.1 Create Virtual Environment
```bash
sudo -u $APP_USER python3 -m venv venv
```

### 2.2 Install Dependencies
```bash
sudo -u $APP_USER /bin/bash << 'EOF'
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install gunicorn
EOF
```

### 2.3 Verify Installation
```bash
sudo -u $APP_USER /bin/bash << 'EOF'
source venv/bin/activate
python -c "import flask; import gunicorn; print('OK')"
EOF
```

### 2.4 Check FAISS Index
```bash
ls -la /home/contextapi/rag-ai-cli/faiss_db/
```

Jika belum ada, build dengan:
```bash
sudo -u $APP_USER /bin/bash << 'EOF'
source venv/bin/activate
cd /home/contextapi/rag-ai-cli
python rag-ai.py "test query"
EOF
```

---

## Phase 3: Gunicorn Configuration

### 3.1 Create Gunicorn Config File

**File**: `/home/contextapi/rag-ai-cli/gunicorn_config.py`

```python
# Gunicorn Configuration
import multiprocessing

# Server socket configuration
bind = "127.0.0.1:8000"           # Listen on localhost:8000
backlog = 2048                      # Maximum pending connections

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"               # sync, gthread, eventlet, gevent
worker_connections = 1000
timeout = 90                        # Worker timeout in seconds
keepalive = 2

# Server mechanics
daemon = False                      # Run as daemon
pidfile = "/tmp/gunicorn.pid"
umask = 0
user = "contextapi"
group = "contextapi"
tmp_upload_dir = None

# SSL Configuration (optional, for HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
# ca_certs = "/path/to/ca_certs"

# Logging
accesslog = "/var/log/contextapi/access.log"
errorlog = "/var/log/contextapi/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "contextapi"

# Server hooks
def on_starting(server):
    print("Gunicorn server starting...")

def when_ready(server):
    print("Gunicorn server ready to accept connections")

def on_exit(server):
    print("Gunicorn server stopping...")
```

### 3.2 Create Environment File

**File**: `/home/contextapi/rag-ai-cli/.env.prod`

```env
# Production Environment
GOOGLE_API_KEY=your_production_api_key_here
FAISS_INDEX_PATH=/home/contextapi/rag-ai-cli/faiss_db
FAISS_INDEX_PATH_MISTRAL=/home/contextapi/rag-ai-cli/faiss_db_mistral
API_HOST=127.0.0.1
API_PORT=8000
FLASK_ENV=production
```

### 3.3 Create Logging Directory
```bash
sudo mkdir -p /var/log/contextapi
sudo chown contextapi:contextapi /var/log/contextapi
sudo chmod 755 /var/log/contextapi
```

### 3.4 Test Gunicorn Manually
```bash
sudo -u contextapi /bin/bash << 'EOF'
cd /home/contextapi/rag-ai-cli
source venv/bin/activate
export $(cat .env.prod | xargs)
gunicorn --config gunicorn_config.py context-api:app
EOF
```

Seharusnya output:
```
[INFO] Starting gunicorn 20.x.x
[INFO] Listening at: http://127.0.0.1:8000
[INFO] Using worker: sync
[INFO] Booting worker with pid: xxxx
```

Press `Ctrl+C` untuk stop.

---

## Phase 4: Systemd Service Setup

### 4.1 Create Systemd Service File

**File**: `/etc/systemd/system/contextapi.service`

```ini
[Unit]
Description=Context API - RAG AI Service
After=network.target
Documentation=https://your-docs-link

[Service]
Type=notify
User=contextapi
Group=contextapi
WorkingDirectory=/home/contextapi/rag-ai-cli

# Environment variables
EnvironmentFile=/home/contextapi/rag-ai-cli/.env.prod

# Virtual environment activation & app start
ExecStart=/home/contextapi/rag-ai-cli/venv/bin/gunicorn \
    --config /home/contextapi/rag-ai-cli/gunicorn_config.py \
    --pass-auth-header context-api:app

# Restart policy
Restart=on-failure
RestartSec=10s
StartLimitInterval=60s
StartLimitBurst=3

# Process management
KillMode=mixed              # Send SIGTERM to process group
KillSignal=SIGTERM

# Resource limits (optional)
StandardOutput=journal
StandardError=journal
SyslogIdentifier=contextapi

# Timeouts
TimeoutStartSec=30
TimeoutStopSec=15

# Security hardening (optional)
NoNewPrivileges=true
PrivateTmp=true
#ProtectSystem=strict
#ProtectHome=yes
#ReadWritePaths=/home/contextapi/rag-ai-cli/faiss_db

[Install]
WantedBy=multi-user.target
```

### 4.2 Create Service Start Script (Optional)

**File**: `/home/contextapi/rag-ai-cli/start.sh`

```bash
#!/bin/bash
set -e

# Load environment
export $(cat .env.prod | xargs)

# Activate virtual environment
source venv/bin/activate

# Start Gunicorn
exec gunicorn \
    --config gunicorn_config.py \
    --pass-auth-header \
    context-api:app
```

```bash
chmod +x /home/contextapi/rag-ai-cli/start.sh
sudo chown contextapi:contextapi /home/contextapi/rag-ai-cli/start.sh
```

---

## Phase 5: Enable & Start Service

### 5.1 Reload Systemd Daemon
```bash
sudo systemctl daemon-reload
```

### 5.2 Enable Service (Start on Boot)
```bash
sudo systemctl enable contextapi.service
```

### 5.3 Start Service
```bash
sudo systemctl start contextapi.service
```

### 5.4 Verify Service Status
```bash
sudo systemctl status contextapi.service
```

Output should show:
```
● contextapi.service - Context API - RAG AI Service
     Loaded: loaded (/etc/systemd/system/contextapi.service; enabled)
     Active: active (running) since ...
     Main PID: XXXX (gunicorn)
```

### 5.5 Check Service Logs
```bash
# Recent logs
sudo journalctl -u contextapi.service -n 50

# Follow logs in real-time
sudo journalctl -u contextapi.service -f

# Filter by date
sudo journalctl -u contextapi.service --since "2 hours ago"
```

---

## Phase 6: Nginx Reverse Proxy (Recommended)

### 6.1 Install Nginx
```bash
sudo apt install -y nginx
```

### 6.2 Create Nginx Config

**File**: `/etc/nginx/sites-available/contextapi`

```nginx
upstream contextapi_app {
    # Connect to Gunicorn socket
    server 127.0.0.1:8000;
    
    # Health check (optional)
    keepalive 32;
}

# HTTP redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    
    # Logging
    access_log /var/log/nginx/contextapi_access.log;
    error_log /var/log/nginx/contextapi_error.log;
    
    # Gzip compression
    gzip on;
    gzip_types text/plain application/json application/javascript text/xml;
    gzip_min_length 1024;
    
    # Rate limiting (optional)
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://contextapi_app;
        proxy_http_version 1.1;
        
        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint (no rate limit)
    location /health {
        proxy_pass http://contextapi_app;
        access_log off;
    }
}
```

### 6.3 Enable Nginx Config
```bash
sudo ln -s /etc/nginx/sites-available/contextapi /etc/nginx/sites-enabled/contextapi
sudo rm -f /etc/nginx/sites-enabled/default

# Test config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 6.4 Setup SSL Certificate (Let's Encrypt)
```bash
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

---

## Phase 7: Monitoring & Maintenance

### 7.1 Create Monitoring Script

**File**: `/usr/local/bin/check-contextapi.sh`

```bash
#!/bin/bash

API_URL="http://localhost:8000/health"
TIMEOUT=5

echo "Checking Context API health..."

response=$(curl -s -o /dev/null -w "%{http_code}" -m $TIMEOUT $API_URL)

if [ "$response" = "200" ]; then
    echo "✓ API is healthy (Status: 200)"
    exit 0
else
    echo "✗ API health check failed (Status: $response)"
    echo "Attempting to restart service..."
    sudo systemctl restart contextapi.service
    exit 1
fi
```

```bash
sudo chmod +x /usr/local/bin/check-contextapi.sh
```

### 7.2 Setup Cron Job for Monitoring
```bash
# Edit crontab
sudo crontab -e

# Add this line to check every 5 minutes
*/5 * * * * /usr/local/bin/check-contextapi.sh >> /var/log/contextapi-health.log 2>&1
```

### 7.3 Log Rotation

**File**: `/etc/logrotate.d/contextapi`

```
/var/log/contextapi/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 contextapi contextapi
    sharedscripts
    postrotate
        sudo systemctl reload contextapi.service > /dev/null 2>&1 || true
    endscript
}
```

### 7.4 Useful Commands

```bash
# Check service status
sudo systemctl status contextapi.service

# Restart service
sudo systemctl restart contextapi.service

# Stop service
sudo systemctl stop contextapi.service

# Start service
sudo systemctl start contextapi.service

# View recent logs
sudo journalctl -u contextapi.service -n 100

# Monitor in real-time
sudo journalctl -u contextapi.service -f

# Check resource usage
ps aux | grep gunicorn

# Check if port 8000 is listening
sudo lsof -i :8000

# Test API
curl http://localhost:8000/health
```

---

## Phase 8: Production Checklist

### Security
- [ ] Change GOOGLE_API_KEY ke production key
- [ ] Setup SSL/TLS certificates
- [ ] Enable firewall rules
- [ ] Setup fail2ban untuk brute force protection
- [ ] Regular backup FAISS index
- [ ] Setup secrets management (Vault, etc)

### Performance
- [ ] Tune Gunicorn workers (2*CPU+1)
- [ ] Setup caching layer (Redis, memcached)
- [ ] Enable Gzip compression di Nginx
- [ ] Setup CDN untuk static files
- [ ] Monitor memory usage

### Monitoring
- [ ] Setup health checks
- [ ] Configure logging aggregation
- [ ] Setup error tracking (Sentry, etc)
- [ ] Monitor API response times
- [ ] Alert on service failures

### Backup & Recovery
- [ ] Regular FAISS index backups
- [ ] Database snapshots (if using DB)
- [ ] Configuration backups
- [ ] Disaster recovery plan
- [ ] Tested restore procedures

---

## Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u contextapi.service -n 50

# Verify config
gunicorn --config gunicorn_config.py --check-config context-api:app

# Check permissions
ls -la /home/contextapi/rag-ai-cli/
```

### High memory usage
```bash
# Reduce worker count
# Edit gunicorn_config.py dan ubah workers

# Check for memory leaks
ps aux | grep gunicorn
```

### Slow response times
```bash
# Check Nginx logs
tail -f /var/log/nginx/contextapi_error.log

# Check Gunicorn logs
sudo journalctl -u contextapi.service -f

# Check server resources
top
```

### FAISS index not found
```bash
# Verify FAISS_INDEX_PATH di .env.prod
cat /home/contextapi/rag-ai-cli/.env.prod

# Check directory
ls -la /home/contextapi/rag-ai-cli/faiss_db/
```

### SSL certificate issues
```bash
# Check certificate expiry
sudo openssl x509 -in /etc/letsencrypt/live/your-domain/fullchain.pem -noout -dates

# Renew certificate
sudo certbot renew --force-renewal

# Test Nginx SSL
sudo nginx -t
```

---

## Performance Tuning

### Gunicorn Workers
```python
# gunicorn_config.py
import multiprocessing

# Formula: (2 * CPU_cores) + 1
workers = (multiprocessing.cpu_count() * 2) + 1

# Or for high-concurrency:
# workers = multiprocessing.cpu_count() * 4
```

### Connection Pooling
```python
# gunicorn_config.py
worker_connections = 1000      # Per worker
keepalive = 2                   # Keep-alive timeout
```

### Worker Timeout
```python
# Adjust based on query complexity
timeout = 120  # seconds
```

---

## Scaling Strategies

### Horizontal Scaling (Multiple Servers)
```
Load Balancer (Nginx/HAProxy)
         ↓
    ┌────┴────┐
    ↓         ↓
Server1    Server2
  (API)      (API)
    ↓         ↓
  Redis   Shared FAISS DB
```

### Load Balancer Config (Nginx)
```nginx
upstream contextapi_backend {
    server server1.com:8000 weight=1;
    server server2.com:8000 weight=1;
    server server3.com:8000 weight=1;
    
    keepalive 32;
}

server {
    listen 80;
    location / {
        proxy_pass http://contextapi_backend;
    }
}
```

---

## Backup Strategy

### Automated FAISS Index Backup
```bash
#!/bin/bash
BACKUP_DIR="/backups/contextapi"
FAISS_DIR="/home/contextapi/rag-ai-cli/faiss_db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/faiss_db_$TIMESTAMP.tar.gz $FAISS_DIR

# Keep only last 7 backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

Add to crontab:
```bash
# Backup daily at 2 AM
0 2 * * * /usr/local/bin/backup-contextapi.sh
```

---

## Useful Commands Summary

```bash
# Service management
sudo systemctl start contextapi
sudo systemctl stop contextapi
sudo systemctl restart contextapi
sudo systemctl reload contextapi
sudo systemctl status contextapi
sudo systemctl enable contextapi

# Logs
sudo journalctl -u contextapi.service -f
sudo tail -f /var/log/contextapi/access.log
sudo tail -f /var/log/contextapi/error.log

# Testing
curl http://localhost:8000/health
curl http://your-domain.com/api/context/info

# Process management
ps aux | grep gunicorn
kill -HUP <pid>  # Graceful reload
kill -TERM <pid> # Graceful shutdown

# Port checking
sudo lsof -i :8000
sudo netstat -tuln | grep 8000
```

---

## Support Resources

- **Gunicorn Docs**: https://docs.gunicorn.org/
- **Systemd Docs**: https://www.freedesktop.org/software/systemd/man/
- **Nginx Docs**: https://nginx.org/en/docs/
- **LetsEncrypt**: https://letsencrypt.org/
- **Flask Behind Proxy**: https://flask.palletsprojects.com/en/latest/deploying/

Selamat mendeploy! 🚀
