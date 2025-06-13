# Coolify Deployment Troubleshooting Guide

## Issue: Coolify Using Nixpacks Instead of Docker Compose

### Problem
Coolify detected the Python application and defaulted to using Nixpacks instead of the Docker Compose configuration we want.

### Solutions (Try in Order)

#### Solution 1: Force Docker Compose via Coolify Dashboard
1. **Go to your Coolify dashboard**
2. **Navigate to your application**
3. **Go to "Source" or "Build" settings**
4. **Change "Build Pack" from "nixpacks" to "docker-compose"**
5. **Set "Docker Compose File" to: `docker-compose.coolify.yml`**
6. **Save and redeploy**

#### Solution 2: Use Configuration Files
We've created multiple configuration files to force Docker Compose:

- `.coolify.yml` - Main Coolify configuration
- `coolify.json` - Alternative JSON configuration  
- `.env.coolify` - Environment variables for Coolify

**After adding these files:**
1. Commit and push to your repository
2. In Coolify dashboard, trigger a new deployment
3. Check the build logs to ensure it uses Docker Compose

#### Solution 3: Manual Override in Coolify
1. **In Coolify dashboard, go to your app**
2. **Click "Edit Application"**
3. **Under "Build Configuration":**
   - Set "Build Pack" to "docker-compose"
   - Set "Docker Compose File" to "docker-compose.coolify.yml"
   - Set "Port" to "80"
4. **Save and redeploy**

#### Solution 4: Repository Structure Check
Ensure your repository has these files in the root:
```
.coolify.yml
coolify.json
.env.coolify
docker-compose.coolify.yml
Dockerfile.backend
Dockerfile.frontend
```

### Verification Steps

1. **Check Build Logs**
   - Look for "Using docker-compose" instead of "Using nixpacks"
   - Should see Docker Compose build steps

2. **Check Services**
   - All 3 services should start: mongodb, backend, frontend
   - Health checks should pass

3. **Test Application**
   - Frontend should be accessible
   - API endpoints should work at `/api/...`

### Alternative: Single Container Approach

If Docker Compose continues to fail, we can use a single container:

1. **In Coolify dashboard:**
   - Set "Build Pack" to "dockerfile"
   - Set "Dockerfile" to "Dockerfile.single"
   - Set "Port" to "80"

2. **This will use our single-container setup with:**
   - MongoDB embedded
   - Backend and Frontend in one container
   - Nginx proxy

### Environment Variables for Coolify

Set these in Coolify dashboard under "Environment Variables":
```
MONGODB_URI=mongodb://localhost:27017/business_scraper
PYTHONUNBUFFERED=1
NODE_ENV=production
```

### Debugging Commands

If you have SSH access to the Coolify server:

```bash
# Check running containers
docker ps

# Check logs
docker logs business-scraper-frontend
docker logs business-scraper-backend
docker logs business-scraper-mongodb

# Check networks
docker network ls

# Restart services
docker-compose -f docker-compose.coolify.yml restart
```

### Contact Points

If these solutions don't work:
1. Check Coolify documentation for Docker Compose support
2. Verify Coolify version supports multi-service deployments
3. Consider using the single container approach as fallback
4. Check Coolify community for similar issues

### Success Indicators

✅ Build logs show "Using docker-compose"  
✅ All 3 containers start successfully  
✅ Health checks pass  
✅ Frontend loads at your domain  
✅ API responds at `/api/health`  
✅ Can scrape and view data  

### Quick Commands to Run After Pushing Files

```bash
# Commit the new configuration files
git add .coolify.yml coolify.json .env.coolify
git commit -m "Add Coolify Docker Compose configuration"
git push origin main

# Then trigger redeploy in Coolify dashboard
```
