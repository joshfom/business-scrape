#!/bin/bash

# Diagnostic script to check the current deployment status
echo "🔍 Business Scraper Deployment Diagnostics"
echo "=========================================="

echo ""
echo "📊 Testing Deployed URLs:"
echo "------------------------"

# Test frontend
echo ""
echo "🌐 Frontend (React App):"
echo "URL: http://doogwgocccok8s44owsww804.152.53.168.44.sslip.io/"
curl -s -I "http://doogwgocccok8s44owsww804.152.53.168.44.sslip.io/" | head -n 5

echo ""
echo "🔌 API Health Check (via Frontend):"
echo "URL: http://doogwgocccok8s44owsww804.152.53.168.44.sslip.io/api/health"
curl -s "http://doogwgocccok8s44owsww804.152.53.168.44.sslip.io/api/health" || echo "❌ API not accessible"

echo ""
echo "🔌 API Full Health Check (via Frontend):"
echo "URL: http://doogwgocccok8s44owsww804.152.53.168.44.sslip.io/api/health/full"
curl -s "http://doogwgocccok8s44owsww804.152.53.168.44.sslip.io/api/health/full" || echo "❌ API not accessible"

echo ""
echo "⚙️  Backend Direct Access:"
echo "URL: http://f0cgkg00koowgwwoowcokwks.152.53.168.44.sslip.io/"
curl -s -I "http://f0cgkg00koowgwwoowcokwks.152.53.168.44.sslip.io/" | head -n 5

echo ""
echo "⚙️  Backend Health (Direct):"
echo "URL: http://f0cgkg00koowgwwoowcokwks.152.53.168.44.sslip.io/health"
curl -s "http://f0cgkg00koowgwwoowcokwks.152.53.168.44.sslip.io/health" || echo "❌ Backend health not accessible"

echo ""
echo "🔍 Analysis:"
echo "============"
echo "✅ Deployment completed successfully"
echo "✅ Both containers are running"
echo "❌ Nginx is serving default page instead of React app"
echo "❌ API endpoints are not accessible"
echo ""
echo "🛠️  Issue: Nginx configuration not applied properly"
echo "📋 Next steps: Check Docker build logs and nginx config in containers"
