#!/bin/bash
# Frontend access test script
# Run this on your VPS to test if everything is working

SERVER_IP="152.53.168.44"
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Testing Business Scraper Frontend Access${NC}\n"

# Test 1: Check if NGINX is responding
echo -e "${YELLOW}1. Testing NGINX response...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:80 | grep -q "200\|301\|302"; then
    echo -e "${GREEN}✅ NGINX is responding${NC}"
else
    echo -e "${RED}❌ NGINX is not responding${NC}"
fi

# Test 2: Check if frontend service is running
echo -e "\n${YELLOW}2. Testing frontend service (port 3020)...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3020 | grep -q "200"; then
    echo -e "${GREEN}✅ Frontend service is responding${NC}"
else
    echo -e "${RED}❌ Frontend service is not responding${NC}"
fi

# Test 3: Check if backend API is running
echo -e "\n${YELLOW}3. Testing backend API (port 8000)...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
    echo -e "${GREEN}✅ Backend API is responding${NC}"
else
    echo -e "${RED}❌ Backend API is not responding${NC}"
fi

# Test 4: Check PM2 processes
echo -e "\n${YELLOW}4. Checking PM2 processes...${NC}"
PM2_STATUS=$(pm2 list 2>/dev/null)
if echo "$PM2_STATUS" | grep -q "business-scraper-frontend.*online"; then
    echo -e "${GREEN}✅ Frontend PM2 process is online${NC}"
else
    echo -e "${RED}❌ Frontend PM2 process is not online${NC}"
fi

if echo "$PM2_STATUS" | grep -q "business-scraper-backend.*online"; then
    echo -e "${GREEN}✅ Backend PM2 process is online${NC}"
else
    echo -e "${RED}❌ Backend PM2 process is not online${NC}"
fi

# Test 5: Test external access
echo -e "\n${YELLOW}5. Testing external access...${NC}"
EXTERNAL_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP 2>/dev/null || echo "000")
if [ "$EXTERNAL_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ External access working${NC}"
    echo -e "${GREEN}🌐 Your frontend is accessible at: http://$SERVER_IP${NC}"
elif [ "$EXTERNAL_RESPONSE" = "000" ]; then
    echo -e "${RED}❌ Cannot connect externally (network/firewall issue)${NC}"
else
    echo -e "${YELLOW}⚠️  External access returns HTTP $EXTERNAL_RESPONSE${NC}"
fi

# Test 6: Check if ports are listening
echo -e "\n${YELLOW}6. Checking listening ports...${NC}"
if netstat -tulpn 2>/dev/null | grep -q ":80.*LISTEN"; then
    echo -e "${GREEN}✅ Port 80 (HTTP) is listening${NC}"
else
    echo -e "${RED}❌ Port 80 (HTTP) is not listening${NC}"
fi

if netstat -tulpn 2>/dev/null | grep -q ":3020.*LISTEN"; then
    echo -e "${GREEN}✅ Port 3020 (Frontend) is listening${NC}"
else
    echo -e "${RED}❌ Port 3020 (Frontend) is not listening${NC}"
fi

if netstat -tulpn 2>/dev/null | grep -q ":8000.*LISTEN"; then
    echo -e "${GREEN}✅ Port 8000 (Backend) is listening${NC}"
else
    echo -e "${RED}❌ Port 8000 (Backend) is not listening${NC}"
fi

echo -e "\n${GREEN}Test completed!${NC}"
echo -e "\nIf all tests pass, you should be able to access your frontend at:"
echo -e "${GREEN}http://$SERVER_IP${NC}"
