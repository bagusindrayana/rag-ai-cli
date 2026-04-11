# Deployment Files Summary

Complete deployment documentation dan helper scripts untuk Context API.

## 📁 Deployment Files Created

### 1. **DEPLOYMENT.md** - Comprehensive Deployment Guide
**Size**: ~10,000 words  
**Language**: English  
**Content**:
- Complete setup guide (8 phases)
- Gunicorn configuration
- Systemd service setup
- Nginx reverse proxy
- SSL/TLS setup
- Monitoring & maintenance
- Troubleshooting
- Performance tuning
- Scaling strategies

**Best for**: Developers & DevOps engineers who want detailed technical reference

---

### 2. **DEPLOYMENT_GUIDE_ID.md** - Practical Indonesian Guide
**Size**: ~5,000 words  
**Language**: Bahasa Indonesia  
**Content**:
- 5-minute quick start
- Step-by-step manual deployment
- Architecture explanation
- Common issues & fixes
- Maintenance commands
- Performance tuning
- Security best practices
- Scaling guide

**Best for**: Indonesian-speaking teams, practical quick reference

---

### 3. **deploy.sh** - Automated Deployment Script
**Type**: Bash script  
**Features**:
- Fully automated setup
- User & permission management
- Virtual environment setup
- Gunicorn configuration
- Systemd service creation
- Log rotation setup
- Health monitoring setup
- Interactive prompts for configuration
- Color-coded output

**Usage**:
```bash
sudo bash deploy.sh
```

**Time**: ~5-10 minutes for complete setup

---

### 4. **troubleshoot.sh** - Diagnostics & Troubleshooting Script
**Type**: Bash script  
**Features**:
- Service status checking
- Port availability check
- Process monitoring
- Log viewing
- API testing
- FAISS index verification
- Permission checking
- Resource monitoring
- Interactive menu or one-command execution
- Color-coded diagnostic output

**Usage**:
```bash
# Interactive mode
sudo bash troubleshoot.sh

# Single check
sudo bash troubleshoot.sh status
sudo bash troubleshoot.sh test
sudo bash troubleshoot.sh full
```

**Available Commands**:
- `status` - Service status
- `process` - Process check
- `ports` - Port checking
- `logs` - View logs
- `test` - Test API
- `faiss` - Check FAISS
- `env` - Environment check
- `resources` - System resources
- `permissions` - Permission check
- `restart` - Restart service
- `key` - API key check
- `full` - Complete diagnostic

---

