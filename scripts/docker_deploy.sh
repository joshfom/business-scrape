#!/bin/bash
# One-click Docker deployment script for Business Scraper
# Run this script on your VPS to deploy everything automatically

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}================================================${NC}"
    echo -e "${BLUE} $1 ${NC}"
    echo -e "${BLUE}================================================${NC}\n"
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please don't run this script as root. Run as a regular user with sudo privileges."
    exit 1
fi

print_header "Business Scraper Docker Deployment"

# Get server info
SERVER_IP=$(hostname -I | awk '{print $1}' || curl -s ifconfig.me)
print_step "Detected server IP: $SERVER_IP"

# 1. Install Docker if not present
print_header "Installing Docker & Docker Compose"

if command -v docker &> /dev/null; then
    print_success "Docker is already installed"
else
    print_step "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    print_success "Docker installed"
fi

if command -v docker-compose &> /dev/null; then
    print_success "Docker Compose is already installed"
else
    print_step "Installing Docker Compose..."
    sudo apt update
    sudo apt install -y docker-compose
    print_success "Docker Compose installed"
fi

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# 2. Prepare application directory
print_header "Preparing Application"

APP_DIR="$HOME/business-scrape"
if [ ! -d "$APP_DIR" ]; then
    print_error "Application directory not found at $APP_DIR"
    print_step "Please upload your application files first:"
    echo -e "  ${GREEN}scp -r /Users/joshua/Code/business-scrape $USER@$SERVER_IP:~/${NC}"
    echo -e "  ${GREEN}Then run this script again${NC}"
    exit 1
fi

cd "$APP_DIR"
print_success "Application directory found"

# 3. Create required directories
print_step "Creating required directories..."
mkdir -p logs backups
sudo chown -R $USER:$USER logs backups

# 4. Set up environment variables
print_step "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.docker .env
    print_success "Environment file created"
else
    print_success "Environment file already exists"
fi

# 5. Configure firewall
print_header "Configuring Firewall"
if command -v ufw &> /dev/null; then
    print_step "Configuring UFW firewall..."
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow OpenSSH
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
    print_success "Firewall configured"
else
    print_step "Installing and configuring UFW firewall..."
    sudo apt update
    sudo apt install -y ufw
    sudo ufw --force reset
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow OpenSSH
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
    print_success "Firewall installed and configured"
fi

# 6. Build and start the application
print_header "Building and Starting Application"

print_step "Building Docker images (this may take a few minutes)..."
docker-compose down 2>/dev/null || true
docker-compose build --no-cache

print_step "Starting all services..."
docker-compose up -d

# 7. Wait for services to be healthy
print_header "Waiting for Services to Start"

print_step "Waiting for MongoDB to be ready..."
timeout=60
while [ $timeout -gt 0 ]; do
    if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" business_scraper &>/dev/null; then
        break
    fi
    sleep 2
    timeout=$((timeout-2))
done

if [ $timeout -le 0 ]; then
    print_error "MongoDB failed to start within 60 seconds"
else
    print_success "MongoDB is ready"
fi

print_step "Waiting for backend to be ready..."
timeout=60
while [ $timeout -gt 0 ]; do
    if curl -s http://localhost:8000/health &>/dev/null; then
        break
    fi
    sleep 2
    timeout=$((timeout-2))
done

if [ $timeout -le 0 ]; then
    print_error "Backend failed to start within 60 seconds"
else
    print_success "Backend is ready"
fi

print_step "Waiting for frontend to be ready..."
timeout=30
while [ $timeout -gt 0 ]; do
    if curl -s http://localhost/ &>/dev/null; then
        break
    fi
    sleep 2
    timeout=$((timeout-2))
done

if [ $timeout -le 0 ]; then
    print_error "Frontend failed to start within 30 seconds"
else
    print_success "Frontend is ready"
fi

# 8. Set up automated backup
print_header "Setting up Automated Backup"
print_step "Adding backup cron job..."

# Create backup cron script
cat > backup_cron.sh << 'EOF'
#!/bin/bash
cd /home/scraper_user/business-scrape
/usr/bin/docker-compose run --rm backup
EOF

chmod +x backup_cron.sh

# Add to crontab if not already there
CRON_JOB="0 3 * * * $HOME/business-scrape/backup_cron.sh"
(crontab -l 2>/dev/null | grep -Fq "$CRON_JOB") || (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

print_success "Daily backup scheduled for 3:00 AM"

# 9. Final status check
print_header "Deployment Status"

echo -e "${YELLOW}Checking service status...${NC}"
docker-compose ps

print_header "🎉 Deployment Complete!"

echo -e "${GREEN}Your Business Scraper application is now running!${NC}\n"

echo -e "${YELLOW}Access URLs:${NC}"
echo -e "  🌐 Frontend:     ${GREEN}http://$SERVER_IP${NC}"
echo -e "  🔧 Backend API:  ${GREEN}http://$SERVER_IP/api${NC}"
echo -e "  📚 API Docs:     ${GREEN}http://$SERVER_IP/api/docs${NC}"

echo -e "\n${YELLOW}Management Commands:${NC}"
echo -e "  📊 View logs:    ${GREEN}docker-compose logs -f${NC}"
echo -e "  🔄 Restart:      ${GREEN}docker-compose restart${NC}"
echo -e "  🛑 Stop:         ${GREEN}docker-compose down${NC}"
echo -e "  ▶️  Start:        ${GREEN}docker-compose up -d${NC}"
echo -e "  📈 Monitor:      ${GREEN}docker stats${NC}"

echo -e "\n${YELLOW}Data Locations:${NC}"
echo -e "  📁 App logs:     ${GREEN}$APP_DIR/logs/${NC}"
echo -e "  💾 Backups:      ${GREEN}$APP_DIR/backups/${NC}"
echo -e "  🗄️  Database:     ${GREEN}Docker volume 'mongodb_data'${NC}"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "  1. Visit ${GREEN}http://$SERVER_IP${NC} to access your application"
echo -e "  2. Create your first scraping job"
echo -e "  3. Monitor logs with: ${GREEN}docker-compose logs -f${NC}"

if groups $USER | grep -q docker; then
    echo -e "\n${GREEN}✅ You can run Docker commands without sudo${NC}"
else
    echo -e "\n${YELLOW}⚠️  You may need to log out and back in to run Docker without sudo${NC}"
fi

print_success "Deployment completed successfully!"
