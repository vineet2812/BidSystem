# PythonAnywhere Deployment Guide

This guide will help you deploy the Bid Management System to PythonAnywhere and update it in the future.

## Initial Setup on PythonAnywhere

### 1. Create PythonAnywhere Account
- Go to https://www.pythonanywhere.com/
- Sign up for a free account (or paid if you need more resources)
- Note your username - you'll need it later

### 2. Upload Your Files

#### Option A: Using Git (Recommended for easy updates)
```bash
# On PythonAnywhere Bash console:
cd ~
git clone YOUR_GITHUB_REPO_URL BidSystem
cd BidSystem
```

#### Option B: Manual Upload
1. Go to PythonAnywhere Dashboard → Files
2. Create a new directory called `BidSystem`
3. Upload all files:
   - app.py
   - db_helper.py
   - create_database.py
   - database.xlsx (or run create_database.py to generate it)
   - requirements.txt
   - wsgi.py
   - templates/ folder (all HTML files)
   - static/ folder (if you have CSS/JS files)

### 3. Set Up Virtual Environment
```bash
# In PythonAnywhere Bash console:
cd ~/BidSystem
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Initialize the Database
```bash
# In PythonAnywhere Bash console (with venv activated):
cd ~/BidSystem
python create_database.py
```

### 5. Configure the Web App

1. Go to PythonAnywhere Dashboard → Web
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.10
5. Click through the wizard

#### Configure WSGI file:
1. On the Web tab, find "Code" section
2. Click on the WSGI configuration file link
3. Delete all content and replace with:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/BidSystem'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Import Flask app
from app import app as application
```

**IMPORTANT:** Replace `YOUR_USERNAME` with your actual PythonAnywhere username!

#### Set Virtual Environment:
1. On the Web tab, find "Virtualenv" section
2. Enter: `/home/YOUR_USERNAME/BidSystem/venv`
3. Click the checkmark to save

#### Set Working Directory:
1. On the Web tab, find "Code" section
2. Set "Source code" to: `/home/YOUR_USERNAME/BidSystem`
3. Set "Working directory" to: `/home/YOUR_USERNAME/BidSystem`

### 6. Configure Static Files (if needed)
On the Web tab, under "Static files" section:
- URL: `/static/`
- Directory: `/home/YOUR_USERNAME/BidSystem/static/`

### 7. Reload the Web App
- Click the green "Reload" button at the top of the Web tab
- Your app should now be live at: `https://YOUR_USERNAME.pythonanywhere.com`

---

## Updating Your Code in the Future

### Method 1: Using Git (Easiest)

1. **On your local machine:**
   ```bash
   # Make your changes
   git add .
   git commit -m "Description of changes"
   git push
   ```

2. **On PythonAnywhere Bash console:**
   ```bash
   cd ~/BidSystem
   source venv/bin/activate
   git pull
   ```

3. **If you added new packages:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Reload the web app:**
   - Go to Web tab → Click "Reload" button
   - OR in Bash console: `touch /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py`

### Method 2: Manual File Upload

1. Go to PythonAnywhere Dashboard → Files
2. Navigate to `/home/YOUR_USERNAME/BidSystem/`
3. Upload the files you changed (they will overwrite existing files)
4. If you changed Python dependencies, run in Bash console:
   ```bash
   cd ~/BidSystem
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. Go to Web tab → Click "Reload" button

---

## Important Notes

### Database Persistence
- Your `database.xlsx` file will persist on PythonAnywhere
- All bid data, vendor information, and history are stored in this file
- **Back it up regularly!** Download it from the Files tab

### File Paths
- PythonAnywhere uses Linux, so use `/` not `\\` in file paths
- All file operations use absolute paths: `/home/YOUR_USERNAME/BidSystem/database.xlsx`

### Secret Key
- Update the secret key in `app.py` for production
- Change `app.secret_key = 'your-secret-key-here'` to a random string

### Free Account Limitations
- Free accounts have limited CPU/bandwidth
- Web app goes to sleep after 3 months of inactivity
- Can't access external databases (but Excel file works fine)

### Debugging
If something goes wrong:
1. Check error logs: Web tab → Log files → Error log
2. Check server log: Web tab → Log files → Server log
3. Use Bash console to run: `python app.py` to see errors

### Database Backup Strategy
```bash
# In PythonAnywhere Bash console:
cd ~/BidSystem
cp database.xlsx database_backup_$(date +%Y%m%d).xlsx
```

Set up a scheduled task (paid accounts) to backup daily.

---

## Quick Reference Commands

### Activate Virtual Environment
```bash
cd ~/BidSystem
source venv/bin/activate
```

### Update from Git
```bash
cd ~/BidSystem
git pull
touch /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py
```

### Install New Packages
```bash
cd ~/BidSystem
source venv/bin/activate
pip install -r requirements.txt
```

### Reload Web App
```bash
touch /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py
```

### View Logs
```bash
# Error log
tail -f /var/log/YOUR_USERNAME.pythonanywhere.com.error.log

# Server log
tail -f /var/log/YOUR_USERNAME.pythonanywhere.com.server.log
```

---

## Updating Workflow (Step by Step)

1. **Make changes on your local machine**
   - Edit files in your local BidSystem folder
   - Test locally: `python app.py`

2. **Push to Git (if using Git)**
   ```bash
   git add .
   git commit -m "Your update description"
   git push
   ```

3. **Update on PythonAnywhere**
   - Open PythonAnywhere Bash console
   ```bash
   cd ~/BidSystem
   source venv/bin/activate
   git pull  # or manually upload files
   ```

4. **Reload the application**
   - Go to Web tab → Click "Reload" button
   - OR: `touch /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py`

5. **Test your changes**
   - Visit your app URL
   - Check error logs if something is wrong

---

## Security Recommendations

1. **Change the secret key in app.py:**
   ```python
   app.secret_key = 'your-very-long-random-secret-key-here'
   ```

2. **Add authentication (optional):**
   - Consider adding real login system for production
   - Current demo uses role-based sessions

3. **Backup database regularly:**
   - Download `database.xlsx` weekly
   - Store backups safely

4. **Monitor logs:**
   - Check error logs periodically
   - Look for unusual activity

---

## Troubleshooting

### "ImportError: No module named 'flask'"
- Virtual environment not activated properly
- Solution: Check virtualenv path in Web tab settings

### "Permission denied" errors
- File permissions issue
- Solution: Run `chmod 644 database.xlsx` in Bash

### Changes not showing up
- Web app not reloaded
- Solution: Click Reload button on Web tab

### Database not found
- Wrong working directory
- Solution: Verify "Working directory" in Web tab

### "502 Bad Gateway"
- Error in your code
- Solution: Check error log for details

---

## Support

- PythonAnywhere Help: https://help.pythonanywhere.com/
- PythonAnywhere Forums: https://www.pythonanywhere.com/forums/
- Your error logs: Web tab → Log files

---

## Summary

✅ **Initial Setup:** Upload files → Set up venv → Configure WSGI → Reload
✅ **Future Updates:** Change code → Push/Upload → Pull/Replace → Reload
✅ **Easy to maintain:** Git makes updates simple
✅ **Database persists:** Excel file stays on server between updates
✅ **No downtime:** Quick reload keeps your app running

Your Bid Management System is now production-ready! 🚀
