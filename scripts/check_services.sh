#!/bin/bash
# Script to check if all required services are running

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check function
check_service() {
    echo -e "${YELLOW}Checking $1...${NC}"
    if $2; then
        echo -e "${GREEN}✅ $1 is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 is NOT running${NC}"
        return 1
    fi
}

# Header
echo -e "${GREEN}======================================="
echo -e "    Business Scraper Service Check"
echo -e "=======================================${NC}"

# Check MongoDB
check_service "MongoDB" "systemctl is-active --quiet mongod"
MONGODB_STATUS=$?

# Check NGINX
check_service "NGINX" "systemctl is-active --quiet nginx"
NGINX_STATUS=$?

# Check PM2 processes
echo -e "${YELLOW}Checking PM2 processes...${NC}"
PM2_OUTPUT=$(pm2 list 2>/dev/null)
if [ $? -eq 0 ] && echo "$PM2_OUTPUT" | grep -q "business-scraper-backend"; then
    echo -e "${GREEN}✅ Backend process is running${NC}"
    BACKEND_STATUS=0
else
    echo -e "${RED}❌ Backend process is NOT running${NC}"
    BACKEND_STATUS=1
fi

if [ $? -eq 0 ] && echo "$PM2_OUTPUT" | grep -q "business-scraper-frontend"; then
    echo -e "${GREEN}✅ Frontend process is running${NC}"
    FRONTEND_STATUS=0
else
    echo -e "${RED}❌ Frontend process is NOT running${NC}"
    FRONTEND_STATUS=1
fi

# Summary
echo -e "\n${GREEN}======================================="
echo -e "             Status Summary"
echo -e "=======================================${NC}"

if [ $MONGODB_STATUS -eq 0 ] && [ $NGINX_STATUS -eq 0 ] && [ $BACKEND_STATUS -eq 0 ] && [ $FRONTEND_STATUS -eq 0 ]; then
    echo -e "${GREEN}All services are running correctly!${NC}"
else
    echo -e "${RED}Some services are not running correctly.${NC}"
    
    # Troubleshooting advice
    echo -e "\n${YELLOW}Troubleshooting:${NC}"
    
    if [ $MONGODB_STATUS -ne 0 ]; then
        echo -e "- MongoDB: Try restarting with 'sudo systemctl restart mongod'"
    fi
    
    if [ $NGINX_STATUS -ne 0 ]; then
        echo -e "- NGINX: Check configuration with 'sudo nginx -t' and restart with 'sudo systemctl restart nginx'"
    fi
    
    if [ $BACKEND_STATUS -ne 0 ]; then
        echo -e "- Backend: Start with 'cd ~/business-scrape && pm2 start ecosystem.config.js --only business-scraper-backend'"
    fi
    
    if [ $FRONTEND_STATUS -ne 0 ]; then
        echo -e "- Frontend: Start with 'cd ~/business-scrape && pm2 start ecosystem.config.js --only business-scraper-frontend'"
    fi
fi
