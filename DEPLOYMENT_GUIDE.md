# Deploying the Business Scraper Project to a VPS

This guide will walk you through deploying the Business Scraper application to a VPS (Virtual Private Server), allowing it to run continuously in the cloud.

## 1. Choose a VPS Provider

There are several reliable VPS providers to choose from:

- **DigitalOcean** - Simple pricing, user-friendly interface
- **Linode** - Good performance-to-cost ratio
- **AWS EC2** - Feature-rich but more complex
- **Vultr** - Affordable options with good performance
- **OVH** - Cost-effective solutions

For beginners, I recommend **DigitalOcean** or **Linode** for their simplicity.

### Minimum Requirements:
- 2 vCPUs
- 4 GB RAM
- 25 GB SSD
- Ubuntu 22.04 LTS

## 2. Initial Server Setup

After creating your VPS with Ubuntu 22.04:

1. **SSH into your server**:

```bash
ssh root@your_server_ip
```

2. **Create a non-root user**:

```bash
adduser scraper_user
usermod -aG sudo scraper_user
```

3. **Set up SSH keys** (optional but recommended):

```bash
mkdir -p /home/scraper_user/.ssh
chmod 700 /home/scraper_user/.ssh
# Copy your public key to the authorized_keys file
echo "your_public_key_content" > /home/scraper_user/.ssh/authorized_keys
chmod 600 /home/scraper_user/.ssh/authorized_keys
chown -R scraper_user:scraper_user /home/scraper_user/.ssh
```

4. **Switch to the new user**:

```bash
su - scraper_user
```

## 3. Install Required Software

Install all necessary software for the application:

```bash
# Update package index
sudo apt update
sudo apt upgrade -y

# Install Python and development tools
sudo apt install -y python3 python3-pip python3-dev python3-venv

# Install MongoDB
sudo apt install -y gnupg
curl -fsSL https://pgp.mongodb.com/server-6.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod

# Install Node.js and npm (for frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install PM2 (process manager)
sudo npm install -g pm2
```

## 4. Clone and Set Up the Application

Clone your repository and set up the application:

```bash
# Navigate to home directory
cd ~

# Clone the repository
git clone https://github.com/yourusername/business-scrape.git
cd business-scrape

# Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
npm run build
cd ..
```

## 5. Configure the Application

Configure the application for production:

1. **Update backend configuration** - Create a production config file:

```bash
cd ~/business-scrape/backend
nano config.py
```

Update the MongoDB connection string and any other settings:

```python
# Add or modify these lines in config.py
MONGODB_URI = "mongodb://localhost:27017/business_scraper"
DEBUG = False
```

2. **Configure the frontend** - Create a production .env file:

```bash
cd ~/business-scrape/frontend
nano .env.production
```

Add the following:

```
REACT_APP_API_URL=http://your_server_ip:8000/api
```

Then rebuild the frontend:

```bash
npm run build
```

## 6. Set Up PM2 to Manage the Application

Create PM2 configuration to manage both frontend and backend:

```bash
cd ~/business-scrape
nano ecosystem.config.js
```

Add the following configuration:

```javascript
module.exports = {
  apps: [
    {
      name: 'business-scraper-backend',
      cwd: './backend',
      script: '../venv/bin/python3',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 8000',
      env: {
        PYTHONUNBUFFERED: 1
      },
      watch: false,
      autorestart: true,
      max_memory_restart: '1G',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    },
    {
      name: 'business-scraper-frontend',
      cwd: './frontend',
      script: 'serve',
      args: '-s build -l 3020',
      env: {
        PM2_SERVE_PATH: './build',
        PM2_SERVE_PORT: 3020
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
    }
  ]
};
```

Install the `serve` package for serving the frontend:

```bash
sudo npm install -g serve
```

Start the application with PM2:

```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

Follow the instructions provided by the `pm2 startup` command to enable PM2 to start on system boot.

## 7. Set Up NGINX as a Reverse Proxy

Install and configure NGINX:

```bash
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/business-scraper
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name your_server_ip_or_domain;

    # Frontend
    location / {
        proxy_pass http://localhost:3020;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/business-scraper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 8. Set Up SSL with Let's Encrypt (Optional but Recommended)

If you have a domain pointed to your server:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your_domain.com
```

## 9. Firewall Configuration

Configure the firewall:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## 10. Monitoring and Management

Monitor your application:

```bash
# View logs
pm2 logs

# Monitor processes
pm2 monit

# Restart services
pm2 restart all

# Check application status
pm2 status
```

## 11. Database Backup Strategy

Set up automatic MongoDB backups:

```bash
# Create backup script
nano ~/backup_mongodb.sh
```

Add the following:

```bash
#!/bin/bash
BACKUP_DIR="/home/scraper_user/mongodb_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p $BACKUP_DIR
mongodump --db business_scraper --out $BACKUP_DIR/backup_$TIMESTAMP
find $BACKUP_DIR -type d -name "backup_*" -mtime +7 -exec rm -rf {} \;
```

Make it executable:

```bash
chmod +x ~/backup_mongodb.sh
```

Set up a daily cron job:

```bash
crontab -e
```

Add:

```
0 3 * * * /home/scraper_user/backup_mongodb.sh
```

## 12. Troubleshooting Common Issues

### Backend won't start:
- Check logs: `pm2 logs business-scraper-backend`
- Verify MongoDB is running: `sudo systemctl status mongod`
- Check Python dependencies: `source venv/bin/activate && pip install -r requirements.txt`

### Frontend won't load:
- Check NGINX configuration: `sudo nginx -t`
- Verify frontend server is running: `pm2 status business-scraper-frontend`

### Database connection issues:
- Check MongoDB status: `sudo systemctl status mongod`
- Verify connection string in config.py

## 13. Scaling Considerations

As your scraping needs grow:

- Increase VPS resources (CPU/RAM) for larger workloads
- Consider setting up a load balancer for high traffic
- Implement MongoDB replication for database redundancy
- Set up separate VPS instances for frontend and backend

## Conclusion

Your Business Scraper application should now be deployed on a VPS and running continuously. This setup allows the application to run 24/7 without the need for your personal computer to remain on.

For any issues or questions, refer to the troubleshooting section or consult the official documentation for each component.
