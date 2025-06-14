#!/bin/bash

# Coolify Deployment Verification Script
echo "🔍 Verifying files for Coolify deployment..."

# Check required files
required_files=(
    "requirements.txt"
    "docker-compose.yaml"
    "Dockerfile"
    "Dockerfile.backend"
    "Dockerfile.frontend"
    "nginx.conf"
    "supervisord.conf"
)

missing_files=()
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file MISSING"
        missing_files+=("$file")
    fi
done

# Check directories
required_dirs=("backend" "frontend" "scripts")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir/ directory"
    else
        echo "❌ $dir/ directory MISSING"
        missing_files+=("$dir/")
    fi
done

# Check specific backend files
backend_files=(
    "backend/main.py"
    "backend/config.py"
    "backend/__init__.py"
)

for file in "${backend_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file MISSING"
        missing_files+=("$file")
    fi
done

# Check frontend files
frontend_files=(
    "frontend/package.json"
    "frontend/src/App.tsx"
    "frontend/public/index.html"
)

for file in "${frontend_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file MISSING"
        missing_files+=("$file")
    fi
done

echo ""
if [ ${#missing_files[@]} -eq 0 ]; then
    echo "🎉 All required files are present!"
    echo ""
    echo "✅ Ready for Coolify deployment with:"
    echo "   • Build Pack: Docker Compose"
    echo "   • Docker Compose File: docker-compose.yaml"
    echo "   • Port: 80"
else
    echo "⚠️  Missing files detected:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "Please ensure all files are present before deploying."
fi

echo ""
echo "🔧 Coolify Configuration:"
echo "========================"
echo "Build Pack: Docker Compose"
echo "Docker Compose File: docker-compose.yaml"
echo "Port: 80"
echo "Static Site: No"
echo ""
echo "Environment Variables:"
echo "- MONGODB_URI=mongodb://mongodb:27017/business_scraper"
echo "- PYTHONUNBUFFERED=1"
echo "- NODE_ENV=production"
