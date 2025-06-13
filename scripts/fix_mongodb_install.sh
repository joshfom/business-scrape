#!/bin/bash
# Fixed MongoDB installation script for Debian 12

# Set English locale for current session
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

echo "Setting up English locale..."
sudo locale-gen en_US.UTF-8
sudo update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

echo "Installing MongoDB 6.0 (more stable for Debian 12)..."

# Remove existing MongoDB repository files
sudo rm -f /etc/apt/sources.list.d/mongodb-org-*.list
sudo rm -f /usr/share/keyrings/mongodb-server-*.gpg

# Install required packages
sudo apt update
sudo apt install -y wget gnupg

# Add MongoDB 6.0 repository (more stable for Debian 12)
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/debian bullseye/mongodb-org/6.0 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Update package list
sudo apt update

# Install MongoDB
sudo apt install -y mongodb-org

# Pin MongoDB packages to prevent automatic updates
echo "mongodb-org hold" | sudo dpkg --set-selections
echo "mongodb-org-database hold" | sudo dpkg --set-selections
echo "mongodb-org-server hold" | sudo dpkg --set-selections
echo "mongodb-mongosh hold" | sudo dpkg --set-selections
echo "mongodb-org-mongos hold" | sudo dpkg --set-selections
echo "mongodb-org-tools hold" | sudo dpkg --set-selections

# Create MongoDB user and directories if they don't exist
sudo useradd mongodb -r -s /bin/false 2>/dev/null || true
sudo mkdir -p /var/lib/mongodb
sudo mkdir -p /var/log/mongodb
sudo chown mongodb:mongodb /var/lib/mongodb
sudo chown mongodb:mongodb /var/log/mongodb

# Start and enable MongoDB
sudo systemctl daemon-reload
sudo systemctl enable mongod
sudo systemctl start mongod

# Check MongoDB status
echo "Checking MongoDB status..."
sleep 3
sudo systemctl status mongod --no-pager

# Test MongoDB connection
echo "Testing MongoDB connection..."
if mongosh --eval "db.adminCommand('ismaster')" >/dev/null 2>&1; then
    echo "✅ MongoDB is running and accessible"
else
    echo "❌ MongoDB connection test failed"
    echo "Trying alternative connection test..."
    if mongo --eval "db.adminCommand('ismaster')" >/dev/null 2>&1; then
        echo "✅ MongoDB is running (using legacy mongo client)"
    else
        echo "❌ MongoDB is not responding"
    fi
fi

echo "MongoDB installation completed!"
