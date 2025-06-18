#!/bin/bash

# VPS Deployment Script for Business Scraper
# This script copies the project to VPS and deploys it

set -e

VPS_IP="152.53.168.44"
VPS_USER="root"
PROJECT_DIR="/opt/business-scraper"

echo "🚀 Starting VPS deployment to $VPS_IP..."

# Check if we can connect to VPS
echo "📡 Testing VPS connection..."
if ! ssh -o ConnectTimeout=10 $VPS_USER@$VPS_IP "echo 'VPS connection successful'"; then
    echo "❌ Cannot connect to VPS. Please check your SSH access."
    exit 1
fi

# Create project directory on VPS
echo "📁 Creating project directory on VPS..."
ssh $VPS_USER@$VPS_IP "mkdir -p $PROJECT_DIR"

# Copy essential files to VPS
echo "📤 Copying project files to VPS..."
rsync -avz --exclude='.git' \
           --exclude='node_modules' \
           --exclude='__pycache__' \
           --exclude='.venv' \
           --exclude='logs' \
           --exclude='*.log' \
           ./ $VPS_USER@$VPS_IP:$PROJECT_DIR/

# Run deployment on VPS
echo "🐳 Deploying on VPS..."
ssh $VPS_USER@$VPS_IP << 'EOF'
cd /opt/business-scraper

echo "🔧 Installing Docker and Docker Compose if needed..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

echo "🛑 Stopping any existing containers..."
docker-compose down --remove-orphans || true

echo "🧹 Cleaning up old volumes..."
docker volume prune -f || true

echo "🔥 Building and starting containers..."
docker-compose up -d --build

echo "⏳ Waiting for containers to be healthy..."
sleep 30

echo "🔍 Checking container status..."
docker-compose ps

echo "🩺 Testing API health..."
if curl -f -u intobusiness:Goodluck@2025 http://localhost/api/public/stats; then
    echo "✅ API is working!"
else
    echo "❌ API test failed"
    docker-compose logs backend
fi

echo "🎉 Deployment complete!"
echo "🌐 Your application should be available at: http://152.53.168.44"
echo "🔐 Login credentials: intobusiness / Goodluck@2025"
EOF

echo "✅ VPS deployment completed!"
echo "🌐 Access your application at: http://152.53.168.44"
echo "🔐 Use credentials: intobusiness / Goodluck@2025"

# Copy files to VPS
print_status "Copying project files to VPS..."
rsync -avz --delete \
    --exclude 'node_modules' \
    --exclude '.git' \
    --exclude 'logs' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    ./ $VPS_USER@$VPS_IP:$APP_DIR/

# Run deployment on VPS
print_status "Running deployment on VPS..."
ssh $VPS_USER@$VPS_IP << 'ENDSSH'
cd /opt/business-scraper

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
    curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Remove old volumes for fresh start
echo "Removing old volumes..."
docker volume rm business-scrape_mongodb_data 2>/dev/null || true

# Build and start containers
echo "Starting containers..."
docker-compose up -d --build

# Wait for containers to be healthy
echo "Waiting for containers to start..."
sleep 30

# Test the deployment
echo "Testing deployment..."
if curl -f -u intobusiness:Goodluck@2025 http://localhost/api/public/stats > /dev/null 2>&1; then
    echo "✅ API is working!"
else
    echo "❌ API test failed"
    docker-compose logs backend
fi

# Show container status
echo "Container status:"
docker-compose ps

# Setup firewall for port 80
ufw allow 80/tcp 2>/dev/null || echo "UFW not available or already configured"

echo "🎉 Deployment completed!"
echo "🌐 Access your application at: http://152.53.168.44"
echo "🔐 Username: intobusiness, Password: Goodluck@2025"
ENDSSH

print_status "VPS deployment completed!"
print_status "Access your application at: http://152.53.168.44"
print_warning "Username: intobusiness, Password: Goodluck@2025"

# Test the deployed application
print_status "Testing deployed application..."
sleep 5
if curl -f -u intobusiness:Goodluck@2025 http://152.53.168.44/api/public/stats > /dev/null 2>&1; then
    print_status "VPS deployment successful! API is responding."
else
    print_warning "API test failed. The application might still be starting up."
    print_warning "Try accessing http://152.53.168.44 in a few minutes."
fi

echo ""
echo "📋 Management commands (run on VPS):"
echo "   ssh root@152.53.168.44"
echo "   cd /opt/business-scraper"
echo "   docker-compose ps          # View status"
echo "   docker-compose logs        # View logs"
echo "   docker-compose restart     # Restart all"
echo "   docker-compose down        # Stop all"
