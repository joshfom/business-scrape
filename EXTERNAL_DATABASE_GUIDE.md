# External Database Deployment Guide

This guide shows how to deploy the Business Scraper with external database services instead of running MongoDB in containers.

## 🎯 **Benefits of External Database**

✅ **Simplified Deployment** - No database container management  
✅ **Better Performance** - Dedicated database servers  
✅ **Automatic Backups** - Managed by database service  
✅ **Scalability** - Can handle more connections  
✅ **Reliability** - Professional database hosting  

## 🔧 **Database Service Options**

### **MongoDB Services:**
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) (Free tier available)
- [DigitalOcean Managed MongoDB](https://www.digitalocean.com/products/managed-databases)
- [AWS DocumentDB](https://aws.amazon.com/documentdb/)
- [Google Cloud MongoDB](https://cloud.google.com/mongodb)

### **PostgreSQL Services:**
- [Supabase](https://supabase.com) (Free tier available)
- [Neon](https://neon.tech) (Free tier available)
- [DigitalOcean Managed PostgreSQL](https://www.digitalocean.com/products/managed-databases)
- [AWS RDS PostgreSQL](https://aws.amazon.com/rds/postgresql/)
- [Google Cloud SQL](https://cloud.google.com/sql)

## 📋 **Setup Instructions**

### **Option 1: MongoDB Atlas (Recommended)**

1. **Create MongoDB Atlas Account**
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Create free account
   - Create a new cluster (free M0 tier available)

2. **Get Connection String**
   ```
   mongodb+srv://username:password@cluster.mongodb.net/business_scraper?retryWrites=true&w=majority
   ```

3. **Configure Network Access**
   - In Atlas dashboard, go to Network Access
   - Add IP address `0.0.0.0/0` (allow from anywhere) for Coolify deployment

4. **Create Database User**
   - Go to Database Access in Atlas
   - Create a new user with read/write permissions

### **Option 2: Supabase PostgreSQL (Alternative)**

1. **Create Supabase Project**
   - Go to [Supabase](https://supabase.com)
   - Create new project
   - Note the database URL

2. **Get Connection String**
   ```
   postgresql://username:password@host:5432/database
   ```

## 🚀 **Coolify Deployment Configuration**

### **For MongoDB (Current Setup)**

**Environment Variables in Coolify:**
```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/business_scraper?retryWrites=true&w=majority
DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/business_scraper?retryWrites=true&w=majority
PYTHONUNBUFFERED=1
NODE_ENV=production
```

**Docker Compose File:** `docker-compose.external-db.yml`

### **For PostgreSQL (If Migrating)**

**Environment Variables in Coolify:**
```bash
DATABASE_URL=postgresql://username:password@host:5432/business_scraper
PYTHONUNBUFFERED=1
NODE_ENV=production
```

**Requirements File:** Use `requirements-postgresql.txt`

## 📁 **Updated File Structure**

**For MongoDB (No changes needed):**
- Use existing `docker-compose.external-db.yml`
- Current `requirements.txt` works
- Current database models work

**For PostgreSQL Migration:**
- Use `requirements-postgresql.txt`
- Use `backend/models/database_postgresql.py`
- Run database migrations

## 🔄 **Migration Steps**

### **Step 1: Update Coolify Configuration**

1. **In Coolify Dashboard:**
   - Build Pack: `Docker Compose`
   - Docker Compose File: `docker-compose.external-db.yml`
   - Port: `80`

2. **Add Environment Variables:**
   ```bash
   MONGODB_URI=your_connection_string_here
   PYTHONUNBUFFERED=1
   NODE_ENV=production
   ```

### **Step 2: Deploy**

1. **Commit changes:**
   ```bash
   git add docker-compose.external-db.yml
   git commit -m "Add external database support"
   git push origin main
   ```

2. **Update Coolify settings and redeploy**

### **Step 3: Verify**

- Check that both services start (no MongoDB container)
- Verify API health endpoint: `/api/health`
- Test database connectivity
- Verify scraping functionality

## ✅ **Verification Commands**

**Check container status:**
```bash
docker ps
# Should only see: backend, frontend (no mongodb)
```

**Test API connection:**
```bash
curl https://your-domain/api/health
```

**Check logs:**
```bash
docker logs business-scraper-backend
# Should see: "Successfully connected to MongoDB at mongodb+srv://..."
```

## 🆘 **Troubleshooting**

### **Common Issues:**

1. **Connection String Format**
   - MongoDB: Must include database name in URL
   - Check for special characters that need URL encoding

2. **Network Access**
   - Ensure database allows connections from `0.0.0.0/0`
   - Or get specific IP from Coolify if available

3. **Authentication**
   - Verify username/password are correct
   - Check user has read/write permissions

4. **Database Name**
   - Ensure database `business_scraper` exists
   - Or update DATABASE_NAME in environment

### **Testing Connection Locally:**

```bash
# For MongoDB
mongosh "mongodb+srv://username:password@cluster.mongodb.net/business_scraper"

# For PostgreSQL  
psql "postgresql://username:password@host:5432/business_scraper"
```

## 💡 **Production Tips**

1. **Use Environment Variables** - Never hardcode credentials
2. **Enable SSL** - Most services provide SSL by default
3. **Monitor Usage** - Watch database metrics and quotas
4. **Backup Strategy** - Most services provide automatic backups
5. **Connection Pooling** - Adjust max connections as needed

## 🎯 **Next Steps**

1. Choose your database service (MongoDB Atlas recommended)
2. Create account and get connection string
3. Update Coolify environment variables
4. Deploy with `docker-compose.external-db.yml`
5. Test and verify functionality

This approach eliminates container dependency issues and provides a more robust, production-ready database solution!
