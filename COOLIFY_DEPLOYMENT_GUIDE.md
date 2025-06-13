# Deploying Business Scraper with Coolify

Coolify is a self-hosted Heroku/Netlify alternative that makes deploying applications incredibly simple. This guide will walk you through deploying your Business Scraper application using Coolify.

## Prerequisites

✅ Coolify is already installed on your VPS  
✅ You have access to the Coolify dashboard  
✅ Your Business Scraper code is in a Git repository (GitHub, GitLab, etc.)  

## Step 1: Prepare Your Repository

Before deploying with Coolify, ensure your repository has the necessary Docker files. If you haven't already, commit these files to your repository:

### Required Files in Your Repository:
- `docker-compose.yml`
- `Dockerfile.backend`
- `Dockerfile.frontend`
- `nginx.conf`
- `.env.docker` (rename to `.env`)
- `scripts/mongo-init.js`

### Optional but Recommended:
- `scripts/backup.sh`
- This deployment guide

## Step 2: Access Coolify Dashboard

1. Navigate to your Coolify dashboard (usually at `https://your-domain.com` or `http://your-server-ip:8000`)
2. Log in with your Coolify credentials

## Step 3: Create a New Project

1. Click on **"New Project"**
2. Give your project a name: `business-scraper`
3. Add a description: `Web scraping application for business data`

## Step 4: Add Your Git Repository

1. In your project, click **"New Resource"**
2. Select **"Git Repository"**
3. Choose your Git provider (GitHub, GitLab, etc.)
4. Enter your repository URL: `https://github.com/yourusername/business-scrape`
5. Select the branch (usually `main` or `master`)

## Step 5: Configure the Application

### Application Settings:
1. **Name**: `business-scraper`
2. **Build Pack**: Select **"Docker Compose"**
3. **Port**: `80` (for the frontend)
4. **Dockerfile Location**: Keep default (Coolify will find docker-compose.yml)

### Environment Variables:
Add these environment variables in Coolify:

```bash
# Database Configuration
MONGODB_URI=mongodb://mongodb:27017/business_scraper

# Application Settings
PYTHONUNBUFFERED=1
NODE_ENV=production

# Frontend API Configuration
REACT_APP_API_URL=/api
```

## Step 6: Configure Docker Compose Services

Coolify will automatically detect your `docker-compose.yml` file. Make sure your compose file looks like this:

```yaml
version: '3.8'

services:
  # MongoDB Database
  mongodb:
    image: mongo:6.0
    restart: unless-stopped
    environment:
      MONGO_INITDB_DATABASE: business_scraper
    volumes:
      - mongodb_data:/data/db
      - ./scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/business_scraper --quiet
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Backend API
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    restart: unless-stopped
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/business_scraper
      - PYTHONUNBUFFERED=1
    depends_on:
      mongodb:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs

  # Frontend
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
      args:
        - REACT_APP_API_URL=/api
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  mongodb_data:
    driver: local
```

## Step 7: Set Up Domain and SSL

### Domain Configuration:
1. In Coolify, go to your application settings
2. Click on **"Domains"**
3. Add your domain: `scraper.yourdomain.com` (or use the server IP)
4. Enable **"Generate SSL Certificate"** for HTTPS

### DNS Configuration:
Point your domain to your server's IP address:
```
A record: scraper.yourdomain.com -> 152.53.168.44
```

## Step 8: Deploy the Application

1. Click **"Deploy"** in your Coolify dashboard
2. Coolify will:
   - Clone your repository
   - Build Docker images
   - Start all services
   - Generate SSL certificates
   - Set up reverse proxy

## Step 9: Monitor Deployment

### View Deployment Logs:
1. Click on **"Logs"** in your application
2. Watch the build and deployment process
3. Look for any errors during the build

### Check Service Status:
1. Go to **"Services"** tab
2. Verify all containers are running:
   - ✅ frontend
   - ✅ backend  
   - ✅ mongodb

## Step 10: Access Your Application

Once deployed, your application will be available at:
- **Frontend**: `https://scraper.yourdomain.com`
- **API**: `https://scraper.yourdomain.com/api`
- **API Docs**: `https://scraper.yourdomain.com/api/docs`

## Coolify-Specific Configuration

### Create a `.coolify` directory in your repository:

