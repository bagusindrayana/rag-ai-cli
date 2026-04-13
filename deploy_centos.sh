#!/bin/bash
# Context API Deployment Setup Helper (CentOS/RHEL)
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="contextapi"
APP_USER="contextapi"
APP_PORT=8000
APP_HOME="/home/$APP_USER/rag-ai-cli"
PYTHON_BIN="python3"

print_header() { echo -e "${BLUE}========================================${NC}"; echo -e "${BLUE}$1${NC}"; echo -e "${BLUE}========================================${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }

detect_pkg_manager() {
    if command -v dnf >/dev/null 2>&1; then
        PKG_MANAGER=dnf
    else
        PKG_MANAGER=yum
    fi
}

check_root() { if [[ $EUID -ne 0 ]]; then print_error "Script harus dijalankan sebagai root (sudo)"; exit 1; fi }

check_os() {
    if ! grep -E "CentOS|Red Hat|Fedora|Rocky|AlmaLinux" /etc/os-release >/dev/null 2>&1; then
        print_warning "OS mungkin bukan CentOS/RHEL; lanjutkan dengan hati-hati..."
    fi
    print_success "OS compatibility check passed"
}

install_dependencies() {
    print_header "Installing System Dependencies"
    detect_pkg_manager
    $PKG_MANAGER -y makecache
    # packages: python3, pip, venv, git, curl, semanage (policycoreutils-python-utils), firewalld, cronie
    $PKG_MANAGER -y install $PYTHON_BIN $PYTHON_BIN-pip python3-virtualenv python3-venv git curl policycoreutils-python-utils firewalld cronie || true

    # Ensure pip is available
    if ! command -v pip3 >/dev/null 2>&1; then
        $PKG_MANAGER -y install python3-pip || true
    fi

    systemctl enable --now firewalld.service || true
    systemctl enable --now crond.service || true

    print_success "System dependencies installed"
}

create_user() {
    print_header "Creating Application User"
    if id "$APP_USER" &>/dev/null; then
        print_warning "User $APP_USER sudah exist"
    else
        useradd -m -s /bin/bash $APP_USER
        print_success "User $APP_USER created"
    fi
}

setup_directories() {
    print_header "Setting Up Directories"
    mkdir -p "$APP_HOME"
    chown -R $APP_USER:$APP_USER "$APP_HOME"
    print_success "Directories created: $APP_HOME"

    mkdir -p /var/log/$APP_NAME
    chown $APP_USER:$APP_USER /var/log/$APP_NAME
    print_success "Log directory created"
}

setup_venv() {
    print_header "Setting Up Virtual Environment"
    sudo -u $APP_USER $PYTHON_BIN -m venv "$APP_HOME/venv"
    print_success "Virtual environment created"
}

install_requirements() {
    print_header "Installing Python Requirements"
    sudo -u $APP_USER bash -c "source $APP_HOME/venv/bin/activate && pip install --upgrade pip setuptools wheel && if [ -f $APP_HOME/requirements.txt ]; then pip install -r $APP_HOME/requirements.txt; fi && pip install gunicorn"
    print_success "Python requirements installed"
}

create_gunicorn_config() {
    print_header "Creating Gunicorn Configuration"
    cat > $APP_HOME/gunicorn_config.py << 'EOF'
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 90
keepalive = 2

# Server mechanics
daemon = False
user = "contextapi"
group = "contextapi"

# Logging
accesslog = "/var/log/contextapi/access.log"
errorlog = "/var/log/contextapi/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)s'

# Process naming
proc_name = "contextapi"
EOF
    chown $APP_USER:$APP_USER $APP_HOME/gunicorn_config.py
    print_success "Gunicorn config created"
}

create_env_file() {
    print_header "Creating Environment File"
    if [ -f "$APP_HOME/.env.prod" ]; then
        print_warning ".env.prod already exists"
        return
    fi
    read -p "Enter Google API Key: " GOOGLE_API_KEY
    cat > $APP_HOME/.env.prod << EOF
GOOGLE_API_KEY=$GOOGLE_API_KEY
FAISS_INDEX_PATH=$APP_HOME/faiss_db
FAISS_INDEX_PATH_MISTRAL=$APP_HOME/faiss_db_mistral
API_HOST=127.0.0.1
API_PORT=8000
FLASK_ENV=production
EOF
    chown $APP_USER:$APP_USER $APP_HOME/.env.prod
    chmod 600 $APP_HOME/.env.prod
    print_success "Environment file created"
}

create_systemd_service() {
    print_header "Creating Systemd Service File"
    cat > /etc/systemd/system/$APP_NAME.service << EOF
[Unit]
Description=Context API - RAG AI Service
After=network.target
Documentation=file://$APP_HOME/DEPLOYMENT.md

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_HOME
EnvironmentFile=$APP_HOME/.env.prod

ExecStart=$APP_HOME/venv/bin/gunicorn \
    --config $APP_HOME/gunicorn_config.py \
    context-api:app

Restart=on-failure
RestartSec=10s
StartLimitInterval=60s
StartLimitBurst=3

KillMode=mixed
KillSignal=SIGTERM

StandardOutput=journal
StandardError=journal
SyslogIdentifier=$APP_NAME

TimeoutStartSec=30
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    print_success "Systemd service created"
}

configure_selinux_and_permissions() {
    print_header "Configuring SELinux (if enabled) and permissions"
    if command -v sestatus >/dev/null 2>&1 && sestatus | grep -q "enabled"; then
        print_info "SELinux is enabled — applying basic file contexts"
        # semanage may not be present; attempt but ignore failures
        semanage fcontext -a -t httpd_sys_rw_content_t "$APP_HOME(/.*)?" 2>/dev/null || true
        restorecon -R "$APP_HOME" 2>/dev/null || true

        semanage fcontext -a -t var_log_t "/var/log/$APP_NAME(/.*)?" 2>/dev/null || true
        restorecon -R "/var/log/$APP_NAME" 2>/dev/null || true
    else
        print_info "SELinux not enabled or semanage not available — skipping"
    fi
    chown -R $APP_USER:$APP_USER "$APP_HOME"
}

configure_firewall() {
    print_header "Configuring Firewall"
    if command -v firewall-cmd >/dev/null 2>&1; then
        firewall-cmd --permanent --add-port=${APP_PORT}/tcp || true
        firewall-cmd --reload || true
        print_success "Firewall opened port ${APP_PORT}"
    else
        print_warning "firewall-cmd not found — ensure port ${APP_PORT} is accessible"
    fi
}

setup_monitoring() {
    print_header "Setting Up Monitoring"
    cat > /usr/local/bin/check-$APP_NAME.sh << 'EOF'
#!/bin/bash
API_URL="http://localhost:8000/health"
response=$(curl -s -o /dev/null -w "%{http_code}" -m 5 $API_URL)
if [ "$response" = "200" ]; then
    echo "✓ API is healthy"
    exit 0
else
    echo "✗ API health check failed (Status: $response)"
    systemctl restart $APP_NAME.service
    exit 1
fi
EOF
    chmod +x /usr/local/bin/check-$APP_NAME.sh
    (crontab -l 2>/dev/null | grep -v "check-$APP_NAME"; echo "*/5 * * * * /usr/local/bin/check-$APP_NAME.sh >> /var/log/$APP_NAME-health.log 2>&1") | crontab -
    print_success "Health check script created and cron job added"
}

create_logrotate() {
    print_header "Setting Up Log Rotation"
    cat > /etc/logrotate.d/$APP_NAME << EOF
/var/log/$APP_NAME/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $APP_USER $APP_USER
    sharedscripts
    postrotate
        systemctl reload $APP_NAME.service > /dev/null 2>&1 || true
    endscript
}
EOF
    print_success "Log rotation configured"
}

