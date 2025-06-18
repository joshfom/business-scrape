#!/bin/bash

# Complete VPS deployment script
echo "🚀 Deploying Business Scraper to VPS..."

VPS_IP="152.53.168.44"
VPS_USER="root"
APP_DIR="/opt/business-scraper"

# Step 1: Copy project files to VPS
echo "📁 Copying project files to VPS..."
rsync -avz --delete \
    --exclude 'node_modules' \
    --exclude '.git' \
    --exclude 'logs' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '*.log' \
    ./ $VPS_USER@$VPS_IP:$APP_DIR/

# Step 2: Deploy on VPS
echo "🔧 Running deployment on VPS..."
ssh $VPS_USER@$VPS_IP << ENDSSH
set -e

cd $APP_DIR

echo "Current directory: \$(pwd)"
echo "Files in directory:"
ls -la

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

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Remove old volumes for fresh start
echo "Cleaning up old volumes..."
docker volume prune -f

# Build and start containers
echo "Building and starting containers..."
docker-compose up -d --build

# Wait for containers to be healthy
echo "Waiting for containers to start..."
sleep 45

# Show container status
echo "Container status:"
docker-compose ps

# Setup firewall
echo "Setting up firewall..."
ufw allow 80/tcp 2>/dev/null || echo "UFW not available"

echo "🎉 Deployment completed!"
ENDSSH

# Step 3: Test the deployment
echo "🧪 Testing VPS deployment..."
sleep 10

echo "Testing API endpoint..."
if curl -s -u intobusiness:Goodluck@2025 "http://$VPS_IP/api/public/stats" | grep -q "total_businesses"; then
    echo "✅ API is working!"
else
    echo "⚠️  API test failed, but containers might still be starting..."
fi

echo ""
echo "🎉 VPS Deployment Complete!"
echo "🌐 Access your application at: http://$VPS_IP"
echo "🔐 Username: intobusiness"
echo "🔐 Password: Goodluck@2025"
echo ""
echo "📋 Management commands:"
echo "   ssh root@$VPS_IP"
echo "   cd /opt/business-scraper"
echo "   docker-compose ps"
echo "   docker-compose logs"
