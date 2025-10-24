# Quick Start Guide - Bid Management System

## Installation (3 Simple Steps)

### Step 1: Install Dependencies
Open PowerShell in the project directory and run:
```powershell
pip install -r requirements.txt
```

### Step 2: Create Database
The database has already been created! (`database.xlsx` exists)

If you need to recreate it:
```powershell
python create_database.py
```

### Step 3: Run the Application
```powershell
python app.py
```

Then open your browser to: **http://localhost:5000**

## First Time Usage

1. **Start as Admin** (default role)
   - Click "Create New Bid"
   - Enter contract details (name, description, value)
   - Submit

2. **Switch to Vendor** (use role buttons at top)
   - View open bids
   - Click "View & Submit Bid"
   - Select your company (V001, V002, or V003)
   - Enter bid amount and description
   - Submit

3. **Back to Admin**
   - View your bid
   - Review vendor submissions
   - Select winning vendor
   - Add justification
   - Click "Submit for A1 Approval"

4. **Switch to A1 Approver**
   - Review the pending bid
   - Add comment
   - Approve (sends to A2) or Reject (sends back to Admin)

5. **Switch to A2 Approver**
   - Final review
   - Add comment
   - Approve (finalizes) or Reject (sends to A1)

6. **View Approved Bid**
   - Switch to any role
   - From dashboard, click "PDF" button
   - Download complete approval document

## Role Buttons (Top of Every Page)

- **Admin** - Create bids, select vendors
- **Vendor** - Submit bids
- **A1 Approver** - First approval level
- **A2 Approver** - Final approval level

## Key Features

✅ Excel-based database (easy to view/edit)
✅ Complete workflow tracking
✅ Comment/history trail
✅ PDF generation for approved bids
✅ Simple role switching (no login needed)
✅ Bootstrap UI

## Files Created

- `app.py` - Main Flask application
- `db_helper.py` - Database operations
- `create_database.py` - Database setup script
- `database.xlsx` - Excel database
- `requirements.txt` - Python dependencies
- `templates/` - 10 HTML templates
- `README.md` - Full documentation
- `QUICKSTART.md` - This file

## Troubleshooting

**Port 5000 already in use?**
Edit `app.py`, last line, change port:
```python
app.run(debug=True, port=5001)
```

**Database locked?**
Close `database.xlsx` in Excel before running the app.

**Changes not showing?**
Press Ctrl+Shift+R in browser to force refresh.

## What's Next?

After testing, you can:
- Add more vendors in `database.xlsx` > Vendors sheet
- Modify templates for custom branding
- Add more fields to database as needed
- Implement login system
- Add email notifications
- Export to real database (MySQL, PostgreSQL)

Enjoy your Bid Management System! 🎉
