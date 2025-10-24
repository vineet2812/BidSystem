# Bid Management System

A comprehensive Flask-based web application for managing contract bids with a multi-level approval workflow.

## Features

- **Admin Role**: Create bids, review vendor submissions, select winning vendors, and submit for approval
- **Vendor Role**: View open bids and submit proposals
- **A1 Approver Role**: Review and approve/reject vendor selections
- **A2 Approver Role**: Final approval authority with PDF generation
- **Excel Database**: Uses Excel file (database.xlsx) as the backend database
- **Complete Workflow Tracking**: Full audit trail of all actions and comments
- **PDF Generation**: Download approval documents for approved bids

## System Workflow

1. **Admin** creates a new bid contract
2. **Vendors** submit their bids with pricing and proposals
3. **Admin** reviews vendor submissions, selects winning vendor with justification, and submits for A1 approval
4. **A1 Approver** reviews and either:
   - Approves → sends to A2 Approver
   - Rejects → sends back to Admin
5. **A2 Approver** (final authority) either:
   - Approves → bid is finalized and PDF becomes available
   - Rejects → sends back to A1 Approver

## Database Structure

The system uses `database.xlsx` with 4 sheets:

### 1. Bids Sheet
Stores all bid/contract information and approval status
- bid_id, contract_name, contract_description, contract_value
- created_date, admin_name, status
- selected_vendor_id, admin_justification, submission_date
- a1_status, a1_comment, a1_date
- a2_status, a2_comment, a2_date

### 2. Vendors Sheet
Stores vendor information
- vendor_id, vendor_name, contact_email, contact_phone

### 3. VendorBids Sheet
Stores vendor bid submissions
- submission_id, bid_id, vendor_id, vendor_name
- bid_amount, bid_description, submission_date, is_selected

### 4. History Sheet
Complete audit trail of all actions
- history_id, bid_id, action_date, action_by, role
- action, comment, previous_status, new_status

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Step 1: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 2: Create Database

Run the database creation script:

```powershell
python create_database.py
```

This will create `database.xlsx` with the proper structure and sample vendors.

### Step 3: Run the Application

```powershell
python app.py
```

The application will start on `http://localhost:5000`

## Usage

### Role Switching
- Use the buttons at the top of every page to switch between roles
- No login/password required (as per requirements)
- Roles: Admin, Vendor, A1 Approver, A2 Approver

### Admin Workflow
1. Click "Create New Bid" to create a contract
2. View bids from dashboard
3. Wait for vendor submissions
4. Click "View" on a bid to see vendor submissions
5. Select winning vendor and provide justification
6. Click "Submit for A1 Approval"

### Vendor Workflow
1. Switch to Vendor role
2. View open bids on dashboard
3. Click "View & Submit Bid"
4. Select your company, enter bid amount and description
5. Click "Submit Bid"

### A1 Approver Workflow
1. Switch to A1 Approver role
2. View pending bids on dashboard
3. Click "Review" to see bid details
4. Review contract, selected vendor, and admin justification
5. Either approve (sends to A2) or reject (sends to Admin)

### A2 Approver Workflow
1. Switch to A2 Approver role
2. View pending bids on dashboard
3. Click "Review" to see all details including A1 approval
4. Either approve (finalizes bid) or reject (sends back to A1)

### PDF Download
- Available for approved bids only
- Accessible from Admin dashboard or bid detail page
- Contains complete bid information, approval trail, and comments

## File Structure

```
BidSystem/
│
├── app.py                      # Main Flask application
├── db_helper.py                # Excel database operations
├── create_database.py          # Database initialization script
├── requirements.txt            # Python dependencies
├── database.xlsx              # Excel database (created by script)
│
└── templates/                 # HTML templates
    ├── base.html             # Base template with role switcher
    ├── admin_dashboard.html  # Admin dashboard
    ├── create_bid.html       # Create new bid form
    ├── admin_view_bid.html   # Admin bid detail view
    ├── vendor_dashboard.html # Vendor dashboard
    ├── vendor_view_bid.html  # Vendor bid submission form
    ├── a1_dashboard.html     # A1 Approver dashboard
    ├── a1_view_bid.html      # A1 review and approval page
    ├── a2_dashboard.html     # A2 Approver dashboard
    └── a2_view_bid.html      # A2 final review and approval page
```

## Status Definitions

- **Open for Bidding**: Vendors can submit bids
- **Under Review**: Admin reviewing vendor submissions or A1 rejected
- **Pending A1**: Waiting for A1 Approver review
- **Pending A2**: Waiting for A2 Approver review
- **Approved**: Final approval completed
- **Rejected**: Rejected by approvers

## Future Enhancements

The system is designed to be extensible. Possible additions:
- User authentication and login system
- Email notifications for approvals/rejections
- More detailed vendor information
- Bid deadline management
- Multiple currency support
- Advanced reporting and analytics
- Document attachments
- Multi-language support

## Technical Details

- **Framework**: Flask 2.3.3
- **Database**: Excel (via pandas and openpyxl)
- **PDF Generation**: ReportLab
- **UI**: Bootstrap 5
- **Icons**: Bootstrap Icons

## Troubleshooting

**Issue**: Module not found errors
**Solution**: Ensure all packages are installed: `pip install -r requirements.txt`

**Issue**: Database.xlsx not found
**Solution**: Run `python create_database.py` first

**Issue**: Permission denied when writing to Excel
**Solution**: Close database.xlsx if it's open in Excel

**Issue**: Changes not reflected
**Solution**: Refresh the page or restart the Flask application

## Support

For issues or questions, check:
1. All dependencies are installed
2. database.xlsx exists and is not open in Excel
3. Python version is 3.8 or higher
4. Flask app is running on port 5000

## License

This project is created for internal use and can be modified as needed.
