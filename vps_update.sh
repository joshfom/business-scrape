#!/bin/bash

# Business Scraper VPS Update Script
# This script:
# 1. Pulls latest code from GitHub
# 2. Rebuilds containers with MongoDB external access
# 3. Provides job restart capabilities

set -e

echo "🚀 Business Scraper VPS Update Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Are you in the business-scrape directory?"
    exit 1
fi

# Update code from GitHub
print_status "Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/main
print_success "Code updated successfully"

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down
print_success "Containers stopped"

# Remove old images to force rebuild
print_status "Removing old images..."
docker-compose build --no-cache
print_success "Images rebuilt"

# Start containers with new configuration
print_status "Starting containers with MongoDB external access..."
docker-compose up -d
print_success "Containers started"

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Check container status
print_status "Checking container status..."
docker-compose ps

# Check if MongoDB is accessible externally
print_status "Testing MongoDB external access..."
if docker exec business-scraper-mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    print_success "MongoDB is running and accessible"
    echo ""
    echo "📊 MongoDB Connection Details for TablePlus:"
    echo "----------------------------------------"
    echo "Host: 152.53.168.44"
    echo "Port: 27017"
    echo "Username: admin"
    echo "Password: business123"
    echo "Database: business_scraper"
    echo "Auth Database: admin"
    echo ""
else
    print_warning "MongoDB might not be fully ready yet"
fi

# Check if backend is accessible
print_status "Testing backend API..."
if curl -f http://localhost:8000/api/public/stats > /dev/null 2>&1; then
    print_success "Backend API is running"
else
    print_warning "Backend API might not be ready yet"
fi

# Show job restart instructions
echo ""
echo "🔄 Job Restart Instructions:"
echo "============================"
echo ""
echo "To manage scraping jobs, use the restart_jobs.py script:"
echo ""
echo "1. List all jobs:"
echo "   python3 restart_jobs.py list"
echo ""
echo "2. List jobs with zero extraction:"
echo "   python3 restart_jobs.py list-zero"
echo ""
echo "3. Restart all jobs with zero extraction:"
echo "   python3 restart_jobs.py restart-zero"
echo ""
echo "4. Restart a specific job (use partial ID):"
echo "   python3 restart_jobs.py restart --job-id 507f1f77bcf"
echo ""
echo "5. Show database statistics:"
echo "   python3 restart_jobs.py stats"
echo ""

# Install Python dependencies for the restart script
print_status "Installing Python dependencies for job management..."
pip3 install motor pymongo > /dev/null 2>&1 || print_warning "Could not install Python dependencies"

print_success "VPS update completed successfully!"
echo ""
echo "🌐 Services are now running:"
echo "  - Frontend: http://152.53.168.44"
echo "  - Backend API: http://152.53.168.44/api"
echo "  - MongoDB: 152.53.168.44:27017"
echo ""
echo "🔐 Frontend Login:"
echo "  Username: intobusiness"
echo "  Password: Goodluck@2025"
