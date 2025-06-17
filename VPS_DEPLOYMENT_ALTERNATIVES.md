# VPS Deployment Alternatives Guide

Since your Coolify deployment is still showing the nginx default page, here are reliable alternative deployment methods for your VPS:

## 🚨 Current Coolify Issue
Your deployment at `http://v884ko8g0cwsosggsg480o4w.152.53.168.44.sslip.io/` is showing the default nginx page, indicating the single-container configuration isn't working properly in Coolify.

## 🎯 Alternative VPS Deployment Options

### Option 1: Direct Docker Deployment (Recommended)

This is the most reliable method - deploy directly to your VPS using Docker:

#### Step 1: Prepare Your VPS
```bash
# SSH into your VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install Docker if not already installed
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

#### Step 2: Deploy Using Our Script
```bash
# Clone the repository
git clone https://github.com/joshfom/business-scrape.git
cd business-scrape

# Run the deployment script
./scripts/vps_deploy.sh your-domain.com "your-mongodb-uri"
```

**What this does:**
- Builds the single container image
- Runs it on port 80
- Sets up nginx reverse proxy (optional)
- Configures auto-restart
- Tests all endpoints

### Option 2: Docker Compose on VPS

#### Step 1: Use the VPS Docker Compose File
```bash
# On your VPS
git clone https://github.com/joshfom/business-scrape.git
cd business-scrape

# Update MongoDB URI in docker-compose.vps.yml
nano docker-compose.vps.yml

# Deploy
docker-compose -f docker-compose.vps.yml up -d
```

#### Step 2: Test
```bash
curl http://localhost/
curl http://localhost/api/health
```

### Option 3: Manual Installation (No Docker)

If you prefer not to use Docker:

```bash
# Run the manual installation script
./scripts/manual_vps_install.sh "your-mongodb-uri"
```

**What this does:**
- Installs Python, Node.js, nginx, supervisor
- Builds the React frontend
- Sets up the FastAPI backend with supervisor
- Configures nginx to serve both
- Starts all services

## 🔧 Why These Methods Work Better Than Coolify

1. **Direct Control**: You control exactly how the application is built and deployed
2. **Proven Configuration**: Uses the exact same setup as your working local environment
3. **Better Debugging**: Direct access to logs and configuration
4. **No Platform Limitations**: Not constrained by Coolify's interpretation of your config

## 📋 Recommended Approach: Option 1 (Direct Docker)

I recommend **Option 1** because:
- ✅ Uses your proven `Dockerfile.single`
- ✅ Same container that works locally
- ✅ Easy to manage and update
- ✅ Includes health checks and auto-restart
- ✅ Can easily add SSL later

## 🚀 Quick Deployment Commands

### For Option 1 (Direct Docker):
```bash
# SSH to your VPS
ssh root@your-vps-ip

# Clone and deploy
git clone https://github.com/joshfom/business-scrape.git
cd business-scrape
./scripts/vps_deploy.sh your-domain.com
```

### For Option 2 (Docker Compose):
```bash
# SSH to your VPS
ssh root@your-vps-ip

# Clone and deploy
git clone https://github.com/joshfom/business-scrape.git
cd business-scrape
docker-compose -f docker-compose.vps.yml up -d
```

## 🔍 Post-Deployment Testing

After deployment, test these URLs (replace with your VPS IP):

1. **Frontend**: `http://your-vps-ip/`
2. **API Health**: `http://your-vps-ip/api/health`
3. **API Docs**: `http://your-vps-ip/api/docs`

## 🛠️ Management Commands

### Docker Deployment:
```bash
# View logs
docker logs business-scraper

# Restart
docker restart business-scraper

# Update
git pull
docker build -f Dockerfile.single -t business-scraper:latest .
docker restart business-scraper
```

### Manual Deployment:
```bash
# View backend logs
sudo supervisorctl tail business-scraper-backend

# Restart services
sudo supervisorctl restart business-scraper-backend
sudo systemctl restart nginx
```

## 🔒 Adding SSL (Optional)

After successful deployment, you can add SSL using Certbot:

```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d your-domain.com
```

## 💡 Why This Approach is Better

- **Reliability**: Direct deployment eliminates platform-specific issues
- **Control**: Full control over configuration and deployment process
- **Debugging**: Direct access to logs and system
- **Performance**: No additional abstraction layers
- **Cost**: Uses your VPS directly without platform fees

These methods will give you a working deployment that you can rely on and easily manage!
