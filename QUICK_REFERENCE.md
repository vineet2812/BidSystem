# Quick Reference Card for PythonAnywhere Updates

## 🚀 UPDATING YOUR APP (3 SIMPLE STEPS)

### Step 1: Make Changes Locally
- Edit your files in the BidSystem folder
- Test locally: `python app.py`

### Step 2: Upload to PythonAnywhere
**Option A - Using Git (Recommended):**
```bash
# On your local machine:
git add .
git commit -m "Your changes description"
git push

# On PythonAnywhere Bash:
cd ~/BidSystem
./update.sh
```

**Option B - Manual Upload:**
- Go to PythonAnywhere → Files
- Navigate to `/home/YOUR_USERNAME/BidSystem/`
- Upload changed files (they will replace old ones)
- Go to Web tab → Click "Reload" button

### Step 3: Done! 
Visit your site: `https://YOUR_USERNAME.pythonanywhere.com`

---

## 📋 COMMON TASKS

### View Logs
```bash
# Error log
tail -f /var/log/YOUR_USERNAME.pythonanywhere.com.error.log

# Or use PythonAnywhere Web tab → Log files
```

### Backup Database
```bash
cd ~/BidSystem
./backup_database.sh
```

### Reload App After Changes
```bash
touch /var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py
# OR just click "Reload" on Web tab
```

### Install New Python Package
```bash
cd ~/BidSystem
source venv/bin/activate
pip install package_name
pip freeze > requirements.txt  # Update requirements
```

---

## 🔧 CONFIGURATION FILES

### Important File Locations on PythonAnywhere:

| File | Location | Purpose |
|------|----------|---------|
| Application | `/home/YOUR_USERNAME/BidSystem/` | Your code |
| Database | `/home/YOUR_USERNAME/BidSystem/database.xlsx` | All data |
| WSGI | `/var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py` | Web config |
| Venv | `/home/YOUR_USERNAME/BidSystem/venv/` | Python packages |
| Error Log | `/var/log/YOUR_USERNAME.pythonanywhere.com.error.log` | Errors |

---

## ⚠️ TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Changes not showing | Click "Reload" on Web tab |
| Import errors | Check venv path in Web tab settings |
| 502 error | Check error log for Python errors |
| Database not found | Verify working directory in Web tab |

---

## 📞 QUICK HELP

- PythonAnywhere Help: https://help.pythonanywhere.com/
- Your app URL: `https://YOUR_USERNAME.pythonanywhere.com`
- Full guide: See DEPLOYMENT_GUIDE.md

---

## ✅ CHECKLIST FOR FIRST DEPLOYMENT

- [ ] Sign up for PythonAnywhere account
- [ ] Upload all files to `/home/YOUR_USERNAME/BidSystem/`
- [ ] Create virtual environment: `python3.10 -m venv venv`
- [ ] Install packages: `pip install -r requirements.txt`
- [ ] Run: `python create_database.py`
- [ ] Configure WSGI file (replace YOUR_USERNAME)
- [ ] Set virtualenv path in Web tab
- [ ] Set working directory in Web tab
- [ ] Click "Reload" button
- [ ] Test your app!

---

**Remember:** Replace `YOUR_USERNAME` with your actual PythonAnywhere username everywhere!
