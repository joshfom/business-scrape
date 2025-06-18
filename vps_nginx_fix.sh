#!/bin/bash

# Quick VPS nginx fix - run this on your VPS
# This updates the nginx configuration to accept any hostname/IP

echo "🔧 Updating nginx configuration on VPS..."

# SSH into VPS and update nginx config
ssh root@152.53.168.44 << 'ENDSSH'

# Navigate to the project directory
cd /opt/business-scrape

# Update nginx.conf to accept any server name
sed -i 's/server_name localhost;/server_name _;/' nginx.conf

# Verify the change
echo "Updated nginx.conf:"
grep "server_name" nginx.conf

# Start the containers with the updated configuration
echo "Starting containers with updated nginx config..."
docker-compose up -d --build

# Wait for containers to start
sleep 30

# Show container status
echo "Container status:"
docker-compose ps

# Test the API
echo "Testing API..."
curl -u intobusiness:Goodluck@2025 http://localhost/api/public/stats

echo "🎉 Update complete!"
echo "Try accessing http://152.53.168.44 in your browser now"

ENDSSH