```bash
mkdir .coolify
```

### Add deployment hooks (optional):

Create `.coolify/deploy.sh`:
```bash
#!/bin/bash
# Pre-deployment script

echo "🚀 Starting Business Scraper deployment..."

# Create required directories
mkdir -p logs backups

# Set permissions
chmod -R 755 logs backups

echo "✅ Pre-deployment completed"
```

### Add health checks:

Create `.coolify/healthcheck.sh`:
```bash
#!/bin/bash
# Health check script

# Check if backend is responding
if curl -f http://localhost:8000/health; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

# Check if frontend is responding
if curl -f http://localhost:80; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    exit 1
fi

echo "✅ All services are healthy"
```

Make scripts executable:
```bash
chmod +x .coolify/deploy.sh
chmod +x .coolify/healthcheck.sh
```

## Step 11: Set Up Automated Backups

### Using Coolify's Backup Feature:
1. Go to **"Backups"** in your application
2. Enable **"Database Backup"**
3. Set schedule: `0 3 * * *` (daily at 3 AM)
4. Configure backup retention (7 days recommended)

### Custom Backup Service:
Add this to your docker-compose.yml:
```yaml
  backup:
    image: mongo:6.0
    restart: "no"
    volumes:
      - mongodb_data:/data/db:ro
      - ./backups:/backups
      - ./scripts/backup.sh:/backup.sh:ro
    entrypoint: ["/bin/bash", "/backup.sh"]
    depends_on:
      - mongodb
    profiles:
      - backup
```

## Step 12: Set Up Monitoring (Optional)

### Enable Coolify Monitoring:
1. Go to **"Monitoring"** in your application
2. Enable **"Application Monitoring"**
3. Set up alerts for:
   - High CPU usage
   - High memory usage
   - Application downtime

### Custom Monitoring:
Add Prometheus/Grafana monitoring by including these services in docker-compose.yml.

## Step 13: Environment-Specific Configuration

### Production Settings:
```bash
# In Coolify environment variables
NODE_ENV=production
PYTHONUNBUFFERED=1
DEBUG=false

# Database
MONGODB_URI=mongodb://mongodb:27017/business_scraper

# Security
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
```

## Management Through Coolify

### Common Operations:

1. **Restart Application**: 
   - Go to your application → Click "Restart"

2. **View Logs**: 
   - Applications → Logs → Select service

3. **Scale Services**: 
   - Go to Services → Select service → Adjust replicas

4. **Update Application**: 
   - Push to your Git repository
   - Coolify will auto-deploy (if enabled)
   - Or manually click "Deploy"

5. **Rollback**: 
   - Go to Deployments → Select previous deployment → Rollback

## Troubleshooting

### Common Issues:

**Build fails:**
```bash
# Check build logs in Coolify
# Ensure all Docker files are in repository
# Verify environment variables are set
```

**Services won't start:**
```bash
# Check service logs in Coolify
# Verify port conflicts
# Check resource usage
```

**Database connection issues:**
```bash
# Check MongoDB service status
# Verify MONGODB_URI environment variable
# Check network connectivity between services
```

## Advantages of Using Coolify

✅ **Easy deployments** - Git push to deploy  
✅ **Built-in SSL** - Automatic HTTPS certificates  
✅ **Monitoring** - Built-in application monitoring  
✅ **Backups** - Automated backup management  
✅ **Scaling** - Easy horizontal scaling  
✅ **Rollbacks** - One-click rollback to previous versions  
✅ **Logs** - Centralized log management  
✅ **Multiple environments** - Easy staging/production setups  

## Best Practices

1. **Use Git tags** for version control
2. **Enable auto-deployment** for main branch
3. **Set up staging environment** for testing
4. **Configure proper health checks**
5. **Monitor resource usage**
6. **Regular backups** of both app and database
7. **Use environment variables** for configuration
8. **Enable SSL** for production

## Security Considerations

1. **Enable SSL/HTTPS** through Coolify
2. **Set up basic auth** if needed (through Coolify proxy settings)
3. **Use secrets** for sensitive configuration
4. **Regularly update** base Docker images
5. **Monitor** for security vulnerabilities

Your Business Scraper application should now be deployed and running smoothly with Coolify! The platform handles most of the complexity while giving you full control over your application.
