#!/bin/bash
# Script to add basic authentication to the Business Scraper frontend
# This will protect the entire application with a username/password

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "${YELLOW}>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script with sudo"
    exit 1
fi

echo -e "${GREEN}Adding Basic Authentication to Business Scraper${NC}\n"

# Default credentials (you can change these)
DEFAULT_USERNAME="admin"
DEFAULT_PASSWORD="scraper2025!"

# Get credentials from user or use defaults
read -p "Enter username (default: $DEFAULT_USERNAME): " USERNAME
USERNAME=${USERNAME:-$DEFAULT_USERNAME}

read -s -p "Enter password (default: $DEFAULT_PASSWORD): " PASSWORD
PASSWORD=${PASSWORD:-$DEFAULT_PASSWORD}
echo

# Install apache2-utils for htpasswd
print_step "Installing htpasswd utility..."
apt-get update
apt-get install -y apache2-utils

# Create the password file
print_step "Creating password file..."
HTPASSWD_FILE="/etc/nginx/.htpasswd"
echo "$PASSWORD" | htpasswd -i -c "$HTPASSWD_FILE" "$USERNAME"

# Set proper permissions
chmod 644 "$HTPASSWD_FILE"
chown root:www-data "$HTPASSWD_FILE"

# Backup current NGINX configuration
print_step "Backing up current NGINX configuration..."
cp /etc/nginx/sites-available/business-scraper /etc/nginx/sites-available/business-scraper.backup

# Create new NGINX configuration with basic auth
print_step "Updating NGINX configuration with basic authentication..."
cat > /etc/nginx/sites-available/business-scraper << 'EOF'
server {
    listen 80;
    server_name 152.53.168.44 v2202506281396351341.luckysrv.de;

    # Basic Authentication
    auth_basic "Business Scraper - Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;

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
        
        # Pass authentication to backend
        proxy_set_header Authorization $http_authorization;
        proxy_pass_header Authorization;
    }

    # API endpoints - also protected by basic auth
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
        
        # Pass authentication to backend
        proxy_set_header Authorization $http_authorization;
        proxy_pass_header Authorization;
    }

    # Optional: Health check endpoint without auth (for monitoring)
    location /api/health {
        auth_basic off;
        proxy_pass http://localhost:8000/api/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Test NGINX configuration
print_step "Testing NGINX configuration..."
if nginx -t; then
    print_success "NGINX configuration test passed"
    
    # Reload NGINX
    print_step "Reloading NGINX..."
    systemctl reload nginx
    print_success "NGINX reloaded successfully"
else
    print_error "NGINX configuration test failed"
    print_step "Restoring backup configuration..."
    cp /etc/nginx/sites-available/business-scraper.backup /etc/nginx/sites-available/business-scraper
    systemctl reload nginx
    exit 1
fi

echo -e "\n${GREEN}Basic Authentication Setup Complete!${NC}"
echo -e "\n${YELLOW}Login Credentials:${NC}"
echo -e "Username: ${GREEN}$USERNAME${NC}"
echo -e "Password: ${GREEN}$PASSWORD${NC}"
echo -e "\n${YELLOW}Access URLs:${NC}"
echo -e "Frontend: ${GREEN}http://152.53.168.44${NC}"
echo -e "API Docs: ${GREEN}http://152.53.168.44/api/docs${NC}"
echo -e "Health Check (no auth): ${GREEN}http://152.53.168.44/api/health${NC}"

echo -e "\n${YELLOW}Important Notes:${NC}"
echo -e "• All access now requires the username and password above"
echo -e "• The browser will prompt for credentials on first visit"
echo -e "• Credentials are stored in: /etc/nginx/.htpasswd"
echo -e "• To change credentials, run this script again"
echo -e "• To remove auth, restore from: /etc/nginx/sites-available/business-scraper.backup"

# Create a script to manage auth credentials
cat > /usr/local/bin/manage-scraper-auth << 'EOF'
#!/bin/bash
# Script to manage Business Scraper authentication

case "$1" in
    "add-user")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Usage: $0 add-user <username> <password>"
            exit 1
        fi
        echo "$3" | htpasswd -i /etc/nginx/.htpasswd "$2"
        systemctl reload nginx
        echo "User $2 added successfully"
        ;;
    "remove-user")
        if [ -z "$2" ]; then
            echo "Usage: $0 remove-user <username>"
            exit 1
        fi
        htpasswd -D /etc/nginx/.htpasswd "$2"
        systemctl reload nginx
        echo "User $2 removed successfully"
        ;;
    "list-users")
        echo "Current users:"
        cut -d: -f1 /etc/nginx/.htpasswd
        ;;
    "disable-auth")
        cp /etc/nginx/sites-available/business-scraper.backup /etc/nginx/sites-available/business-scraper
        systemctl reload nginx
        echo "Authentication disabled - backup configuration restored"
        ;;
    *)
        echo "Usage: $0 {add-user|remove-user|list-users|disable-auth}"
        echo "Examples:"
        echo "  $0 add-user newuser newpassword"
        echo "  $0 remove-user olduser"
        echo "  $0 list-users"
        echo "  $0 disable-auth"
        ;;
esac
EOF

chmod +x /usr/local/bin/manage-scraper-auth

echo -e "\n${GREEN}Management script created: ${NC}/usr/local/bin/manage-scraper-auth"
echo -e "Use it to add/remove users or disable auth entirely"
