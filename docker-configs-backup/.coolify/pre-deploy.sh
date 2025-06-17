#!/bin/bash
# Coolify pre-deployment script for Business Scraper

set -e

echo "🚀 Starting Business Scraper pre-deployment..."

# Create required directories
echo "📁 Creating required directories..."
mkdir -p logs backups

# Set proper permissions
echo "🔐 Setting permissions..."
chmod -R 755 logs backups

# Verify required files exist
echo "✅ Verifying required files..."
required_files=(
    "docker-compose.yml"
    "Dockerfile.backend"
    "Dockerfile.frontend"
    "nginx.conf"
    "backend/requirements.txt"
    "frontend/package.json"
)

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done

echo "✅ All required files present"

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Business Scraper Environment Configuration
MONGODB_URI=mongodb://mongodb:27017/business_scraper
PYTHONUNBUFFERED=1
NODE_ENV=production
REACT_APP_API_URL=/api
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Validate environment variables
echo "🔍 Validating environment configuration..."
source .env

if [[ -z "$MONGODB_URI" ]]; then
    echo "❌ MONGODB_URI not set"
    exit 1
fi

echo "✅ Environment configuration valid"

# Clean up any previous builds (optional)
echo "🧹 Cleaning up previous builds..."
docker system prune -f --volumes=false 2>/dev/null || true

echo "🎉 Pre-deployment completed successfully!"
echo "📊 Ready for Docker build and deployment..."
