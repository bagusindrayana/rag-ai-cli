#!/bin/bash
# Context API Troubleshooting & Debugging Helper

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_section() {
    echo -e "\n${BLUE}→ $1${NC}"
}

# 1. Check service status
check_service_status() {
    print_header "Service Status Check"
    
    print_section "Systemd Service Status"
    sudo systemctl status contextapi.service
    
    print_section "Service Enable Status"
    if systemctl is-enabled --quiet contextapi.service; then
        print_success "Service is enabled (will auto-start on boot)"
    else
        print_warning "Service is NOT enabled"
    fi
    
    print_section "Service Active Status"
    if systemctl is-active --quiet contextapi.service; then
        print_success "Service is active (running)"
    else
        print_error "Service is NOT active"
    fi
}

# 2. Check process
check_process() {
    print_header "Process Check"
    
    print_section "Gunicorn Processes"
    if ps aux | grep -v grep | grep gunicorn > /dev/null; then
        ps aux | grep gunicorn | grep -v grep
        print_success "Gunicorn processes found"
    else
        print_error "No Gunicorn processes found"
    fi
}

# 3. Check ports
check_ports() {
    print_header "Port Check"
    
    print_section "Port 8000 (Gunicorn)"
    if sudo lsof -i :8000 2>/dev/null; then
        print_success "Port 8000 is listening"
    else
        print_error "Port 8000 is NOT listening"
    fi
    
    print_section "Port 80 (HTTP)"
    if sudo lsof -i :80 2>/dev/null; then
        print_success "Port 80 is listening"
    else
        print_warning "Port 80 is NOT listening (Nginx might not be running)"
    fi
    
    print_section "Port 443 (HTTPS)"
    if sudo lsof -i :443 2>/dev/null; then
        print_success "Port 443 is listening"
    else
        print_warning "Port 443 is NOT listening"
    fi
}

# 4. Check logs
check_logs() {
    print_header "Recent Logs"
    
    print_section "Last 30 Systemd Log Entries"
    sudo journalctl -u contextapi.service -n 30
    
    print_section "Last 20 Access Log Entries"
    if [ -f /var/log/contextapi/access.log ]; then
        tail -20 /var/log/contextapi/access.log
    else
        print_warning "Access log not found"
    fi
    
    print_section "Last 20 Error Log Entries"
    if [ -f /var/log/contextapi/error.log ]; then
        tail -20 /var/log/contextapi/error.log
    else
        print_warning "Error log not found"
    fi
}

