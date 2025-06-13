# Docker Deployment Guide for Business Scraper

This guide shows you how to deploy the Business Scraper application using Docker containers. This approach eliminates compatibility issues and makes deployment much simpler.

## Prerequisites

Your VPS needs only:
- Docker
- Docker Compose
- Git (to clone your repository)

## Quick Start

### 1. Install Docker on Your VPS

```bash
# Connect to your VPS
ssh root@152.53.168.44

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install -y docker-compose

# Start Docker service
systemctl start docker
systemctl enable docker

# Add user to docker group (optional, to run docker without sudo)
usermod -aG docker scraper_user
```

### 2. Deploy the Application

```bash
# Clone or upload your application
cd /home/scraper_user
git clone https://github.com/yourusername/business-scrape.git
# OR upload via scp: scp -r /Users/joshua/Code/business-scrape scraper_user@152.53.168.44:~/

cd business-scrape

# Build and start all services
docker-compose up -d --build
```

That's it! Your application will be available at:
- **Frontend**: http://152.53.168.44
- **API**: http://152.53.168.44/api
- **API Docs**: http://152.53.168.44/api/docs

## What Gets Created

The Docker setup includes:

### 🐳 **Containers**
- **MongoDB**: Database server (port 27017)
- **Backend**: FastAPI application (port 8000)
- **Frontend**: React app served by Nginx (port 80)
- **Backup**: Automated backup service

### 📦 **Features**
- **Automatic restarts**: All containers restart if they crash
- **Health checks**: Monitors service health and dependencies
- **Data persistence**: MongoDB data survives container restarts
- **Automated backups**: Daily database backups at 3 AM
- **Optimized builds**: Multi-stage builds for smaller images
- **Network isolation**: Services communicate securely

## Management Commands

### Basic Operations
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb

# Restart a specific service
docker-compose restart backend

# Check service status
docker-compose ps
```

### Monitoring
```bash
# Monitor resource usage
docker stats

# Check container health
docker-compose ps

# View detailed service info
docker inspect business-scraper-backend
```

### Database Operations
```bash
# Connect to MongoDB
docker exec -it business-scraper-mongodb mongosh business_scraper

# Run a manual backup
docker-compose run --rm backup

# Restore from backup
docker exec -i business-scraper-mongodb mongorestore --db business_scraper --drop /backups/your_backup_folder/business_scraper
```

### Updates and Maintenance
```bash
# Pull latest code and rebuild
git pull
docker-compose down
docker-compose up -d --build

# Clean up unused images and containers
docker system prune -a

# View disk usage
docker system df
```

## Data Persistence

### MongoDB Data
- Stored in Docker volume: `mongodb_data`
- Persists across container restarts
- Automatically backed up to `./backups/` directory

### Backups
- Automatic daily backups at 3 AM
- Stored in `./backups/` directory on the host
- Compressed tar.gz files
- Automatically cleaned up (keeps 7 days)

### Logs
- Application logs stored in `./logs/` directory
- Accessible from both container and host

## Environment Configuration

Edit `.env.docker` to customize settings:
```bash
# Database connection
MONGODB_URI=mongodb://mongodb:27017/business_scraper

# API URL for frontend
REACT_APP_API_URL=/api

# Python settings
PYTHONUNBUFFERED=1
```

## Adding Basic Authentication

To add HTTP basic auth, create an `.htpasswd` file:

```bash
# Create auth file
docker run --rm httpd:2.4-alpine htpasswd -nbB admin your_password > .htpasswd

# Update docker-compose.yml to mount the file
# Add to frontend service volumes:
volumes:
  - ./.htpasswd:/etc/nginx/.htpasswd:ro

# Update nginx.conf to enable auth
# Add these lines to the server block:
auth_basic "Business Scraper - Restricted Access";
auth_basic_user_file /etc/nginx/.htpasswd;
```

## Scaling and Performance

### Resource Limits
Add resource limits to `docker-compose.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

### Multiple Backend Instances
Scale the backend for higher load:
```bash
docker-compose up -d --scale backend=3
```

## Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check if ports are in use
netstat -tulpn | grep -E ':80|:8000|:27017'
```

**Database connection issues:**
```bash
# Test MongoDB connectivity
docker exec business-scraper-backend ping -c 3 mongodb

# Check MongoDB logs
docker-compose logs mongodb
```

**Build failures:**
```bash
# Clean build cache
docker builder prune

# Rebuild without cache
docker-compose build --no-cache
```

### Health Checks

All services have health checks that you can monitor:
```bash
# Check health status
docker-compose ps

# View health check logs
docker inspect --format='{{json .State.Health}}' business-scraper-backend
```

## Security Considerations

1. **Firewall**: Only expose necessary ports (80, 443)
2. **Updates**: Regularly update base images
3. **Secrets**: Use Docker secrets for sensitive data
4. **Networks**: Services communicate over isolated Docker network
5. **User permissions**: Run containers as non-root when possible

## Production Recommendations

1. **HTTPS**: Add SSL certificates with Let's Encrypt
2. **Monitoring**: Add Prometheus + Grafana for monitoring
3. **Logging**: Configure centralized logging
4. **Backup offsite**: Copy backups to remote storage
5. **Resource monitoring**: Set up alerts for resource usage

## Advantages of Docker Deployment

✅ **Consistency**: Identical environment everywhere  
✅ **Isolation**: No conflicts with host system  
✅ **Easy updates**: Simple rebuild and restart process  
✅ **Rollback**: Easy to revert to previous versions  
✅ **Scalability**: Easy to scale individual services  
✅ **Portability**: Works on any Docker-capable system  
✅ **Development**: Same environment for dev and production  
✅ **Dependencies**: No more dependency hell  

This Docker setup gives you a production-ready, scalable, and maintainable deployment of your Business Scraper application!
