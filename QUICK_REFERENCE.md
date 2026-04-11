# Deployment Quick Reference Card

**Print or bookmark this for quick access during deployment.**

---

## 🚀 QUICK START (5 minutes)

```bash
# 1. Connect & clone
ssh user@server
git clone <repo> && cd rag-ai-cli

# 2. Automated deployment
sudo bash deploy.sh

# 3. Verify
sudo systemctl status contextapi
curl http://localhost:8000/health
```

---

## 📋 MANUAL STEPS (if needed)

```bash
# System setup
sudo apt update && apt install -y python3 python3-pip python3-venv git

# Create user
sudo useradd -m contextapi
sudo mkdir -p /home/contextapi/rag-ai-cli
sudo chown contextapi /home/contextapi/rag-ai-cli

# Setup app
sudo -u contextapi -s
cd /home/contextapi/rag-ai-cli
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn

# Build FAISS
python rag-ai.py "test query"

# Create .env.prod (with GOOGLE_API_KEY)
echo "GOOGLE_API_KEY=xxx" > .env.prod

# Exit to root
exit

# Create systemd service (see DEPLOYMENT.md appendix)
# Edit /etc/systemd/system/contextapi.service

# Start service
sudo systemctl daemon-reload
sudo systemctl enable contextapi
sudo systemctl start contextapi
```

---

## ✅ VERIFICATION

| Check | Command | Expected |
|-------|---------|----------|
| Service Status | `sudo systemctl status contextapi` | `active (running)` |
| Process Running | `ps aux \| grep gunicorn` | Shows gunicorn process |
| Port Listening | `sudo lsof -i :8000` | Shows gunicorn listening |
| Health Endpoint | `curl http://localhost:8000/health` | 200 OK + JSON |
| Logs Clean | `sudo journalctl -u contextapi.service -n 20` | No ERROR lines |
| FAISS Loaded | `curl http://localhost:8000/api/context/info` | Shows indices |

---

## 🔍 TROUBLESHOOTING QUICK FIXES

| Problem | Command | Cause |
|---------|---------|-------|
| Won't start | `sudo journalctl -u contextapi.service -n 20` | Check error logs |
| Port in use | `sudo lsof -i :8000; kill -9 <PID>` | Port 8000 taken |
| FAISS missing | `ls /home/contextapi/rag-ai-cli/faiss_db/` | Run: `python rag-ai.py "test"` |
| API timeout | `nano gunicorn_config.py; timeout = 120` | Increase timeout |
| API key error | `cat .env.prod \| grep GOOGLE_API_KEY` | Set correct key |
| Permission denied | `sudo chown contextapi -R /home/contextapi` | Fix ownership |

---

## 🛠️ COMMON OPERATIONS

| Task | Command |
|------|---------|
| Start service | `sudo systemctl start contextapi` |
| Stop service | `sudo systemctl stop contextapi` |
| Restart service | `sudo systemctl restart contextapi` |
| View logs (realtime) | `sudo journalctl -u contextapi.service -f` |
| View last logs | `sudo journalctl -u contextapi.service -n 100` |
| Test API | `curl http://localhost:8000/health` |
| Check process | `ps aux \| grep gunicorn` |
| Check port | `sudo lsof -i :8000` |
| Full diagnostic | `sudo bash troubleshoot.sh full` |
| Check resources | `free -h && df -h` |
| Tail access log | `tail -f /var/log/contextapi/access.log` |
| Tail error log | `tail -f /var/log/contextapi/error.log` |

---

## 🌐 NGINX SETUP (Optional)

```bash
# Copy config
sudo cp nginx.conf.example /etc/nginx/sites-available/contextapi

# Edit domain
sudo nano /etc/nginx/sites-available/contextapi
# Change: your-domain.com

# Enable
sudo ln -s /etc/nginx/sites-available/contextapi /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test & restart
sudo nginx -t
sudo systemctl restart nginx

# Get SSL (Let's Encrypt)
sudo certbot certonly --nginx -d your-domain.com
```

---

## 🔐 SECURITY CHECKLIST

```bash
# Fix permissions
sudo chmod 600 /home/contextapi/.env.prod

# Setup firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Check for exposed files
sudo find /home/contextapi -name ".env*" -type f

# Set correct ownership
sudo chown -R contextapi /home/contextapi/rag-ai-cli
```

---

## 📊 CONFIGURATION FILES

| File | Location | Purpose |
|------|----------|---------|
| Gunicorn Config | `gunicorn_config.py` | Server settings |
| Environment | `.env.prod` | API keys & paths |
| Systemd Service | `/etc/systemd/system/contextapi.service` | Service definition |
| Nginx Config | `/etc/nginx/sites-available/contextapi` | Reverse proxy |
| Access Log | `/var/log/contextapi/access.log` | HTTP logs |
| Error Log | `/var/log/contextapi/error.log` | Application errors |

