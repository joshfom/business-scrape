#!/bin/bash

# Manual VPS Installation Script
# Installs and runs the Business Scraper without Docker

set -e

echo "🏗️  Manual VPS Installation for Business Scraper"
echo "==============================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Configuration
APP_DIR="/opt/business-scraper"
USER="businessscraper"
MONGODB_URI=${1:-"mongodb://root:77T87Tjn62LDdS5Bq9bY52FGxDBdXfEmJS1cj69elnhQBsRj7BsAnr3SKQF77oot@fo8g4g0w8gcc8k44s8s4gsks:27017/?directConnection=true"}

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
print_status "Installing required packages..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    nginx \
    supervisor \
    git \
    curl \
    build-essential

# Create application user
print_status "Creating application user..."
sudo useradd -m -s /bin/bash $USER 2>/dev/null || true

# Clone repository
print_status "Setting up application directory..."
sudo rm -rf $APP_DIR
sudo git clone https://github.com/joshfom/business-scrape.git $APP_DIR
sudo chown -R $USER:$USER $APP_DIR

# Setup Python environment
print_status "Setting up Python environment..."
cd $APP_DIR
sudo -u $USER python3 -m venv venv
sudo -u $USER ./venv/bin/pip install --upgrade pip
sudo -u $USER ./venv/bin/pip install -r requirements.txt

# Build frontend
print_status "Building frontend..."
cd $APP_DIR/frontend
sudo -u $USER npm install
sudo -u $USER REACT_APP_API_URL=/api npm run build

# Setup nginx
print_status "Configuring nginx..."
sudo tee /etc/nginx/sites-available/business-scraper > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    # Serve React app
    location / {
        root $APP_DIR/frontend/build;
        index index.html;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # Proxy API requests to backend
    location /api {
        proxy_pass http://localhost:8000/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/business-scraper /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# Setup supervisor
print_status "Configuring supervisor..."
sudo tee /etc/supervisor/conf.d/business-scraper.conf > /dev/null <<EOF
[program:business-scraper-backend]
command=$APP_DIR/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
directory=$APP_DIR/backend
user=$USER
autostart=true
autorestart=true
startretries=3
environment=MONGODB_URI="$MONGODB_URI",PYTHONUNBUFFERED="1"
stderr_logfile=/var/log/supervisor/business-scraper-backend_err.log
stdout_logfile=/var/log/supervisor/business-scraper-backend_out.log
EOF

# Start services
print_status "Starting services..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start business-scraper-backend
sudo systemctl enable nginx supervisor
sudo systemctl start nginx supervisor

# Wait for services to start
sleep 10

# Test deployment
print_status "Testing deployment..."

# Test frontend
if curl -f http://localhost/ > /dev/null 2>&1; then
    print_status "Frontend is accessible"
else
    print_error "Frontend is not accessible"
fi

# Test API
if curl -f http://localhost/api/health > /dev/null 2>&1; then
    print_status "API is accessible"
else
    print_error "API is not accessible"
    print_warning "Checking backend logs..."
    sudo supervisorctl tail business-scraper-backend
fi

# Show status
echo "📊 Service status:"
sudo supervisorctl status
sudo systemctl status nginx --no-pager -l

echo ""
print_status "Manual installation complete!"
echo "🌐 Your application is available at: http://your-server-ip/"
echo "📋 API docs available at: http://your-server-ip/api/docs"
echo ""
echo "📖 Management commands:"
echo "   View backend logs: sudo supervisorctl tail business-scraper-backend"
echo "   Restart backend: sudo supervisorctl restart business-scraper-backend"
echo "   Restart nginx: sudo systemctl restart nginx"
echo "   View all services: sudo supervisorctl status"
