#!/bin/bash

# VPS Direct Deployment Script
# This script deploys the Business Scraper to a VPS using Docker directly

set -e

echo "🚀 Business Scraper VPS Deployment"
echo "=================================="

# Colors for output
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
APP_NAME="business-scraper"
PORT=80
DOMAIN=${1:-"your-domain.com"}
MONGODB_URI=${2:-"mongodb://root:77T87Tjn62LDdS5Bq9bY52FGxDBdXfEmJS1cj69elnhQBsRj7BsAnr3SKQF77oot@fo8g4g0w8gcc8k44s8s4gsks:27017/?directConnection=true"}

echo "📋 Configuration:"
echo "   App Name: $APP_NAME"
echo "   Port: $PORT"
echo "   Domain: $DOMAIN"
echo "   MongoDB: [configured]"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    print_status "Docker installed. Please log out and back in, then run this script again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

print_status "Docker is available"

# Clone or update repository
if [ -d "/opt/$APP_NAME" ]; then
    print_status "Updating existing repository..."
    cd /opt/$APP_NAME
    sudo git pull
else
    print_status "Cloning repository..."
    sudo git clone https://github.com/joshfom/business-scrape.git /opt/$APP_NAME
    cd /opt/$APP_NAME
fi

# Stop existing container
print_status "Stopping existing container..."
sudo docker stop $APP_NAME 2>/dev/null || true
sudo docker rm $APP_NAME 2>/dev/null || true

# Build the image
print_status "Building Docker image..."
sudo docker build -f Dockerfile.single -t $APP_NAME:latest .

# Run the container
print_status "Starting container..."
sudo docker run -d \
    --name $APP_NAME \
    --restart unless-stopped \
    -p $PORT:80 \
    -e MONGODB_URI="$MONGODB_URI" \
    -e PYTHONUNBUFFERED=1 \
    $APP_NAME:latest

# Wait for container to start
print_status "Waiting for container to start..."
sleep 30

# Test the deployment
echo "🧪 Testing deployment..."

# Test frontend
if curl -f http://localhost:$PORT/ > /dev/null 2>&1; then
    print_status "Frontend is accessible"
else
    print_error "Frontend is not accessible"
    print_warning "Checking container logs..."
    sudo docker logs --tail 20 $APP_NAME
fi

# Test API
if curl -f http://localhost:$PORT/api/health > /dev/null 2>&1; then
    print_status "API is accessible"
else
    print_error "API is not accessible"
fi

# Show container status
echo "📊 Container status:"
sudo docker ps --filter name=$APP_NAME

echo ""
print_status "Deployment complete!"
echo "🌐 Access your application at: http://$DOMAIN:$PORT"
echo "📋 API docs available at: http://$DOMAIN:$PORT/api/docs"
echo ""
echo "📖 Management commands:"
echo "   View logs: sudo docker logs $APP_NAME"
echo "   Stop app: sudo docker stop $APP_NAME"
echo "   Start app: sudo docker start $APP_NAME"
echo "   Update app: sudo docker pull $APP_NAME:latest && sudo docker restart $APP_NAME"
echo ""

# Set up nginx reverse proxy (optional)
read -p "Do you want to set up nginx reverse proxy for port 80? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Setting up nginx reverse proxy..."
    
    # Install nginx
    sudo apt update
    sudo apt install -y nginx
    
    # Create nginx config
    sudo tee /etc/nginx/sites-available/$APP_NAME > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://localhost:$PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF
    
    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl reload nginx
    
    print_status "Nginx reverse proxy configured"
    echo "🌐 Your app is now available at: http://$DOMAIN"
fi

print_status "VPS deployment completed successfully!"
