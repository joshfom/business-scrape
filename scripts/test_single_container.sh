#!/bin/bash

# Single Container Deployment Test Script
# This script tests the single container deployment locally before pushing to Coolify

set -e

echo "🔧 Testing Single Container Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_status "Docker is running"

# Build the single container image
echo "🏗️  Building single container image..."
if docker build -f Dockerfile.single -t business-scraper-single .; then
    print_status "Image built successfully"
else
    print_error "Failed to build image"
    exit 1
fi

# Stop any existing container
echo "🛑 Stopping any existing container..."
docker stop business-scraper-test 2>/dev/null || true
docker rm business-scraper-test 2>/dev/null || true

# Run the container
echo "🚀 Starting container..."
docker run -d \
    --name business-scraper-test \
    -p 8080:80 \
    -e MONGODB_URI="mongodb://root:77T87Tjn62LDdS5Bq9bY52FGxDBdXfEmJS1cj69elnhQBsRj7BsAnr3SKQF77oot@fo8g4g0w8gcc8k44s8s4gsks:27017/?directConnection=true" \
    -e PYTHONUNBUFFERED=1 \
    business-scraper-single

print_status "Container started on port 8080"

# Wait for container to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Test endpoints
echo "🧪 Testing endpoints..."

# Test frontend
echo "Testing frontend..."
if curl -f http://localhost:8080/ > /dev/null 2>&1; then
    print_status "Frontend is accessible"
else
    print_error "Frontend is not accessible"
fi

# Test API health
echo "Testing API health..."
if curl -f http://localhost:8080/api/health > /dev/null 2>&1; then
    print_status "API health endpoint is working"
else
    print_error "API health endpoint is not working"
fi

# Test API docs
echo "Testing API docs..."
if curl -f http://localhost:8080/api/docs > /dev/null 2>&1; then
    print_status "API docs are accessible"
else
    print_warning "API docs may not be accessible (this might be expected)"
fi

# Show container logs
echo "📋 Recent container logs:"
docker logs --tail 20 business-scraper-test

# Show container status
echo "📊 Container status:"
docker ps --filter name=business-scraper-test

echo ""
print_status "Test complete! Container is running on http://localhost:8080"
echo "To stop the test container, run: docker stop business-scraper-test && docker rm business-scraper-test"
echo ""
echo "If all tests pass, you can proceed with Coolify deployment using:"
echo "  - Build Pack: Dockerfile"
echo "  - Dockerfile: Dockerfile.single"
echo "  - Port: 80"
