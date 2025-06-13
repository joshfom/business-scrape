#!/bin/bash

# Coolify Deployment Fix Script
# This script helps fix Coolify deployments that are using Nixpacks instead of Docker Compose

echo "🔧 Coolify Deployment Fix Script"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.coolify.yml" ]; then
    echo "❌ Error: docker-compose.coolify.yml not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

echo "✅ Found docker-compose.coolify.yml"

# Check for configuration files
echo ""
echo "📋 Checking configuration files..."

files=(".coolify.yml" "coolify.json" ".env.coolify" "docker-compose.coolify.yml")
missing_files=()

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Missing configuration files detected!"
    echo "Some Coolify configuration files are missing."
    echo "This script should have created them. Please check the output above."
fi

# Validate docker-compose.coolify.yml
echo ""
echo "🔍 Validating Docker Compose file..."
if command -v docker-compose &> /dev/null; then
    if docker-compose -f docker-compose.coolify.yml config &> /dev/null; then
        echo "✅ docker-compose.coolify.yml is valid"
    else
        echo "❌ docker-compose.coolify.yml has syntax errors"
        echo "Running validation..."
        docker-compose -f docker-compose.coolify.yml config
        exit 1
    fi
else
    echo "⚠️  docker-compose not found, skipping validation"
fi

# Check Git status
echo ""
echo "📦 Checking Git status..."
if git status --porcelain | grep -E "\.(coolify\.yml|coolify\.json|env\.coolify)$"; then
    echo "🔄 Configuration files need to be committed"
    echo ""
    echo "Run these commands to commit and push:"
    echo "  git add .coolify.yml coolify.json .env.coolify"
    echo "  git commit -m 'Add Coolify Docker Compose configuration'"
    echo "  git push origin main"
else
    echo "✅ Configuration files are committed"
fi

echo ""
echo "🎯 Next Steps:"
echo "=============="
echo ""
echo "1. 📤 PUSH CHANGES (if needed):"
echo "   git add .coolify.yml coolify.json .env.coolify"
echo "   git commit -m 'Add Coolify Docker Compose configuration'"
echo "   git push origin main"
echo ""
echo "2. 🎛️  CONFIGURE COOLIFY DASHBOARD:"
echo "   • Go to your Coolify dashboard"
echo "   • Navigate to your application"
echo "   • Go to 'Source' or 'Build' settings"
echo "   • Change 'Build Pack' from 'nixpacks' to 'docker-compose'"
echo "   • Set 'Docker Compose File' to: docker-compose.coolify.yml"
echo "   • Set 'Port' to: 80"
echo "   • Save settings"
echo ""
echo "3. 🚀 REDEPLOY:"
echo "   • Click 'Deploy' or 'Redeploy' in Coolify dashboard"
echo "   • Monitor build logs for 'Using docker-compose'"
echo "   • Wait for all services to start"
echo ""
echo "4. ✅ VERIFY:"
echo "   • Check that frontend loads"
echo "   • Test API at /api/health"
echo "   • Verify all 3 containers are running"
echo ""
echo "📖 For detailed troubleshooting, see: COOLIFY_TROUBLESHOOTING.md"
echo ""

# Check if git is available and show current branch
if command -v git &> /dev/null; then
    current_branch=$(git branch --show-current 2>/dev/null)
    if [ -n "$current_branch" ]; then
        echo "📍 Current Git branch: $current_branch"
        echo ""
    fi
fi

echo "🔧 Fix script completed!"
