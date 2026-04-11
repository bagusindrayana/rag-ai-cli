# Cara Deploy dengan Gunicorn & Systemd - Ringkasan Praktis

Panduan lengkap deployment Context API dengan Gunicorn application server dan Systemd service manager di Linux.

## 🎯 Ringkasan Singkat (5 Menit)

Jika hanya mau cepat:

```bash
# 1. SSH ke server & clone project
ssh user@server
git clone <repo> rag-ai-cli && cd rag-ai-cli

# 2. Jalankan automated deployment
sudo bash deploy.sh

# 3. Verifikasi
sudo systemctl status contextapi
curl http://localhost:8000/health
```

Done! API berjalan di port 8000 via Systemd.

---

## 📖 Penjelasan Lengkap

### Apa itu Gunicorn?
- **Application Server** untuk Python (seperti Tomcat untuk Java)
- Menjalankan Flask app dengan multiple workers
- Komunikasi antar process via HTTP
- Lebih stable & production-ready dari development server

### Apa itu Systemd?
- **Service Manager** untuk Linux
- Auto-start service saat boot
- Auto-restart jika crash
- Centralized logging
- Monitoring & management mudah

### Arsitektur Deployment

```
User Request
    ↓
Nginx (Port 80/443)  ← Reverse Proxy, SSL, Load Balancing
    ↓
Gunicorn (Port 8000) ← Application Server, Multiple Workers
    ↓
Context API (Flask)
    ↓
FAISS Vector DB
```

---

## 🚀 Step-by-Step Manual Deployment

### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv curl git nginx certbot

# Create application user
sudo useradd -m -s /bin/bash contextapi

# Setup directories
sudo mkdir -p /home/contextapi/rag-ai-cli
sudo chown contextapi:contextapi /home/contextapi/rag-ai-cli
```

### Step 2: Clone & Setup Application

```bash
# Login sebagai app user
sudo -u contextapi -s

# Clone application
cd /home/contextapi
git clone <your-repo-url> rag-ai-cli
cd rag-ai-cli

# Create virtual environment
python3 -m venv venv

# Activate & install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Verify
python -c "import flask, gunicorn; print('OK')"
```

### Step 3: Prepare FAISS Index

```bash
# Build FAISS index (from app user)
source venv/bin/activate
python rag-ai.py "test query"

# Verify index created
ls -la faiss_db/
```

### Step 4: Configure Gunicorn

Copy file [gunicorn_config.py](gunicorn_config.py) dari dokumentasi atau:

```bash
# Manual configuration
cat > /home/contextapi/rag-ai-cli/gunicorn_config.py << 'EOF'
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 90
keepalive = 2
user = "contextapi"
group = "contextapi"
accesslog = "/var/log/contextapi/access.log"
errorlog = "/var/log/contextapi/error.log"
loglevel = "info"
proc_name = "contextapi"
EOF
```

### Step 5: Create Environment File

```bash
# Create .env.prod
sudo cat > /home/contextapi/rag-ai-cli/.env.prod << 'EOF'
GOOGLE_API_KEY=your_key_here
FAISS_INDEX_PATH=/home/contextapi/rag-ai-cli/faiss_db
API_HOST=127.0.0.1
API_PORT=8000
FLASK_ENV=production
EOF

# Set permissions
sudo chmod 600 /home/contextapi/rag-ai-cli/.env.prod
```

### Step 6: Create Log Directory

```bash
sudo mkdir -p /var/log/contextapi
sudo chown contextapi:contextapi /var/log/contextapi
sudo chmod 755 /var/log/contextapi
```

### Step 7: Create Systemd Service File

Edit `/etc/systemd/system/contextapi.service`:

```bash
sudo nano /etc/systemd/system/contextapi.service
```

Content:
```ini
[Unit]
Description=Context API - RAG AI Service
After=network.target

[Service]
Type=notify
User=contextapi
Group=contextapi
WorkingDirectory=/home/contextapi/rag-ai-cli
EnvironmentFile=/home/contextapi/rag-ai-cli/.env.prod

ExecStart=/home/contextapi/rag-ai-cli/venv/bin/gunicorn \
    --config /home/contextapi/rag-ai-cli/gunicorn_config.py \
    context-api:app

Restart=on-failure
RestartSec=10s

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Step 8: Enable & Start Service

```bash
# Reload daemon
sudo systemctl daemon-reload

# Enable (auto-start on boot)
sudo systemctl enable contextapi.service

# Start service
sudo systemctl start contextapi.service

# Verify
sudo systemctl status contextapi.service
```

### Step 9: Test API Locally

```bash
# Test health check
curl http://localhost:8000/health

# Should return: {"status": "healthy", ...}
```

### Step 10: Setup Nginx Reverse Proxy

Create `/etc/nginx/sites-available/contextapi`:

```nginx
upstream contextapi_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://contextapi_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/contextapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 11: Setup SSL (Optional but Recommended)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d your-domain.com

# Update nginx.conf with SSL
# See DEPLOYMENT.md for full config
```

---

## 📋 Checklist Verification

```bash
# Verify systemd service
sudo systemctl status contextapi.service

# Verify process running
ps aux | grep gunicorn

# Verify port listening
sudo lsof -i :8000

# Verify logs
sudo journalctl -u contextapi.service -f

# Test API
curl http://localhost:8000/health
curl http://your-domain.com/api/context/info

# Check resources
free -h
df -h
```

---

## 🛑 Common Issues & Fixes

