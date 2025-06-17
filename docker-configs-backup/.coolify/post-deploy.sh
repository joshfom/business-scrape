#!/bin/bash
# Coolify post-deployment script for Business Scraper

set -e

echo "🎯 Starting Business Scraper post-deployment..."

# Wait for services to be fully ready
echo "⏳ Waiting for services to be ready..."

# Function to check if a service is responding
check_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    echo "🔍 Checking $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is ready"
            return 0
        fi
        
        echo "⏳ Attempt $attempt/$max_attempts: $service_name not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to become ready after $max_attempts attempts"
    return 1
}

# Check MongoDB
echo "🗄️ Checking MongoDB connection..."
if docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" business_scraper --quiet > /dev/null 2>&1; then
    echo "✅ MongoDB is ready"
else
    echo "❌ MongoDB is not responding"
    exit 1
fi

# Check Backend API
check_service "Backend API" "http://localhost:8000/health"

# Check Frontend
check_service "Frontend" "http://localhost:80"

# Run any database migrations or setup
echo "🗄️ Initializing database..."
docker-compose exec -T mongodb mongosh business_scraper --eval "
    // Ensure indexes exist
    db.businesses.createIndex({ 'page_url': 1 }, { unique: true, background: true });
    db.businesses.createIndex({ 'name': 1 }, { background: true });
    db.businesses.createIndex({ 'city': 1 }, { background: true });
    db.scraping_jobs.createIndex({ 'status': 1 }, { background: true });
    db.scraping_jobs.createIndex({ 'created_at': 1 }, { background: true });
    print('✅ Database indexes created/updated');
" > /dev/null 2>&1 || echo "⚠️ Database initialization had some issues, but continuing..."

# Set up log rotation (if logrotate is available)
if command -v logrotate > /dev/null 2>&1; then
    echo "📋 Setting up log rotation..."
    sudo tee /etc/logrotate.d/business-scraper > /dev/null << EOF
$(pwd)/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
    echo "✅ Log rotation configured"
else
    echo "⚠️ logrotate not available, skipping log rotation setup"
fi

# Display deployment summary
echo ""
echo "🎉 Post-deployment completed successfully!"
echo ""
echo "📊 Deployment Summary:"
echo "====================="
echo "🌐 Application: Business Scraper"
echo "📅 Deployed: $(date)"
echo "🏗️ Build: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
echo ""
echo "🔗 Service Status:"
echo "  ✅ MongoDB: Running"
echo "  ✅ Backend API: Running on port 8000"
echo "  ✅ Frontend: Running on port 80"
echo ""
echo "📁 Data Locations:"
echo "  🗄️ Database: Docker volume 'mongodb_data'"
echo "  📋 Logs: $(pwd)/logs/"
echo "  💾 Backups: $(pwd)/backups/"
echo ""
echo "🎯 Your application is now fully deployed and ready to use!"
