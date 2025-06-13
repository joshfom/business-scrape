#!/bin/bash
# Automated deployment script for Debian 12 VPS
# Server: 152.53.168.44 (v2202506281396351341.luckysrv.de)

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_section() {
    echo -e "\n${GREEN}==== $1 ====${NC}\n"
}

print_step() {
    echo -e "${YELLOW}>> $1${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (you should be root on first login)"
    exit 1
fi

SERVER_IP="152.53.168.44"
APP_USER="scraper_user"

print_section "Business Scraper Deployment for Debian 12"
print_step "Server IP: $SERVER_IP"

# 1. Update system
print_section "Updating System"
apt update && apt upgrade -y

# 2. Create non-root user
print_section "Creating Application User"
if ! id "$APP_USER" &>/dev/null; then
    adduser --disabled-password --gecos "" $APP_USER
    usermod -aG sudo $APP_USER
    print_step "User $APP_USER created"
else
    print_step "User $APP_USER already exists"
fi

# 3. Install basic dependencies
print_section "Installing System Dependencies"
apt install -y git python3 python3-pip python3-dev python3-venv \
    build-essential curl gnupg nginx supervisor wget \
    software-properties-common apt-transport-https ca-certificates \
    lsb-release

# 4. Install MongoDB for Debian 12
print_section "Installing MongoDB"
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
    gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | \
    tee /etc/apt/sources.list.d/mongodb-org-7.0.list

apt update
apt install -y mongodb-org

# Start and enable MongoDB
systemctl start mongod
systemctl enable mongod
print_step "MongoDB installed and started"

# 5. Install Node.js 20.x
print_section "Installing Node.js"
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# 6. Install PM2 and serve globally
print_section "Installing PM2"
npm install -g pm2 serve

# 7. Set up application directory
print_section "Setting Up Application Directory"
APP_DIR="/home/$APP_USER/business-scrape"
mkdir -p $APP_DIR
chown $APP_USER:$APP_USER $APP_DIR

# 8. Switch to app user for application setup
print_section "Setting Up Application (as $APP_USER)"
sudo -u $APP_USER bash << EOF
cd /home/$APP_USER

# Note: You'll need to upload your application files here
# For now, we'll create the directory structure
mkdir -p business-scrape/{backend,frontend,scripts}

# Create a placeholder for the application files
cat > business-scrape/README_DEPLOY.md << 'INNER_EOF'
# Application Deployment

Your application directory is ready at: /home/$APP_USER/business-scrape

## Next Steps:

1. Upload your application files to this directory using scp:
   From your local machine, run:
   \`\`\`bash
   scp -r /Users/joshua/Code/business-scrape/* $APP_USER@$SERVER_IP:~/business-scrape/
   \`\`\`

2. Or clone from your git repository:
   \`\`\`bash
   cd ~/business-scrape
   git clone https://github.com/yourusername/business-scrape.git .
   \`\`\`

3. Then run the application setup:
   \`\`\`bash
   ./finish_deployment.sh
   \`\`\`
INNER_EOF
EOF

# 9. Create finish deployment script
print_section "Creating Finish Deployment Script"
cat > /home/$APP_USER/finish_deployment.sh << 'EOF'
#!/bin/bash
# Finish deployment script - run this after uploading your application files

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Finishing Business Scraper Deployment${NC}"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found. Please ensure you're in the application directory with all files uploaded.${NC}"
    exit 1
fi

# Set up Python virtual environment
echo -e "${YELLOW}Setting up Python environment...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Build frontend
echo -e "${YELLOW}Building frontend...${NC}"
cd frontend
npm install
REACT_APP_API_URL=http://152.53.168.44/api npm run build
cd ..

# Create PM2 ecosystem file
echo -e "${YELLOW}Creating PM2 configuration...${NC}"
cat > ecosystem.config.js << 'INNER_EOF'
module.exports = {
  apps: [
    {
      name: 'business-scraper-backend',
      cwd: './backend',
      script: '../venv/bin/python3',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 8000',
      env: {
        PYTHONUNBUFFERED: 1
      },
      watch: false,
      autorestart: true,
      max_memory_restart: '1G',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
    {
      name: 'business-scraper-frontend',
      cwd: './frontend',
      script: 'serve',
      args: '-s build -l 3020',
      env: {
        PM2_SERVE_PATH: './build',
        PM2_SERVE_PORT: 3020
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    }
  ]
};
INNER_EOF

# Start application
echo -e "${YELLOW}Starting application with PM2...${NC}"
pm2 start ecosystem.config.js
pm2 save
pm2 startup

echo -e "${GREEN}Application setup complete!${NC}"
echo -e "Your application should be accessible at: http://152.53.168.44"
echo -e "Check status with: pm2 status"
echo -e "View logs with: pm2 logs"
EOF

chown $APP_USER:$APP_USER /home/$APP_USER/finish_deployment.sh
chmod +x /home/$APP_USER/finish_deployment.sh

# 10. Configure NGINX
print_section "Configuring NGINX"
cat > /etc/nginx/sites-available/business-scraper << EOF
server {
    listen 80;
    server_name $SERVER_IP v2202506281396351341.luckysrv.de;

    # Frontend
    location / {
        proxy_pass http://localhost:3020;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site and remove default
ln -sf /etc/nginx/sites-available/business-scraper /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test NGINX configuration
if nginx -t; then
    systemctl restart nginx
    print_step "NGINX configured and restarted"
else
    print_error "NGINX configuration test failed"
    exit 1
fi

# 11. Configure firewall
print_section "Configuring Firewall"
apt install -y ufw
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# 12. Create backup script
print_section "Setting Up Database Backup"
cat > /home/$APP_USER/backup_mongodb.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/scraper_user/mongodb_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p $BACKUP_DIR
mongodump --db business_scraper --out $BACKUP_DIR/backup_$TIMESTAMP
find $BACKUP_DIR -type d -name "backup_*" -mtime +7 -exec rm -rf {} \;
EOF

chown $APP_USER:$APP_USER /home/$APP_USER/backup_mongodb.sh
chmod +x /home/$APP_USER/backup_mongodb.sh

# Add to crontab for scraper_user
sudo -u $APP_USER bash << 'EOF'
(crontab -l 2>/dev/null; echo "0 3 * * * /home/scraper_user/backup_mongodb.sh") | crontab -
EOF

print_section "Initial Deployment Complete!"
echo -e "${GREEN}Your VPS is now ready for the Business Scraper application.${NC}"
echo -e ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. Upload your application files:"
echo -e "   ${GREEN}scp -r /Users/joshua/Code/business-scrape/* $APP_USER@$SERVER_IP:~/business-scrape/${NC}"
echo -e ""
echo -e "2. SSH into the server as $APP_USER:"
echo -e "   ${GREEN}ssh $APP_USER@$SERVER_IP${NC}"
echo -e ""
echo -e "3. Run the finish deployment script:"
echo -e "   ${GREEN}cd ~/business-scrape && ./finish_deployment.sh${NC}"
echo -e ""
echo -e "4. Your application will be accessible at:"
echo -e "   ${GREEN}http://$SERVER_IP${NC}"
echo -e ""
echo -e "${YELLOW}Security Note:${NC} Remember to change the root password and set up SSH keys!"
EOF

chmod +x /Users/joshua/Code/business-scrape/scripts/debian_deploy.sh
