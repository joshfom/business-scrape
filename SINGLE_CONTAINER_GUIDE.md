# Single Container Deployment Guide

## 🎯 **Single Container Architecture**

This approach combines everything into one container:
- ✅ **Frontend:** React app served by Nginx on port 80
- ✅ **Backend:** FastAPI running on localhost:8000  
- ✅ **Nginx Proxy:** Routes `/api/*` to backend, everything else to frontend
- ✅ **External MongoDB:** Uses your provided connection string
- ✅ **Supervisor:** Manages backend + nginx processes

## 🚀 **Coolify Configuration Steps:**

### **1. Update Coolify Settings:**
In your Coolify dashboard:

- **Build Pack:** Change from `Docker Compose` to `Dockerfile`
- **Dockerfile:** Set to `Dockerfile.single`
- **Port:** Keep as `80`
- **Is it a static site?** `No`

### **2. Environment Variables (Optional):**
The MongoDB URI is already embedded, but you can override if needed:
```
MONGODB_URI=mongodb://root:77T87Tjn62LDdS5Bq9bY52FGxDBdXfEmJS1cj69elnhQBsRj7BsAnr3SKQF77oot@fo8g4g0w8gcc8k44s8s4gsks:27017/?directConnection=true
PYTHONUNBUFFERED=1
```

### **3. Deploy:**
- Click "Deploy" or "Redeploy"
- Monitor build logs for successful completion

## 📊 **What Happens During Build:**

1. **Stage 1 - Frontend Build:**
   - Installs Node.js dependencies
   - Builds React app with optimized production bundle
   - Creates static files ready for nginx

2. **Stage 2 - Main Container:**
   - Installs Python, nginx, supervisor
   - Copies backend code and installs Python dependencies  
   - Copies built frontend files to nginx directory
   - Configures nginx to serve frontend + proxy API
   - Sets up supervisor to manage processes

## 🔄 **Process Management:**

Supervisor manages two processes:
- **Backend:** `uvicorn main:app --host 0.0.0.0 --port 8000`
- **Nginx:** `nginx -g "daemon off;"`

## ✅ **Expected URLs After Deployment:**

- **Frontend:** `http://your-coolify-domain/` → React dashboard
- **API Health:** `http://your-coolify-domain/api/health` → `{"status": "healthy"}`
- **API Full Health:** `http://your-coolify-domain/api/health/full` → Database status
- **API Endpoints:** `http://your-coolify-domain/api/businesses`, etc.

## 🔍 **Verification Steps:**

1. **Check build logs** - Should see successful frontend build and container creation
2. **Wait for container startup** - Allow 30-60 seconds for all services to start
3. **Test frontend** - Should see React app instead of nginx default page
4. **Test API** - `/api/health` should return JSON response

## 🛠️ **Troubleshooting:**

### If frontend still shows nginx default:
- Check build logs for React build errors
- Verify nginx configuration is being applied

### If API endpoints return 404:
- Check that backend process is running
- Verify MongoDB connection

### Container won't start:
- Check for Python/dependency installation errors
- Verify supervisor configuration

## 📋 **Advantages of Single Container:**

- ✅ **Simpler deployment** - One container to manage
- ✅ **No inter-container networking** - Everything on localhost
- ✅ **Faster startup** - No container dependencies
- ✅ **Easier debugging** - All logs in one place
- ✅ **More reliable** - Fewer moving parts

This approach should resolve all the nginx configuration issues you were experiencing with the multi-container setup!