---

## 🔧 TUNING

| Setting | Default | For More Performance |
|---------|---------|----------------------|
| Workers | `cpu_count * 2 + 1` | Same for most cases |
| Timeout | 90s | Increase to 120-180s |
| Keepalive | 2s | Increase to 5s |
| Body Size | 100MB | Adjust as needed |

Edit `gunicorn_config.py` and restart:
```bash
sudo systemctl restart contextapi
```

---

## 📱 MONITORING SETUP (Optional)

```bash
# Health check every 5 minutes
sudo crontab -e
# Add:
*/5 * * * * curl http://localhost:8000/health > /dev/null 2>&1

# Or create alert script
sudo nano /usr/local/bin/check-contextapi.sh
sudo chmod +x /usr/local/bin/check-contextapi.sh
```

---

## 📈 SCALING

### Add more workers
```python
# gunicorn_config.py
workers = 8  # Increase from default
```

### Add more servers
```
Load Balancer (Nginx)
     ↓
  [Server 1:8000]
  [Server 2:8000]
  [Server 3:8000]
```

### Vertical scaling
- More CPU → increase workers
- More RAM → handle more concurrent requests
- Faster storage → better FAISS performance

---

## 📞 HELP COMMANDS

```bash
# Full diagnostic report
sudo bash troubleshoot.sh full

# Interactive troubleshooting menu
sudo bash troubleshoot.sh

# Show systemd logs
sudo journalctl -u contextapi.service

# Check if everything is working
curl -s http://localhost:8000/health | jq .

# Performance check
ps aux | grep gunicorn
top -p $(pgrep -f gunicorn | head -1)
```

---

## ⏰ POST-DEPLOYMENT TASKS

- [ ] Setup automated backups for FAISS
- [ ] Configure external logging (Sentry, ELK, etc)
- [ ] Setup monitoring & alerts
- [ ] Document team SOPs
- [ ] Train team on operations
- [ ] Setup SSL auto-renewal (certbot)
- [ ] Schedule regular health checks
- [ ] Plan disaster recovery

---

## 🆘 EMERGENCY COMMANDS

```bash
# Emergency restart
sudo systemctl restart contextapi && sleep 3 && curl http://localhost:8000/health

# Clear & restart
sudo systemctl stop contextapi
sleep 2
pkill -f gunicorn
sudo systemctl start contextapi

# Force kill stuck process
pkill -9 -f gunicorn
sudo systemctl start contextapi

# View all errors
sudo journalctl -u contextapi.service --priority=err
```

---

## 📚 DOCUMENTATION REFERENCE

| Document | Best For |
|----------|----------|
| `DEPLOYMENT_GUIDE_ID.md` | Indonesian speakers, practical guide |
| `DEPLOYMENT.md` | English speakers, detailed reference |
| `troubleshoot.sh` | Running diagnostics & fixing issues |
| `deploy.sh` | Automated setup |
| `nginx.conf.example` | Reverse proxy configuration |
| This file | Quick reference during deployment |

---

## 💾 BACKUP STRATEGY

```bash
# Backup FAISS index
tar -czf /backups/faiss_db_$(date +%Y%m%d).tar.gz \
    /home/contextapi/rag-ai-cli/faiss_db/

# Backup config
tar -czf /backups/contextapi_config_$(date +%Y%m%d).tar.gz \
    /etc/systemd/system/contextapi.service \
    /home/contextapi/rag-ai-cli/.env.prod

# Automate (add to crontab)
# 0 2 * * * /path/to/backup-script.sh
```

---

## 🎯 TYPICAL DEPLOYMENT FLOW

```
Day 0 - Selection & Planning
  └─ Choose server, plan capacity
     └─ Get Google API key
        └─ Prepare domain (optional)

Day 1 - Setup
  └─ SSH to server
     └─ Clone repo
        └─ Run sudo bash deploy.sh (10 min)
           └─ Run sudo bash troubleshoot.sh full (verify)

Day 1 - Configuration (if needed)
  └─ Setup Nginx reverse proxy (15 min)
     └─ Get SSL certificate (5 min)
        └─ Configure monitoring (20 min)

Day 1 - Testing
  └─ API health checks
     └─ Query testing
        └─ Load testing

Day 1 - Go Live
  └─ Point domain to server
     └─ Monitor logs
        └─ Team training

Post-Deployment
  └─ Daily monitoring
     └─ Weekly backups
        └─ Regular updates
```

---

**Last Updated**: 2024  
**Version**: 1.0  
**Deploy Command**: `sudo bash deploy.sh`  
**Status Check**: `sudo systemctl status contextapi`  
**Logs**: `sudo journalctl -u contextapi.service -f`

---

Print this page or save as bookmark for quick reference! 🚀
