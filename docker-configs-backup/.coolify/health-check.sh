#!/bin/bash
# Coolify health check script for Business Scraper

# Exit codes:
# 0 = healthy
# 1 = unhealthy

# Check Backend API health
echo "🔍 Checking Backend API..."
if ! curl -f -s "http://localhost:8000/health" > /dev/null; then
    echo "❌ Backend API health check failed"
    exit 1
fi

# Check Frontend
echo "🔍 Checking Frontend..."
if ! curl -f -s "http://localhost:80" > /dev/null; then
    echo "❌ Frontend health check failed"
    exit 1
fi

# Check MongoDB connection
echo "🔍 Checking MongoDB..."
if ! docker-compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" business_scraper --quiet > /dev/null 2>&1; then
    echo "❌ MongoDB health check failed"
    exit 1
fi

# Optional: Check if there are any recent errors in logs
echo "🔍 Checking for recent errors..."
error_count=$(find ./logs -name "*.log" -mtime -1 -exec grep -l "ERROR\|CRITICAL" {} \; 2>/dev/null | wc -l)
if [ "$error_count" -gt 5 ]; then
    echo "⚠️ Warning: Found recent errors in logs (count: $error_count)"
    # Don't fail the health check for this, just warn
fi

# Optional: Check disk space
echo "🔍 Checking disk space..."
disk_usage=$(df . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$disk_usage" -gt 90 ]; then
    echo "⚠️ Warning: Disk usage is high ($disk_usage%)"
    # Don't fail the health check for this, just warn
fi

echo "✅ All health checks passed"
exit 0