### "Failed to start service"
```bash
# Check logs
sudo journalctl -u contextapi.service -n 50

# Most common:
# 1. Port already in use
sudo lsof -i :8000
kill -9 <PID>

# 2. Permission issue
sudo chown contextapi:contextapi /home/contextapi/rag-ai-cli -R

# 3. FAISS not found
ls /home/contextapi/rag-ai-cli/faiss_db/
```

### "Cannot connect to API"
```bash
# Check if service running
sudo systemctl status contextapi

# Check if port listening
sudo lsof -i :8000

# Restart service
sudo systemctl restart contextapi
```

### "API timeout"
```bash
# Increase timeout in gunicorn_config.py
timeout = 120  # seconds

# Restart
sudo systemctl restart contextapi
```

### "Google API Key error"
```bash
# Verify .env.prod
sudo cat /home/contextapi/rag-ai-cli/.env.prod

# Update if needed
sudo nano /home/contextapi/rag-ai-cli/.env.prod

# Reload service
sudo systemctl restart contextapi
```

---

## 🔧 Maintenance Commands

### Daily Operations

```bash
# Check status
sudo systemctl status contextapi

# View logs (real-time)
sudo journalctl -u contextapi.service -f

# View logs (last 100 lines)
sudo journalctl -u contextapi.service -n 100

# Restart service
sudo systemctl restart contextapi

# Stop service
sudo systemctl stop contextapi

# Start service
sudo systemctl start contextapi
```

### Monitoring

```bash
# Check resource usage
ps aux | grep gunicorn

# Memory usage
free -h
top -p $(pgrep -f gunicorn | head -1)

# Disk usage
df -h

# Check logs for errors
sudo grep ERROR /var/log/contextapi/error.log
```

### Updates

```bash
# Update application
cd /home/contextapi/rag-ai-cli
git pull
source venv/bin/activate
pip install -r requirements.txt

# Rebuild FAISS (if new documents)
python rag-ai.py "test query"

# Restart service
sudo systemctl restart contextapi
```

---

## 📊 Performance Tuning

### Gunicorn Worker Count
```python
# In gunicorn_config.py
# Formula: (2 × CPU cores) + 1

import multiprocessing
workers = multiprocessing.cpu_count() * 2 + 1

# For 4-core server: workers = 9
# For 8-core server: workers = 17
```

### Memory Optimization
```bash
# Monitor memory
watch -n 1 'ps aux | grep gunicorn | head -5'

# Reduce workers if memory high
# or increase if CPU low
```

---

## 🔐 Security Best Practices

```bash
# Set proper permissions
sudo chmod 600 /home/contextapi/rag-ai-cli/.env.prod
sudo chmod 755 /home/contextapi/rag-ai-cli

# Use firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Regular updates
sudo apt update && sudo apt upgrade -y

# Monitor logs
sudo journalctl -u contextapi.service -f

# Rotate logs
# Already configured in /etc/logrotate.d/contextapi
```

---

## 📈 Scaling to Multiple Servers

```
Domain: your-domain.com
    ↓
Load Balancer (HAProxy/AWS ELB)
    ↓
┌───────────────┬──────────────┬──────────────┐
↓               ↓              ↓
API Server 1  API Server 2  API Server 3
:8000         :8000         :8000
```

### Load Balancer Config (HAProxy)
```
frontend web
    bind *:80
    default_backend api_servers

backend api_servers
    balance roundrobin
    server api1 server1.com:8000 check
    server api2 server2.com:8000 check
    server api3 server3.com:8000 check
```

---

## 🚨 Emergency Recovery

### Restart All

```bash
# Stop
sudo systemctl stop contextapi

# Verify stopped
sudo lsof -i :8000 | grep LISTEN

# Start
sudo systemctl start contextapi

# Verify
sudo systemctl status contextapi
```

### View Full Logs

```bash
# All errors
sudo journalctl -u contextapi.service --priority=err

# Last hour
sudo journalctl -u contextapi.service --since "1 hour ago"

# Export to file
sudo journalctl -u contextapi.service --boot > /tmp/contextapi-logs.txt
```

### Hard Reset

```bash
# Kill all processes
pkill -f gunicorn

# Clear cache
# (jika applicable)

# Restart
sudo systemctl restart contextapi
```

---

## 📞 Important Files Reference

| File | Purpose |
|------|---------|
| `/etc/systemd/system/contextapi.service` | Systemd service config |
| `/home/contextapi/rag-ai-cli/gunicorn_config.py` | Gunicorn settings |
| `/home/contextapi/rag-ai-cli/.env.prod` | Environment variables |
| `/var/log/contextapi/access.log` | Access logs |
| `/var/log/contextapi/error.log` | Error logs |
| `/etc/nginx/sites-available/contextapi` | Nginx reverse proxy |

---

## 📚 Useful Resources

- [Systemd Service Manual](https://manpages.ubuntu.com/manpages/focal/man5/systemd.service.5.html)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Proxy Guide](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)

---

## ✅ Verification Checklist

Setelah deployment:

- [ ] Service running: `sudo systemctl status contextapi` → `active (running)`
- [ ] Port listening: `sudo lsof -i :8000` → shows gunicorn
- [ ] Health check: `curl http://localhost:8000/health` → returns 200 OK
- [ ] FAISS loaded: `curl http://localhost:8000/api/context/info` → shows indices
- [ ] Logs clean: `sudo journalctl -u contextapi.service -n 20` → no errors
- [ ] Auto-restart: `sudo systemctl is-enabled contextapi` → enabled

**Selamat! API Anda sudah live di production! 🎉**
