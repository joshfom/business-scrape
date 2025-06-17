# VPS Deployment Guide

## Quick Start

1. **Clone the repository on your VPS:**
   ```bash
   git clone <your-repo-url>
   cd business-scrape
   ```

2. **Set up environment:**
   ```bash
   cp .env.template .env
   nano .env  # Update credentials and settings
   ```

3. **Deploy:**
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment:**
   ```bash
   docker-compose ps
   curl -u your_username:your_password http://localhost/
   ```

## Production Considerations

### Firewall Setup
```bash
# Allow HTTP traffic
sudo ufw allow 80/tcp
sudo ufw enable
```

### Domain Setup (Optional)
If using a domain, update your DNS A record to point to your VPS IP.

### SSL Certificate (Recommended)
For HTTPS, consider using a reverse proxy like Caddy or nginx with Let's Encrypt:

```yaml
# Add to docker-compose.yml for SSL
caddy:
  image: caddy:latest
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./Caddyfile:/etc/caddy/Caddyfile
    - caddy_data:/data
```

### Backup Strategy
```bash
# Backup MongoDB data
docker-compose exec mongodb mongodump --authenticationDatabase admin -u admin -p business123 --out /data/db/backup

# Copy backup from container
docker cp business-scraper-mongodb:/data/db/backup ./mongodb-backup-$(date +%Y%m%d)
```

### Monitoring
```bash
# Check logs
docker-compose logs -f

# Check resource usage
docker stats

# Health status
docker-compose ps
```

## Security Checklist

- ✅ Change default passwords in .env
- ✅ Use strong basic auth credentials  
- ✅ Keep .env file secure (not in git)
- ✅ Configure firewall
- ✅ Regular backups
- ✅ Monitor logs for suspicious activity

## Troubleshooting

### Container Issues
```bash
# Restart services
docker-compose restart

# Rebuild if needed
docker-compose build --no-cache
docker-compose up -d
```

### Access Issues
```bash
# Check if services are running
docker-compose ps

# Check logs
docker-compose logs frontend
docker-compose logs backend
```

### Database Issues
```bash
# Check MongoDB connection
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Reset if needed
docker-compose down -v  # ⚠️ This deletes data!
docker-compose up -d
```

---

**Ready for Production Deployment!** 🚀
