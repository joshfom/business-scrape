#!/bin/bash
# Quick fix script for Coolify deployment issue

echo "🔧 Fixing Coolify deployment to use Docker Compose..."

# Create .coolify.yml to force Docker Compose usage
cat > .coolify.yml << 'EOF'
version: "3.8"
type: "docker-compose"
services:
  app:
    build: "."
    compose_file: "docker-compose.yml"
EOF

echo "✅ Created .coolify.yml"

# Commit and push
git add .coolify.yml
git commit -m "Force Coolify to use Docker Compose"
git push origin main

echo "✅ Pushed changes to repository"

echo ""
echo "🎯 Next steps:"
echo "1. Go to your Coolify dashboard"
echo "2. Navigate to your business-scraper application"
echo "3. Go to Settings → Build"
echo "4. Change Build Pack to 'Docker Compose'"
echo "5. Set Docker Compose File to 'docker-compose.yml'"
echo "6. Click 'Deploy' to redeploy"
echo ""
echo "🌐 After redeployment, you should have:"
echo "   - MongoDB container"
echo "   - Backend API container"
echo "   - Frontend container"
echo "   - Full application working at your domain"
