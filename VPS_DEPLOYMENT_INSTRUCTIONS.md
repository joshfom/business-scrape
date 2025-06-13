# Deployment Instructions for Your VPS

## Server Details
- **Hostname**: v2202506281396351341.luckysrv.de
- **IP Address**: 152.53.168.44
- **OS**: Debian 12 (Bookworm) - minimal
- **Root Password**: iIcjiS92z45gVEs

## Step 1: Initial Connection and Security

### Connect to your server:
```bash
ssh root@152.53.168.44
# Enter password: iIcjiS92z45gVEs GD25
```

### Change the root password (recommended):
```bash
passwd
# Enter a new secure password
```

### Update the system:
```bash
apt update && apt upgrade -y
```

### Create a non-root user:
```bash
adduser scraper_user
# Follow prompts to set password and user info
usermod -aG sudo scraper_user
```

### Set up SSH key authentication (optional but recommended):
On your local machine, generate SSH keys if you don't have them:
```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

Copy your public key to the server:
```bash
ssh-copy-id scraper_user@152.53.168.44
```

## Step 1.5: Set System Language to English (Optional)

If your system is in German or another language, you can change it to English:

```bash
# Set English locale
sudo locale-gen en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

# Set for current session
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# To make it permanent, add to your .bashrc
echo 'export LANG=en_US.UTF-8' >> ~/.bashrc
echo 'export LC_ALL=en_US.UTF-8' >> ~/.bashrc
```

Note: You may need to log out and log back in for the changes to take full effect.

## Step 2: Install Required Software

Switch to the new user and install dependencies:
```bash
su - scraper_user
```

### Install Git, Python, and development tools:
```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-dev python3-venv build-essential curl gnupg nginx supervisor
```

### Install MongoDB (Fixed for Debian 12):
```bash
# Option 1: Use the fix script (recommended)
# Upload fix_mongodb_install.sh from your local machine first:
# scp /Users/joshua/Code/business-scrape/scripts/fix_mongodb_install.sh scraper_user@152.53.168.44:~/
chmod +x ~/fix_mongodb_install.sh
./fix_mongodb_install.sh

# Option 2: Manual installation if script fails
# Clean up any previous attempts
sudo rm -f /etc/apt/sources.list.d/mongodb-org-*.list
sudo rm -f /usr/share/keyrings/mongodb-server-*.gpg

# Install MongoDB 6.0 (more stable for Debian 12)
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install -y mongodb-org

# Start and enable MongoDB
sudo systemctl daemon-reload
sudo systemctl enable mongod
sudo systemctl start mongod

# Verify MongoDB is running
sudo systemctl status mongod
```

### Install Node.js and npm:
```bash
# Install Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install PM2 globally
sudo npm install -g pm2 serve
```

## Step 3: Deploy the Application

### Clone your repository:
```bash
cd ~
git clone https://github.com/yourusername/business-scrape.git
# Or upload your files using scp from your local machine
```

If you need to upload files from your local machine instead:
```bash
# Run this on your LOCAL machine, not the server
scp -r /Users/joshua/Code/business-scrape scraper_user@152.53.168.44:~/
```

### Set up Python environment:
```bash
cd ~/business-scrape
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Build the frontend:
```bash
cd frontend
npm install
REACT_APP_API_URL=http://152.53.168.44/api npm run build
cd ..
```

## Step 4: Configure PM2

Create the PM2 ecosystem file:
```bash
cat > ecosystem.config.js << 'EOL'
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
EOL
```

## Step 5: Configure NGINX

```bash
sudo tee /etc/nginx/sites-available/business-scraper << 'EOL'
server {
    listen 80;
    server_name 152.53.168.44 v2202506281396351341.luckysrv.de;

    # Frontend
    location / {
        proxy_pass http://localhost:3020;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API
    location /api {
        proxy_pass http://localhost:8000/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOL

# Enable the site
sudo ln -s /etc/nginx/sites-available/business-scraper /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart NGINX
sudo nginx -t
sudo systemctl restart nginx
```

## Step 6: Start the Application

```bash
# Start the application with PM2
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Set up PM2 to start on boot
pm2 startup
# Follow the command output instructions
```

## Step 7: Configure Firewall

```bash
# Install and configure UFW firewall
sudo apt install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

## Step 8: Test the Deployment

Your application should now be accessible at:
- **Frontend**: http://152.53.168.44
- **API**: http://152.53.168.44/api
- **API Docs**: http://152.53.168.44/api/docs

### Check services status:
```bash
# Check all services
sudo systemctl status mongod
sudo systemctl status nginx
pm2 status

# Check logs if needed
pm2 logs
```

## Step 9: Set Up Database Backup

```bash
# Create backup script
cat > ~/backup_mongodb.sh << 'EOL'
#!/bin/bash
BACKUP_DIR="/home/scraper_user/mongodb_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
mkdir -p $BACKUP_DIR
mongodump --db business_scraper --out $BACKUP_DIR/backup_$TIMESTAMP
find $BACKUP_DIR -type d -name "backup_*" -mtime +7 -exec rm -rf {} \;
EOL

chmod +x ~/backup_mongodb.sh

# Add to crontab for daily backups at 3 AM
(crontab -l 2>/dev/null; echo "0 3 * * * /home/scraper_user/backup_mongodb.sh") | crontab -
```

## Troubleshooting

If you encounter issues:

1. **Check service status**: `pm2 status`, `sudo systemctl status mongod nginx`
2. **Check logs**: `pm2 logs`, `sudo journalctl -u mongod`, `sudo journalctl -u nginx`
3. **Check ports**: `sudo netstat -tulpn | grep -E ':80|:8000|:3020|:27017'`
4. **Test API directly**: `curl http://localhost:8000/health`

## Final Notes

- Your application is now running on: **http://152.53.168.44**
- MongoDB is secured and only accessible locally
- PM2 will automatically restart your application if it crashes
- Daily database backups are configured
- The firewall is configured to only allow SSH and web traffic

Remember to change all default passwords and consider setting up SSL certificates for production use.
