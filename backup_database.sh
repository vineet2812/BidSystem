#!/bin/bash
# Database Backup Script for PythonAnywhere
# Creates a timestamped backup of your database

echo "💾 Backing up database..."

cd ~/BidSystem

# Create backup with timestamp
BACKUP_NAME="database_backup_$(date +%Y%m%d_%H%M%S).xlsx"
cp database.xlsx "$BACKUP_NAME"

echo "✅ Backup created: $BACKUP_NAME"
echo "📁 Location: ~/BidSystem/$BACKUP_NAME"

# Optional: Keep only last 10 backups
ls -t database_backup_*.xlsx | tail -n +11 | xargs -r rm
echo "🧹 Cleaned up old backups (keeping last 10)"
