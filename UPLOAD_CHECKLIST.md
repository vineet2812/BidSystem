# Files to Upload to PythonAnywhere

## ✅ CHECKLIST - Upload These Files

### 📁 Root Directory Files (Upload to /home/YOUR_USERNAME/BidSystem/)

#### Python Application Files (REQUIRED)
- [ ] `app.py` - Main Flask application
- [ ] `db_helper.py` - Database helper functions
- [ ] `create_database.py` - Database initialization script
- [ ] `requirements.txt` - Python dependencies list
- [ ] `wsgi.py` - PythonAnywhere WSGI configuration

#### Database (OPTIONAL - can generate on server)
- [ ] `database.xlsx` - Your database with all data
  - ℹ️ Can also run `python create_database.py` on server to create fresh

#### Utility Scripts (OPTIONAL but recommended)
- [ ] `update.sh` - Quick update script
- [ ] `backup_database.sh` - Database backup script
- [ ] `check_config.py` - Configuration checker

#### Documentation (OPTIONAL - for reference)
- [ ] `DEPLOYMENT_GUIDE.md` - Complete deployment guide
- [ ] `QUICK_REFERENCE.md` - Quick command reference
- [ ] `GETTING_STARTED.md` - Getting started guide
- [ ] `README.md` - Project overview
- [ ] `.gitignore` - Git ignore rules (if using Git)

### 📁 Templates Folder (Upload to /home/YOUR_USERNAME/BidSystem/templates/)

**All 12 HTML files (REQUIRED):**
- [ ] `base.html` - Base template
- [ ] `admin_dashboard.html` - Admin dashboard
- [ ] `admin_view_bid.html` - Admin bid view
- [ ] `create_bid.html` - Create bid form
- [ ] `vendor_login.html` - Vendor login page
- [ ] `vendor_register.html` - Vendor registration
- [ ] `vendor_dashboard.html` - Vendor dashboard
- [ ] `vendor_view_bid.html` - Vendor bid view
- [ ] `a1_dashboard.html` - A1 approver dashboard
- [ ] `a1_view_bid.html` - A1 bid view
- [ ] `a2_dashboard.html` - A2 approver dashboard
- [ ] `a2_view_bid.html` - A2 bid view

---

## 🎯 MINIMUM FILES NEEDED TO RUN

If you want to upload minimal files first:

### Must Have:
1. `app.py`
2. `db_helper.py`
3. `create_database.py`
4. `requirements.txt`
5. `wsgi.py`
6. All 12 files in `templates/` folder

### Generate on Server:
- Run `python create_database.py` to create `database.xlsx`

### Add Later:
- Documentation files
- Utility scripts

---

## 📤 UPLOAD METHODS

### Method 1: PythonAnywhere Files Tab (Easiest)
1. Go to PythonAnywhere → **Files** tab
2. Click "Create new directory" → Name it `BidSystem`
3. Click into `BidSystem` folder
4. Click "Upload a file" → Select and upload each file
5. Create `templates` folder inside BidSystem
6. Upload all HTML files into templates folder

### Method 2: Zip Upload (Faster)
1. Compress your BidSystem folder to .zip on your computer
2. Go to PythonAnywhere → **Files** tab
3. Upload the .zip file
4. In Bash console: `unzip BidSystem.zip`

### Method 3: Git (Best for Updates)
1. Create Git repository with your code
2. In PythonAnywhere Bash console:
   ```bash
   cd ~
   git clone YOUR_REPO_URL BidSystem
   ```

---

## 🚫 DON'T UPLOAD THESE

**These are automatically created or not needed:**
- `__pycache__/` folder
- `.venv/` or `venv/` folder (create new on server)
- `.vscode/` or `.idea/` folders
- `*.pyc` files
- `.DS_Store` or `Thumbs.db`
- Any backup files ending in `.bak` or `~`

---

## 📝 AFTER UPLOADING

1. **Open Bash Console** and run:
   ```bash
   cd ~/BidSystem
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python create_database.py
   ```

2. **Configure Web App:**
   - Edit WSGI file (replace YOUR_USERNAME)
   - Set virtualenv path
   - Set working directory
   - Click Reload

3. **Test Your Site:**
   - Visit: `https://YOUR_USERNAME.pythonanywhere.com`

---

## 🔄 FOR FUTURE UPDATES

**Only upload the files you changed!**

Example: If you only changed `app.py`:
1. Go to Files tab → Navigate to `BidSystem/app.py`
2. Click on `app.py` → Upload your new version
3. Go to Web tab → Click Reload
4. Done!

**Pro tip:** Keep a list of files you modified to upload only those.

---

## 📊 FILE SIZE CHECK

Make sure files aren't too large:
- Python files: Usually < 1MB each ✅
- Templates: Usually < 100KB each ✅
- `database.xlsx`: Should be < 10MB for free account ✅
- Total project: Should be < 50MB for free account ✅

Your current project is well within limits!

---

## ✅ VERIFICATION

After uploading, verify in PythonAnywhere Files tab:

```
/home/YOUR_USERNAME/BidSystem/
├── app.py ✓
├── db_helper.py ✓
├── create_database.py ✓
├── requirements.txt ✓
├── wsgi.py ✓
├── database.xlsx ✓ (or create it)
└── templates/
    ├── base.html ✓
    ├── admin_dashboard.html ✓
    ├── vendor_login.html ✓
    └── ... (all 12 files) ✓
```

---

**Ready to upload? Start with GETTING_STARTED.md for step-by-step guide!** 🚀
