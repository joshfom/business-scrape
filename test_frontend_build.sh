#!/bin/bash

# Test frontend Docker build locally
echo "🧪 Testing Frontend Docker Build"
echo "================================="

echo "📁 Checking required files..."
files=("frontend/package.json" "frontend/public/index.html" "frontend/src" "frontend/tsconfig.json" "frontend/.env")

for file in "${files[@]}"; do
    if [ -e "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit 1
    fi
done

echo ""
echo "🐳 Building frontend Docker image..."
if docker build -f Dockerfile.frontend -t business-scraper-frontend-test .; then
    echo "✅ Frontend Docker build successful!"
    echo ""
    echo "🧹 Cleaning up test image..."
    docker rmi business-scraper-frontend-test
    echo "✅ Test completed successfully!"
else
    echo "❌ Frontend Docker build failed!"
    exit 1
fi