# 5. Test API
test_api() {
    print_header "API Tests"
    
    print_section "Health Check (Direct)"
    if response=$(curl -s -w "\n%{http_code}" http://localhost:8000/health 2>/dev/null); then
        http_code=$(echo "$response" | tail -1)
        body=$(echo "$response" | head -n -1)
        
        if [ "$http_code" = "200" ]; then
            print_success "Health check passed (Status: $http_code)"
            echo "Response: $body"
        else
            print_error "Health check failed (Status: $http_code)"
            echo "Response: $body"
        fi
    else
        print_error "Cannot reach API at localhost:8000"
    fi
    
    print_section "Get Info"
    if response=$(curl -s http://localhost:8000/api/context/info 2>/dev/null); then
        if echo "$response" | grep -q "vector_stores"; then
            print_success "Got API info"
            echo "$response" | jq '.' 2>/dev/null || echo "$response"
        else
            print_error "Invalid response from /api/context/info"
            echo "$response"
        fi
    else
        print_error "Cannot reach /api/context/info"
    fi
}

# 6. Check FAISS
check_faiss() {
    print_header "FAISS Index Check"
    
    print_section "Gemini FAISS DB"
    FAISS_PATH="/home/contextapi/rag-ai-cli/faiss_db"
    if [ -d "$FAISS_PATH" ] && [ -f "$FAISS_PATH/index.faiss" ]; then
        print_success "Gemini FAISS index found"
        ls -lh $FAISS_PATH/
    else
        print_error "Gemini FAISS index NOT found"
        print_warning "Build with: python rag-ai.py \"test query\""
    fi
    
    print_section "Mistral FAISS DB"
    FAISS_MISTRAL="/home/contextapi/rag-ai-cli/faiss_db_mistral"
    if [ -d "$FAISS_MISTRAL" ] && [ -f "$FAISS_MISTRAL/index.faiss" ]; then
        print_success "Mistral FAISS index found"
        ls -lh $FAISS_MISTRAL/
    else
        print_warning "Mistral FAISS index NOT found (optional)"
    fi
}

# 7. Check environment
check_environment() {
    print_header "Environment Check"
    
    print_section "Environment File"
    if [ -f "/home/contextapi/rag-ai-cli/.env.prod" ]; then
        print_success "Environment file exists"
        echo "Configuration:"
        grep -v "GOOGLE_API_KEY" /home/contextapi/rag-ai-cli/.env.prod || echo "Source: /home/contextapi/rag-ai-cli/.env.prod"
    else
        print_error "Environment file NOT found"
    fi
    
    print_section "Python Environment"
    if [ -d "/home/contextapi/rag-ai-cli/venv" ]; then
        print_success "Virtual environment exists"
        /home/contextapi/rag-ai-cli/venv/bin/python --version
    else
        print_error "Virtual environment NOT found"
    fi
}

# 8. Check resources
check_resources() {
    print_header "System Resources"
    
    print_section "Memory Usage"
    free -h
    
    print_section "Disk Usage"
    df -h /home
    
    print_section "CPU Info"
    nproc
    
    print_section "Gunicorn Memory"
    ps aux | grep gunicorn | grep -v grep | awk '{sum+=$6} END {print "Total: " sum " KB"}'
}

# 9. Check permissions
check_permissions() {
    print_header "Permission Check"
    
    print_section "App Directory Ownership"
    ls -ld /home/contextapi/rag-ai-cli
    ls -ld /home/contextapi/rag-ai-cli/faiss_db
    
    print_section "Log Directory Ownership"
    ls -ld /var/log/contextapi
    
    print_section "Config Files"
    ls -l /etc/systemd/system/contextapi.service
}

# 10. Restart service
restart_service() {
    print_header "Restarting Service"
    
    print_section "Stopping service..."
    sudo systemctl stop contextapi.service
    sleep 2
    
    print_section "Starting service..."
    sudo systemctl start contextapi.service
    sleep 3
    
    if systemctl is-active --quiet contextapi.service; then
        print_success "Service restarted successfully"
    else
        print_error "Failed to restart service"
        sudo journalctl -u contextapi.service -n 10
    fi
}

# 11. Check Google API Key
check_api_key() {
    print_header "Google API Key Check"
    
    if source /home/contextapi/rag-ai-cli/.env.prod 2>/dev/null && [ -n "$GOOGLE_API_KEY" ]; then
        print_success "Google API Key is set"
        KEY_PREVIEW="${GOOGLE_API_KEY:0:10}...${GOOGLE_API_KEY: -10}"
        echo "Key preview: $KEY_PREVIEW"
    else
        print_error "Google API Key is NOT set"
    fi
}

# 12. Full diagnostic report
run_full_diagnostic() {
    print_header "Full Diagnostic Report"
    
    check_service_status
    check_process
    check_ports
    check_environment
    check_api_key
    check_faiss
    check_permissions
    check_resources
    check_logs
    test_api
}

# Main menu
show_menu() {
    echo ""
    echo "Context API Troubleshooting Tool"
    echo ""
    echo "Select an option:"
    echo "1) Service Status"
    echo "2) Process Check"
    echo "3) Port Check"
    echo "4) View Logs"
    echo "5) Test API"
    echo "6) FAISS Check"
    echo "7) Environment Check"
    echo "8) Resources Check"
    echo "9) Permissions Check"
    echo "10) Restart Service"
    echo "11) API Key Check"
    echo "12) Full Diagnostic"
    echo "0) Exit"
    echo ""
}

# Main
main() {
    if [ "$#" -eq 0 ]; then
        while true; do
            show_menu
            read -p "Enter option (0-12): " choice
            
            case $choice in
                1) check_service_status ;;
                2) check_process ;;
                3) check_ports ;;
                4) check_logs ;;
                5) test_api ;;
                6) check_faiss ;;
                7) check_environment ;;
                8) check_resources ;;
                9) check_permissions ;;
                10) restart_service ;;
                11) check_api_key ;;
                12) run_full_diagnostic ;;
                0) echo "Goodbye!"; exit 0 ;;
                *) print_error "Invalid option" ;;
            esac
            
            read -p "Press Enter to continue..."
        done
    else
        case $1 in
            status) check_service_status ;;
            process) check_process ;;
            ports) check_ports ;;
            logs) check_logs ;;
            test) test_api ;;
            faiss) check_faiss ;;
            env) check_environment ;;
            resources) check_resources ;;
            permissions) check_permissions ;;
            restart) restart_service ;;
            key) check_api_key ;;
            full) run_full_diagnostic ;;
            *)
                echo "Usage: $0 [command]"
                echo "Commands: status, process, ports, logs, test, faiss, env, resources, permissions, restart, key, full"
                ;;
        esac
    fi
}

# Run with elevated privileges if needed
if [ "$EUID" -ne 0 ]; then 
    echo "This script needs sudo access for some checks..."
    sudo bash "$0" "$@"
else
    main "$@"
fi