enable_and_start_service() {
    print_header "Starting Service"
    systemctl enable $APP_NAME.service
    systemctl start $APP_NAME.service
    sleep 2
    if systemctl is-active --quiet $APP_NAME.service; then
        print_success "Service started successfully"
    else
        print_error "Failed to start service"
        journalctl -u $APP_NAME.service -n 20
        return 1
    fi
}

test_api() {
    print_header "Testing API"
    sleep 2
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        print_success "API is responding"
    else
        print_error "API is not responding"
        print_info "Check logs: sudo journalctl -u $APP_NAME.service -f"
        return 1
    fi
}

show_next_steps() {
    print_header "Deployment Complete!"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Verify service status:"
    echo "   sudo systemctl status $APP_NAME.service"
    echo ""
    echo "2. Check logs:"
    echo "   sudo journalctl -u $APP_NAME.service -f"
    echo ""
    echo "3. Test API:"
    echo "   curl http://localhost:8000/health"
    echo ""
    echo "4. (Optional) Setup Nginx reverse proxy:"
    echo "   See DEPLOYMENT.md for Nginx configuration"
    echo ""
}

main() {
    print_header "Context API Deployment Setup (CentOS/RHEL)"
    print_info "This script will setup Context API with Gunicorn + Systemd on CentOS/RHEL"
    check_root
    check_os
    read -p "Continue with deployment? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Deployment cancelled"
        exit 1
    fi
    install_dependencies
    create_user
    setup_directories
    setup_venv
    install_requirements
    create_gunicorn_config
    create_env_file
    create_systemd_service
    configure_selinux_and_permissions
    configure_firewall
    setup_monitoring
    create_logrotate
    enable_and_start_service
    test_api
    echo
    show_next_steps
    print_success "Deployment setup completed!"
}

# Run main
main
