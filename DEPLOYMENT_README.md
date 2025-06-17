# Business Scraper Deployment Guide

## 🚀 Local Testing

### Prerequisites
- Docker and Docker Compose installed
- Git repository cloned

### Local Development
```bash
# Test locally on http://localhost:8080
docker-compose -f docker-compose.local.yml up -d --build

# View logs
docker-compose -f docker-compose.local.yml logs -f app

# Stop
docker-compose -f docker-compose.local.yml down
```

## 🌐 Production VPS Deployment

### Quick Deploy
```bash
# On your VPS
git pull origin main
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Test endpoints
curl http://localhost/api/health
curl http://localhost/api/scraping/jobs
```

### Access
- **Frontend**: `http://your-vps-ip/`
- **API Docs**: `http://your-vps-ip/api/docs`
- **Basic Auth**: Username: `admin`, Password: `business123`

## 🔧 Key Fixes Applied

1. **Backend API Routes**: Removed double `/api` prefix
2. **Frontend Configuration**: Updated to use `/api` for same-domain requests
3. **Basic Authentication**: Added nginx basic auth
4. **CORS**: Updated for production domain
5. **MongoDB**: Using external container with proper credentials

## 📊 Available API Endpoints

- `GET /health` - Health check
- `GET /api/scraping/jobs` - List scraping jobs
- `POST /api/scraping/jobs` - Create scraping job
- `GET /api/businesses/stats/summary` - Business statistics
- `GET /api/docs` - API documentation

## 🛠️ Management Commands

### View Logs
```bash
docker-compose -f docker-compose.prod.yml logs app
docker-compose -f docker-compose.prod.yml logs mongodb
```

### Restart Services
```bash
docker-compose -f docker-compose.prod.yml restart
```

### Update Application
```bash
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
```

### Backup MongoDB
```bash
docker exec business-scraper-mongo-prod mongodump --out /backup
```
