#!/bin/bash
# VPS startup script for Business Scraper application

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================="
echo -e "    Starting Business Scraper on VPS"
echo -e "=========================================${NC}"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root or with sudo${NC}"
  exit 1
fi

# 1. Start MongoDB if not running
if ! systemctl is-active --quiet mongod; then
  echo -e "${YELLOW}Starting MongoDB...${NC}"
  systemctl start mongod
  sleep 2
fi

if ! systemctl is-active --quiet mongod; then
  echo -e "${RED}Failed to start MongoDB. Aborting.${NC}"
  exit 1
else
  echo -e "${GREEN}✅ MongoDB is running${NC}"
fi

# 2. Start NGINX if not running
if ! systemctl is-active --quiet nginx; then
  echo -e "${YELLOW}Starting NGINX...${NC}"
  systemctl start nginx
  sleep 2
fi

if ! systemctl is-active --quiet nginx; then
  echo -e "${RED}Failed to start NGINX. Aborting.${NC}"
  exit 1
else
  echo -e "${GREEN}✅ NGINX is running${NC}"
fi

# 3. Start application with PM2
echo -e "${YELLOW}Starting application with PM2...${NC}"

# Get application directory
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $APP_DIR

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
  echo -e "${RED}PM2 is not installed. Installing...${NC}"
  npm install -g pm2
fi

# Check if ecosystem file exists
if [ ! -f "$APP_DIR/ecosystem.config.js" ]; then
  echo -e "${RED}ecosystem.config.js not found. Please run the deploy.sh script first.${NC}"
  exit 1
fi

# Start with PM2
pm2 start ecosystem.config.js
pm2 save

echo -e "\n${GREEN}========================================="
echo -e "    Business Scraper Started Successfully"
echo -e "=========================================${NC}"

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo -e "You can access the application at:"
echo -e "${GREEN}http://${SERVER_IP}${NC}"
echo -e "${GREEN}Backend API: http://${SERVER_IP}/api${NC}"
echo -e "${GREEN}API Documentation: http://${SERVER_IP}/api/docs${NC}"
echo -e "\nTo check status: ./scripts/check_services.sh"
echo -e "To stop services: ./vps_stop.sh"
