#!/bin/bash

# VPS Git-based deployment script
echo "🚀 Deploying Business Scraper from Git to VPS..."

VPS_IP="152.53.168.44"
VPS_USER="root"
APP_DIR="/opt/business-scrape"
REPO_URL="https://github.com/joshfom/business-scrape.git"

# SSH into VPS and deploy
ssh $VPS_USER@$VPS_IP << ENDSSH
# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Install git if not present
if ! command -v git &> /dev/null; then
    echo "Installing Git..."
    apt update && apt install -y git
fi

# Clone or update repository
if [ -d "$APP_DIR" ]; then
    echo "Updating existing repository..."
    cd $APP_DIR
    git pull
else
    echo "Cloning repository..."
    git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Remove old volumes for fresh start
echo "Cleaning up old data..."
docker volume rm business-scrape_mongodb_data 2>/dev/null || true

# Build and start containers
echo "Building and starting containers..."
docker-compose up -d --build

# Wait for containers to be healthy
echo "Waiting for containers to start (60 seconds)..."
sleep 60

# Test the deployment
echo "Testing deployment..."
echo "API Test:"
curl -u intobusiness:Goodluck@2025 http://localhost/api/public/stats

echo ""
echo "Container Status:"
docker-compose ps

# Setup firewall
echo "Configuring firewall..."
ufw allow 80/tcp 2>/dev/null || echo "UFW not available or already configured"

echo ""
echo "🎉 Deployment completed!"
echo "🌐 Access: http://152.53.168.44"
echo "🔐 Username: intobusiness"
echo "🔐 Password: Goodluck@2025"

ENDSSH

echo ""
echo "✅ VPS deployment script completed!"
echo "🌐 Try accessing: http://152.53.168.44"
echo "🔐 Credentials: intobusiness / Goodluck@2025"
