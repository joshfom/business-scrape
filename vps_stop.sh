#!/bin/bash
# VPS shutdown script for Business Scraper application

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================="
echo -e "    Stopping Business Scraper on VPS"
echo -e "=========================================${NC}"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root or with sudo${NC}"
  exit 1
fi

# 1. Stop application with PM2
echo -e "${YELLOW}Stopping application with PM2...${NC}"

# Check if PM2 is installed
if command -v pm2 &> /dev/null; then
  # Stop all PM2 processes
  pm2 stop all
  echo -e "${GREEN}✅ PM2 processes stopped${NC}"
else
  echo -e "${RED}PM2 is not installed. Skipping PM2 shutdown.${NC}"
fi

# 2. Stop NGINX (optional, only if you want to completely shut down web server)
read -p "Do you want to stop NGINX? This will prevent web access to any sites on this server. (y/n): " stop_nginx
if [[ $stop_nginx == "y" || $stop_nginx == "Y" ]]; then
  echo -e "${YELLOW}Stopping NGINX...${NC}"
  systemctl stop nginx
  echo -e "${GREEN}✅ NGINX stopped${NC}"
else
  echo -e "${YELLOW}Keeping NGINX running${NC}"
fi

# 3. Stop MongoDB (optional, only if you want to shut down the database)
read -p "Do you want to stop MongoDB? This will prevent database access to all applications. (y/n): " stop_mongodb
if [[ $stop_mongodb == "y" || $stop_mongodb == "Y" ]]; then
  echo -e "${YELLOW}Stopping MongoDB...${NC}"
  systemctl stop mongod
  echo -e "${GREEN}✅ MongoDB stopped${NC}"
else
  echo -e "${YELLOW}Keeping MongoDB running${NC}"
fi

echo -e "\n${GREEN}========================================="
echo -e "    Business Scraper Shutdown Complete"
echo -e "=========================================${NC}"

# Status summary
echo -e "${YELLOW}Current service status:${NC}"
echo -e "MongoDB: $(systemctl is-active mongod)"
echo -e "NGINX: $(systemctl is-active nginx)"
echo -e "PM2 processes: $(if pm2 list &>/dev/null; then echo "Stopped"; else echo "Not available"; fi)"

echo -e "\nTo restart services: ./vps_start.sh"
