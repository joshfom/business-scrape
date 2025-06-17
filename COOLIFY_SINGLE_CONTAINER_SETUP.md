# Coolify Single Container Configuration Guide

## 🚨 IMPORTANT: Switch from Docker Compose to Single Container

Your current Coolify setup is configured for the old multi-container approach. You need to change these settings:

## Current Settings (WRONG for single container):
- ❌ Build Pack: Docker Compose
- ❌ Two separate domains (backend + frontend)
- ❌ Docker Compose Location: /docker-compose.yaml

## Correct Settings for Single Container:

### 1. **General Settings**
- **Name**: Keep current name
- **Build Pack**: `Dockerfile` (NOT Docker Compose)

### 2. **Build Configuration**
- **Dockerfile**: `Dockerfile.single`
- **Base Directory**: `/`
- **Port**: `80`

### 3. **Domain Configuration**
- **Remove**: Both "Domains for Backend" and "Domains for Frontend"
- **Add**: One single domain for the entire application
- **Example**: `http://business-scraper.152.53.168.44.sslip.io`

### 4. **Environment Variables**
Add these environment variables:
```
MONGODB_URI=mongodb://root:77T87Tjn62LDdS5Bq9bY52FGxDBdXfEmJS1cj69elnhQBsRj7BsAnr3SKQF77oot@fo8g4g0w8gcc8k44s8s4gsks:27017/?directConnection=true
PYTHONUNBUFFERED=1
```

### 5. **Build Arguments** (Optional)
```
REACT_APP_API_URL=/api
```

## Step-by-Step Instructions:

### Step 1: Change Build Pack
1. Go to your Coolify application settings
2. Under "Build Pack", change from "Docker Compose" to "Dockerfile"
3. Set "Dockerfile" field to: `Dockerfile.single`

### Step 2: Configure Port
1. Set "Port" to: `80`

### Step 3: Update Domains
1. **Delete** the "Domains for Backend" entry
2. **Delete** the "Domains for Frontend" entry
3. **Add** one new domain for the entire application
4. Click "Generate Domain" to get something like: `business-scraper.152.53.168.44.sslip.io`

### Step 4: Add Environment Variables
1. Go to the Environment Variables section
2. Add:
   - `MONGODB_URI`: Your external MongoDB connection string
   - `PYTHONUNBUFFERED`: `1`

### Step 5: Remove Docker Compose Settings
1. Clear "Docker Compose Location" field (not needed for Dockerfile builds)
2. Clear "Custom Build Command" field (not needed for Dockerfile builds)

### Step 6: Deploy
1. Save all settings
2. Click "Deploy"
3. Monitor build logs

## After Deployment - Test These URLs:

With your single domain (e.g., `business-scraper.152.53.168.44.sslip.io`):

1. **Frontend**: `https://your-domain.com/`
   - Should show React dashboard

2. **API Health**: `https://your-domain.com/api/health`
   - Should return: `{"status": "healthy"}`

3. **API Docs**: `https://your-domain.com/api/docs`
   - Should show FastAPI documentation

## Why Single Domain Works:

```
https://your-domain.com/
├── / → React App (served by nginx)
├── /static/ → React static files
└── /api/ → FastAPI backend (proxied by nginx)
```

The nginx configuration inside the container:
- Serves React app for all non-API routes
- Proxies `/api/*` requests to the FastAPI backend
- Everything runs on port 80 inside the container

## Benefits:
- ✅ Simpler configuration
- ✅ No CORS issues
- ✅ Single SSL certificate
- ✅ Easier to manage
- ✅ Better performance (no cross-domain requests)

## Troubleshooting:

### If build fails:
- Check Coolify build logs
- Ensure `Dockerfile.single` exists in repository
- Verify MongoDB connection string format

### If frontend shows nginx default page:
- Ensure Build Pack is set to "Dockerfile" (not Docker Compose)
- Verify Port is set to 80
- Check that only one domain is configured

### If API doesn't work:
- Test the health endpoint: `/api/health`
- Check environment variables are set
- Review application logs in Coolify
