# Single Container Coolify Deployment Guide

This guide covers deploying the Business Scraper application to Coolify using a single Docker container that includes both the FastAPI backend and React frontend, with nginx as a reverse proxy. The MongoDB database is external.

## Prerequisites

1. **External MongoDB Database**: You need an external MongoDB instance. Get the connection string in the format:
   ```
   mongodb://username:password@host:port/?directConnection=true
   ```

2. **Coolify Instance**: Running and accessible

## Deployment Steps

### 1. Update Coolify Application Settings

In your Coolify application:

1. **Build Pack**: Set to `Dockerfile`
2. **Dockerfile**: Set to `Dockerfile.single`
3. **Port**: Set to `80`
4. **Environment Variables**: Add:
   ```
   MONGODB_URI=your_mongodb_connection_string
   PYTHONUNBUFFERED=1
   ```

### 2. Update MongoDB Connection String

Update the `MONGODB_URI` in both:
- `Dockerfile.single` (line 52)
- `supervisord.conf` (line 12)

Replace the current connection string with your external MongoDB credentials.

### 3. Deploy

1. Save the settings in Coolify
2. Click "Deploy"
3. Monitor the build logs

### 4. Verify Deployment

After deployment, test these endpoints:

1. **Frontend**: `https://your-domain.com/`
   - Should show the React dashboard

2. **API Health**: `https://your-domain.com/api/health`
   - Should return: `{"status": "healthy", "timestamp": "..."}`

3. **API Docs**: `https://your-domain.com/api/docs`
   - Should show the FastAPI documentation

## Architecture

```
┌─────────────────────────────────────┐
│           Single Container          │
├─────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────────┐│
│  │    Nginx    │ │   React Build   ││
│  │   (Port 80) │ │  (/var/www/html)││
│  └─────────────┘ └─────────────────┘│
│                ↕                    │
│  ┌─────────────────────────────────┐│
│  │     FastAPI Backend             ││
│  │       (Port 8000)               ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────┐
│        External MongoDB             │
└─────────────────────────────────────┘
```

## Container Services

The single container runs these services via supervisor:

1. **nginx**: Serves React frontend and proxies API requests
2. **FastAPI Backend**: Handles API requests and scraping operations

## File Structure

- `/var/www/html/`: React build files
- `/app/`: FastAPI backend code
- `/etc/nginx/sites-available/default`: Nginx configuration
- `/etc/supervisor/conf.d/supervisord.conf`: Supervisor configuration

## Troubleshooting

### Build Fails
- Check the build logs in Coolify
- Ensure all dependencies are properly specified
- Verify the MongoDB connection string format

### Frontend Shows Nginx Default Page
- Ensure `Dockerfile.single` properly copies the React build
- Check that nginx config points to `/var/www/html`

### API Not Accessible
- Verify the backend is running on port 8000
- Check supervisor logs: `docker exec -it container supervisorctl status`

### Database Connection Issues
- Verify the MongoDB connection string
- Ensure the external MongoDB is accessible from Coolify
- Check backend logs for connection errors

## Environment Variables

Required environment variables:
- `MONGODB_URI`: Connection string to external MongoDB
- `PYTHONUNBUFFERED`: Set to "1" for proper logging

## Health Checks

The container includes a health check that:
- Tests the nginx frontend (port 80)
- Runs every 30 seconds
- Has a 60-second startup period

## Benefits of Single Container Approach

1. **Simplified Deployment**: One container to manage
2. **Reduced Complexity**: No container orchestration needed
3. **Better Resource Usage**: Shared resources between services
4. **Easier Monitoring**: Single container to monitor
5. **Coolify Friendly**: Works well with Coolify's single-container model

## Next Steps

After successful deployment:
1. Set up monitoring and alerts
2. Configure backups for your external MongoDB
3. Set up SSL/TLS if not handled by Coolify
4. Configure rate limiting if needed
5. Set up log aggregation for production monitoring
