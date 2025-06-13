# Configure Coolify to use Docker Compose

## Issue Detected
Coolify is currently detecting your application as a Python app and using Nixpacks instead of Docker Compose. This means only the backend is running, without MongoDB or the frontend.

## Solution: Force Docker Compose Usage

### Method 1: Add a .coolify.yml file to your repository root

Create this file in your repository root to tell Coolify to use Docker Compose:

```yaml
# .coolify.yml
version: "3.8"
type: "docker-compose"
services:
  app:
    build: "."
    compose_file: "docker-compose.yml"
```

### Method 2: Configure in Coolify Dashboard

1. Go to your application in Coolify
2. Click on **"Settings"** or **"Configuration"**
3. Look for **"Build Pack"** or **"Build Method"**
4. Change from **"Nixpacks"** to **"Docker Compose"**
5. Set **"Docker Compose File"** to: `docker-compose.yml`
6. **Redeploy** the application

### Method 3: Use a Dockerfile approach (Alternative)

If Docker Compose doesn't work, we can create a single Dockerfile that includes everything:

```dockerfile
# Dockerfile (single-container approach)
FROM node:18-alpine as frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim

# Install MongoDB
RUN apt-get update && \
    apt-get install -y wget gnupg curl && \
    wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add - && \
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list && \
    apt-get update && \
    apt-get install -y mongodb-org nginx supervisor && \
    apt-get clean

# Copy backend
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/ ./

# Copy frontend build
COPY --from=frontend-build /app/frontend/build /var/www/html

# Copy configurations
COPY nginx.conf /etc/nginx/sites-available/default
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create directories
RUN mkdir -p /data/db /var/log/supervisor /app/logs

EXPOSE 80

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
```

## Quick Fix Steps

### Step 1: Add .coolify.yml to your repository

```bash
# In your local repository
cat > .coolify.yml << 'EOF'
version: "3.8"
type: "docker-compose"
services:
  app:
    build: "."
    compose_file: "docker-compose.yml"
EOF

git add .coolify.yml
git commit -m "Add Coolify Docker Compose configuration"
git push origin main
```

### Step 2: Update Coolify Settings

1. Go to your Coolify dashboard
2. Find your business-scraper application
3. Go to **Settings** → **Build**
4. Change **Build Pack** to **"Docker Compose"**
5. Set **Docker Compose File** to: `docker-compose.yml`
6. Save settings

### Step 3: Redeploy

1. Click **"Deploy"** or **"Redeploy"**
2. Coolify should now use Docker Compose and start all services:
   - MongoDB
   - Backend API  
   - Frontend

## Verification

After redeployment, you should see:
- Multiple containers running (not just one Python container)
- Frontend accessible at your domain
- Backend API working at /api
- Database connectivity

## If Docker Compose Still Doesn't Work

Try this single-container approach by creating these files:
