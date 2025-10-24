#!/bin/bash
# Quick Update Script for PythonAnywhere
# Run this after making changes to update your live site

echo "🚀 Updating Bid Management System on PythonAnywhere..."

# Navigate to project directory
cd ~/BidSystem

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Pull latest changes from Git (if using Git)
echo "📥 Pulling latest changes..."
git pull

# Install/update dependencies
echo "🔧 Installing dependencies..."
pip install -r requirements.txt

# Reload the web app
echo "♻️  Reloading web application..."
touch /var/www/${USER}_pythonanywhere_com_wsgi.py

echo "✅ Update complete! Your site should be live in a few seconds."
echo "🌐 Visit: https://${USER}.pythonanywhere.com"
echo ""
echo "If you see errors, check the logs:"
echo "  Error log: tail -f /var/log/${USER}.pythonanywhere.com.error.log"
