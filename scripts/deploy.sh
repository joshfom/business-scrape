#!/bin/bash
# Deployment script for Business Scraper application
# This script automates the deployment process to a fresh Ubuntu server

# Exit on any error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print section header
print_section() {
    echo -e "\n${GREEN}==== $1 ====${NC}\n"
}

# Print step
print_step() {
    echo -e "${YELLOW}>> $1${NC}"
}

# Print error
print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script with sudo or as root"
    exit 1
fi

# Get application directory
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd $APP_DIR

print_section "Deploying Business Scraper Application"
print_step "Working directory: $APP_DIR"

# 1. Update system packages
print_section "Updating System Packages"
apt-get update
apt-get upgrade -y

# 2. Install required system dependencies
print_section "Installing System Dependencies"
apt-get install -y python3 python3-pip python3-dev python3-venv \
    build-essential curl gnupg nginx supervisor

# 3. Install MongoDB
print_section "Installing MongoDB"
curl -fsSL https://pgp.mongodb.com/server-6.0.asc | \
    gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | \
    tee /etc/apt/sources.list.d/mongodb-org-6.0.list
apt-get update
apt-get install -y mongodb-org

# Start MongoDB service
systemctl start mongod
systemctl enable mongod

print_step "Waiting for MongoDB to start..."
sleep 5

# 4. Install Node.js and npm (for frontend)
print_section "Installing Node.js"
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# 5. Install PM2
print_section "Installing PM2"
npm install -g pm2 serve

# 6. Create a virtual environment and install Python dependencies
print_section "Setting up Python Environment"
python3 -m venv $APP_DIR/venv
source $APP_DIR/venv/bin/activate
pip install -r $APP_DIR/requirements.txt

# 7. Build the frontend
print_section "Building Frontend"
cd $APP_DIR/frontend
npm install
npm run build

# 8. Setup PM2 configuration
print_section "Configuring PM2"
cat > $APP_DIR/ecosystem.config.js << EOL
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
EOL

# 9. Setup NGINX
print_section "Configuring NGINX"
SERVER_IP=$(hostname -I | awk '{print $1}')

cat > /etc/nginx/sites-available/business-scraper << EOL
server {
    listen 80;
    server_name ${SERVER_IP};

    # Frontend
    location / {
        proxy_pass http://localhost:3020;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOL

ln -sf /etc/nginx/sites-available/business-scraper /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test NGINX config
nginx -t

# Restart NGINX
systemctl restart nginx

# 10. Setup MongoDB backup script
print_section "Setting Up Database Backup"
cat > /home/$(logname)/backup_mongodb.sh << EOL
#!/bin/bash
BACKUP_DIR="/home/$(logname)/mongodb_backups"
TIMESTAMP=\$(date +"%Y%m%d_%H%M%S")
mkdir -p \$BACKUP_DIR
mongodump --db business_scraper --out \$BACKUP_DIR/backup_\$TIMESTAMP
find \$BACKUP_DIR -type d -name "backup_*" -mtime +7 -exec rm -rf {} \;
EOL

chmod +x /home/$(logname)/backup_mongodb.sh

# Add to crontab if not already there
CRON_JOB="0 3 * * * /home/$(logname)/backup_mongodb.sh"
(crontab -l 2>/dev/null | grep -Fq "$CRON_JOB") || (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

# 11. Start application with PM2
print_section "Starting Application with PM2"
cd $APP_DIR
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# 12. Configure firewall
print_section "Configuring Firewall"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

print_section "Deployment Complete!"
echo -e "Your Business Scraper application has been deployed successfully."
echo -e "You can access the application at: http://${SERVER_IP}"
echo -e "\nFor any issues, check the logs with: pm2 logs"
