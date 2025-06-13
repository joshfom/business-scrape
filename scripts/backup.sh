#!/bin/bash
# MongoDB backup script for Docker container

BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="business_scraper_backup_$TIMESTAMP"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Perform the backup
echo "🔄 Starting MongoDB backup at $(date)"
mongodump --host mongodb:27017 --db business_scraper --out $BACKUP_DIR/$BACKUP_NAME

if [ $? -eq 0 ]; then
    echo "✅ Backup completed successfully: $BACKUP_NAME"
    
    # Compress the backup
    cd $BACKUP_DIR
    tar -czf ${BACKUP_NAME}.tar.gz $BACKUP_NAME
    rm -rf $BACKUP_NAME
    
    echo "📦 Backup compressed: ${BACKUP_NAME}.tar.gz"
    
    # Clean up old backups (keep last 7 days)
    find $BACKUP_DIR -name "business_scraper_backup_*.tar.gz" -mtime +7 -delete
    echo "🧹 Old backups cleaned up"
else
    echo "❌ Backup failed"
    exit 1
fi
