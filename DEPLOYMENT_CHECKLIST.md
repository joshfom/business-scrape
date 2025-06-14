# Single Container Deployment Checklist

## Pre-Deployment

- [ ] External MongoDB is running and accessible
- [ ] MongoDB connection string is updated in:
  - [ ] `Dockerfile.single` (line 52)
  - [ ] `supervisord.conf` (line 12)
  - [ ] `coolify.json` (environment section)
- [ ] Frontend builds successfully locally
- [ ] Backend runs successfully locally

## Coolify Configuration

- [ ] Build Pack: `Dockerfile`
- [ ] Dockerfile: `Dockerfile.single`
- [ ] Port: `80`
- [ ] Environment Variables:
  - [ ] `MONGODB_URI`: Your external MongoDB connection string
  - [ ] `PYTHONUNBUFFERED`: `1`

## Post-Deployment Testing

- [ ] Frontend loads: `https://your-domain.com/`
- [ ] API health: `https://your-domain.com/api/health`
- [ ] API docs: `https://your-domain.com/api/docs`
- [ ] Can create scraping jobs through the dashboard
- [ ] Data is saved to external MongoDB

## Troubleshooting Steps

If deployment fails:

1. **Check build logs** in Coolify for errors
2. **Verify environment variables** are set correctly
3. **Test container locally** using `scripts/test_single_container.sh`
4. **Check MongoDB connectivity** from the container
5. **Review supervisor logs** for service startup issues

## Local Testing

Run this command to test the single container locally:

```bash
./scripts/test_single_container.sh
```

This will:
- Build the single container image
- Run it locally on port 8080
- Test all endpoints
- Show logs and status

## File Changes Made

- ✅ `nginx.conf`: Updated to serve from `/var/www/html` and proxy to `localhost:8000`
- ✅ `Dockerfile.single`: Complete single-container setup
- ✅ `supervisord.conf`: Runs backend and nginx (no MongoDB)
- ✅ `coolify.json`: Updated for single container deployment
- ✅ `SINGLE_CONTAINER_COOLIFY_GUIDE.md`: Comprehensive deployment guide
- ✅ `scripts/test_single_container.sh`: Local testing script

## Next Steps

1. Update your external MongoDB connection string in the files listed above
2. Test locally using the test script
3. Update Coolify settings as specified
4. Deploy and verify all endpoints work

## Benefits

- ✅ Single container = simpler deployment
- ✅ No container orchestration needed
- ✅ Better resource utilization
- ✅ Works perfectly with Coolify
- ✅ External MongoDB for data persistence
- ✅ nginx handles static files efficiently