### 5. **nginx.conf.example** - Nginx Reverse Proxy Configuration
**Type**: Nginx configuration file  
**Features**:
- SSL/TLS setup (Let's Encrypt)
- HTTP to HTTPS redirect
- Security headers
- Rate limiting
- Gzip compression
- CORS support
- Static file serving
- Health check endpoint
- Error handling

**Usage**:
```bash
# Copy to nginx
sudo cp nginx.conf.example /etc/nginx/sites-available/contextapi

# Edit domain
sudo nano /etc/nginx/sites-available/contextapi

# Enable
sudo ln -s /etc/nginx/sites-available/contextapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Security Features Included**:
- HSTS (HTTP Strict Transport Security)
- X-Content-Type-Options
- X-Frame-Options
- CSP (Content Security Policy)
- Rate limiting
- DDoS protection

---

## 🚀 Quick Deployment Workflows

### Workflow 1: Fully Automated (5-10 minutes)

```bash
# 1. SSH to server
ssh user@server
cd /path/to/rag-ai-cli

# 2. Run deployment script
sudo bash deploy.sh

# 3. Verify
sudo systemctl status contextapi
curl http://localhost:8000/health
```

### Workflow 2: Manual Step-by-Step

Follow `DEPLOYMENT_GUIDE_ID.md` or `DEPLOYMENT.md` for detailed steps.

### Workflow 3: With Nginx & SSL

```bash
# 1. Automated setup
sudo bash deploy.sh

# 2. Setup Nginx
sudo cp nginx.conf.example /etc/nginx/sites-available/contextapi
# Edit domain in file
sudo nginx -t
sudo systemctl restart nginx

# 3. Get SSL cert
sudo certbot certonly --nginx -d your-domain.com

# 4. Verify
curl https://your-domain.com/health
```

---

## 🔍 Diagnostics Workflow

```bash
# Complete system check
sudo bash troubleshoot.sh full

# Or run specific checks
sudo bash troubleshoot.sh status    # Service status
sudo bash troubleshoot.sh test      # API functionality
sudo bash troubleshoot.sh logs      # View logs
sudo bash troubleshoot.sh restart   # Restart service
```

---

## 📊 Deployment Architecture

```
┌─────────────────────────────────────────────────────┐
│              User/Client Request                    │
└────────────────────┬────────────────────────────────┘
                     │
    ┌────────────────┴──────────────────┐
    │   Nginx (Port 80/443)            │
    │  - SSL/TLS termination           │
    │  - Rate limiting                 │
    │  - Compression                   │
    │  - Security headers              │
    └────────────────┬──────────────────┘
                     │ (localhost:8000)
    ┌────────────────┴──────────────────┐
    │   Gunicorn (Port 8000)           │
    │  - Multiple workers              │
    │  - Process management            │
    │  - Error handling                │
    └────────────────┬──────────────────┘
                     │
    ┌────────────────┴──────────────────┐
    │   Context API (Flask)             │
    │  - Request routing                │
    │  - Business logic                 │
    └────────────────┬──────────────────┘
                     │
    ┌────────────────┴──────────────────┐
    │   FAISS Vector Database           │
    │  - Document embeddings            │
    │  - Similarity search              │
    └────────────────────────────────────┘

Managed by Systemd:
  ├─ Auto-start on boot
  ├─ Auto-restart on crash
  ├─ Process supervision
  └─ Centralized logging
```

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Server ready (Linux, 2 GB RAM min)
- [ ] FAISS index built
- [ ] Google API Key obtained
- [ ] Domain name (optional)
- [ ] SSL cert (if using HTTPS)

### Deployment
- [ ] Run deploy.sh successfully
- [ ] Service enabled and running
- [ ] FAISS index accessible
- [ ] Health check passing
- [ ] Logs clean (no errors)

### Post-Deployment
- [ ] Nginx configured (if needed)
- [ ] SSL certificate installed
- [ ] Firewall rules set
- [ ] Monitoring enabled
- [ ] Backups scheduled
- [ ] Team trained on operations

### Security
- [ ] .env.prod permissions restricted
- [ ] Service runs as non-root
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Logs monitored

---

## 🔄 File Relationships

```
Context API Deployment
│
├─ DEPLOYMENT.md
│  └─ Detailed technical reference
│     └─ References Nginx config
│     └─ References troubleshooting
│
├─ DEPLOYMENT_GUIDE_ID.md
│  └─ Indonesian practical guide
│     └─ References automated script
│     └─ Common issues section
│
├─ deploy.sh (AUTOMATED)
│  ├─ Reads gunicorn_config.py
│  ├─ Creates .env.prod
│  ├─ Enables contextapi.service
│  └─ References troubleshoot.sh
│
├─ troubleshoot.sh (DIAGNOSTICS)
│  ├─ Checks contextapi.service
│  ├─ Tests API endpoints
│  ├─ Verifies FAISS
│  └─ Helps fix issues
│
└─ nginx.conf.example (REVERSE PROXY)
   ├─ SSL configuration
   ├─ Rate limiting
   └─ Security headers
```

---

## 📖 Documentation Maps

### For Quick Start (< 15 minutes)
1. SSH to server
2. Clone project
3. Run `sudo bash deploy.sh`
4. Run `sudo bash troubleshoot.sh full` to verify
5. Done! ✅

### For Detailed Understanding
1. Read: `DEPLOYMENT_GUIDE_ID.md` (Indonesian) or `DEPLOYMENT.md` (English)
2. Run: `sudo bash deploy.sh` with explanations
3. Test: `sudo bash troubleshoot.sh` for all checks
4. Monitor: `sudo journalctl -u contextapi.service -f`

### For Troubleshooting
1. Run: `sudo bash troubleshoot.sh full`
2. Check: Specific sections in `DEPLOYMENT_GUIDE_ID.md`
3. Fix: Follow recommended solutions
4. Verify: `sudo bash troubleshoot.sh test`

---

## 🎯 Key Deployment Concepts Explained

### Why Systemd?
- **Automatic restarts**: Service auto-recovers on crash
- **Boot detection**: App starts when server boots
- **Process supervision**: Monitors and manages process
- **Centralized logging**: All logs in journalctl
- **Standard approach**: Industry standard for Linux services

### Why Gunicorn?
- **Production ready**: Designed for production use
- **Multiple workers**: Handle concurrent requests
- **Worker management**: Auto-restart dead workers
- **Graceful reloads**: Zero-downtime updates
- **Well supported**: Large community & documentation

### Why Nginx?
- **Reverse proxy**: Routes requests to Gunicorn
- **Load balancing**: Can distribute to multiple backend servers
- **SSL termination**: Handles HTTPS
- **Compression**: Gzip compression support
- **Security**: Built-in rate limiting, headers

---

## 🔧 Common Configuration Changes

### Change Port
```python
# gunicorn_config.py
bind = "0.0.0.0:9000"  # Change from 8000 to 9000
```

### Change Workers
```python
# gunicorn_config.py
workers = 4  # Explicit count instead of calculated
```

### Change Timeout
```python
# gunicorn_config.py
timeout = 120  # Increase from 90 for slow queries
```

### Change Host Binding
```python
# gunicorn_config.py
bind = "0.0.0.0:8000"  # Accept from any interface
```

After changes:
```bash
sudo systemctl restart contextapi
```

---

## 📞 Operating Commands Reference

```bash
# Service Management
sudo systemctl start contextapi       # Start
sudo systemctl stop contextapi        # Stop
sudo systemctl restart contextapi     # Restart
sudo systemctl reload contextapi      # Reload (graceful)
sudo systemctl status contextapi      # Status check
sudo systemctl enable contextapi      # Enable auto-start
sudo systemctl disable contextapi     # Disable auto-start

# Logging
sudo journalctl -u contextapi.service -f              # Follow logs
sudo journalctl -u contextapi.service -n 50           # Last 50 lines
sudo journalctl -u contextapi.service --since "1 hour ago"  # Since

# Testing
curl http://localhost:8000/health
curl http://your-domain.com/api/context/info
sudo bash troubleshoot.sh test

# Diagnostics
sudo bash troubleshoot.sh full
ps aux | grep gunicorn
sudo lsof -i :8000
```

---

## 💡 Next Steps After Deployment

1. **Monitoring**: Setup alerts (Sentry, DataDog, etc)
2. **Backups**: Schedule FAISS index backups
3. **Updates**: Plan update strategy
4. **Scaling**: Plan for horizontal scaling if needed
5. **Documentation**: Update team documentation
6. **Training**: Train team on operations

---

## 🆘 Getting Help

1. **First**, run complete diagnostics:
   ```bash
   sudo bash troubleshoot.sh full
   ```

2. **Then**, check relevant documentation:
   - `DEPLOYMENT_GUIDE_ID.md` - Indonesian guide
   - `DEPLOYMENT.md` - Detailed English reference
   - Particular section in troubleshooting

3. **Finally**, if still stuck:
   - Check logs: `sudo journalctl -u contextapi.service -f`
   - Check permissions: `ls -la /home/contextapi/rag-ai-cli/`
   - Restart service: `sudo systemctl restart contextapi`

---

Selamat mendeploy! 🚀
