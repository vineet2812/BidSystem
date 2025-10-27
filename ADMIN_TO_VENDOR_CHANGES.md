# Admin to Vendor Renaming - Summary

## Date: October 27, 2025

## Overview
Complete system-wide renaming from "Admin" to "Vendor" terminology throughout the Bid Management System.
Note: This is the second renaming (first was Vendor→Buyer, now Admin→Vendor).

## Current System Roles
- **Vendor** (was Admin) - Creates bids, assigns buyers
- **Buyer** (was Vendor) - Responds to bids
- **A1 Approver** - First level approval
- **A2 Approver** - Final approval

## Changes Made

### 1. Database (database.xlsx)

**Column Renaming in Bids sheet:**
- `admin_name` → `vendor_name`
- `admin_justification` → `vendor_justification`

**Data Updates:**
- History sheet: All "Admin" roles updated to "Vendor" (4 entries updated)

### 2. Python Files

#### db_helper.py
**Backup Created:** `db_helper.py.backup2`

**Variable/Column References:**
- All occurrences of `admin_name` → `vendor_name`
- All occurrences of `admin_justification` → `vendor_justification`

#### app.py
**Backup Created:** `app.py.backup2`

**Routes Renamed:**
- `/admin/login` → `/vendor/login`
- `/admin/logout` → `/vendor/logout`
- `/admin/dashboard` → `/vendor/dashboard`
- `/admin/create_bid` → `/vendor/create_bid`
- `/admin/view_bid/<bid_id>` → `/vendor/view_bid/<bid_id>`

**Function Names:**
- `admin_login()` → `vendor_login()`
- `admin_logout()` → `vendor_logout()`
- `admin_dashboard()` → `vendor_dashboard()`
- `admin_view_bid()` → `vendor_view_bid()`
- `create_bid()` → kept the same

**Session Variables:**
- `session['admin_name']` → `session['vendor_name']`
- `session['role'] = 'Admin'` → `session['role'] = 'Vendor'`

**All Variable Names:**
- `admin_name` → `vendor_name`
- `admin_justification` → `vendor_justification`

### 3. Template Files

**Files Renamed:**
- `admin_dashboard.html` → `vendor_dashboard.html`
- `admin_view_bid.html` → `vendor_view_bid.html`

**All Template Files Updated** (backups created with .backup2 extension):
- `vendor_dashboard.html` (was admin_dashboard.html)
- `vendor_view_bid.html` (was admin_view_bid.html)
- `a1_view_bid.html`
- `a2_view_bid.html`
- `create_bid.html`
- `base.html`

**Content Updates:**
- URL functions: `url_for('admin_*')` → `url_for('vendor_*')`
- Session variables: `session.admin_*` → `session.vendor_*`
- Form fields: `id="admin_*"`, `name="admin_*"` → vendor equivalents
- Object properties: `bid.admin_name`, `bid.admin_justification` → vendor equivalents
- Display text: All "Admin" → "Vendor" throughout
- Page titles: "Admin Dashboard" → "Vendor Dashboard", etc.
- Special cases: "Admin Notes" → "Vendor Notes", "Admin Justification" → "Vendor Justification"

### 4. PDF Generation (app.py)
- Section title: "ADMIN NOTES" → "VENDOR NOTES"
- Field labels updated
- Variable names updated

## Complete Role Transformation Summary

### Original System:
- Admin - Creates bids
- Vendor - Responds to bids
- A1 Approver - First approval
- A2 Approver - Final approval

### After First Renaming (Vendor→Buyer):
- Admin - Creates bids
- Buyer - Responds to bids
- A1 Approver - First approval
- A2 Approver - Final approval

### Current System (Admin→Vendor):
- **Vendor** - Creates bids, assigns buyers
- **Buyer** - Responds to bids
- **A1 Approver** - First level approval
- **A2 Approver** - Final approval

## Testing Checklist

- [ ] Vendor login works correctly
- [ ] Vendor can create bids
- [ ] Vendor can assign buyers to bids
- [ ] Vendor dashboard displays correctly
- [ ] Vendor can view bids
- [ ] Buyers can still access their functionality
- [ ] A1 and A2 approvers see vendor information correctly
- [ ] History shows "Vendor" role correctly (for bid creators)
- [ ] PDF generation includes correct vendor terminology
- [ ] All database operations work with renamed columns

## Rollback Instructions

If you need to revert changes:

1. **Database:** Use Excel to manually rename columns back
2. **Python Files:** Replace files with `.backup2` versions:
   - `db_helper.py.backup2` → `db_helper.py`
   - `app.py.backup2` → `app.py`
3. **Template Files:** Replace all template files with their `.backup2` versions
4. **Rename vendor template files back to admin:**
   ```
   Move-Item vendor_dashboard.html admin_dashboard.html
   Move-Item vendor_view_bid.html admin_view_bid.html
   ```

## Notes

- All functionality remains exactly the same
- Only terminology changed from "Admin" to "Vendor"
- Database structure preserved
- All existing data preserved and updated
- Backups created for all modified files
- This change stacks on top of the previous Vendor→Buyer renaming
