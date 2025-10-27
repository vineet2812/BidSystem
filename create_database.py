"""
Script to create the initial database.xlsx structure for the Bid Management System
"""
import pandas as pd
from datetime import datetime

# Create Bids sheet structure with sample data
bids_data = {
    'bid_id': ['BID001', 'BID002', 'BID003'],
    'contract_name': [
        'IT Infrastructure Refresh',
        'Annual Facility Maintenance',
        'Security Audit & Compliance'
    ],
    'contract_description': [
        'Upgrade core networking hardware, replace end-of-life firewalls, and deploy new monitoring tooling.',
        'Provide preventive maintenance and on-call support for all corporate facilities across three sites.',
        'Conduct organisation-wide security audit, remediate findings, and certify compliance with ISO 27001.'
    ],
    'contract_value': [250000, 175000, 95000],
    'created_date': [
        '2025-09-18 09:15:23',
        '2025-08-05 14:42:10',
        '2025-07-22 11:05:47'
    ],
    'admin_name': ['Morgan Lee', 'Morgan Lee', 'Morgan Lee'],
    'status': ['Awaiting Vendor', 'Pending A1', 'Approved'],
    'selected_vendor_id': ['V003', 'V002', 'V001'],
    'selected_submission_id': ['', 'ASSIGNED', 'ASSIGNED'],
    'admin_justification': [
        '',
        'Vendor has regional technicians and fastest response commitment.',
        'Vendor completed last year’s engagement with zero findings in re-test.'
    ],
    'submission_date': ['', '2025-08-09 10:12:01', '2025-07-27 16:32:55'],
    'vendor_comment': [
        '',
        'We will dedicate a rotating crew with 24/7 coverage and monthly reports.',
        'We will run the audit in three waves and deliver remediation guidance within one week of findings.'
    ],
    'a1_status': ['Pending', 'Approved', 'Approved'],
    'a1_comment': [
        '',
        'Maintenance coverage and SLAs look solid. Recommend proceeding to A2.',
        'Thorough approach and clear timeline. Approved.'
    ],
    'a1_date': ['', '2025-08-10 09:08:17', '2025-07-29 13:20:11'],
    'a2_status': ['Pending', 'Pending', 'Approved'],
    'a2_comment': ['', '', 'Green-lighted. Release purchase order.'],
    'a2_date': ['', '', '2025-07-30 10:45:03']
}

# Create Vendors sheet structure with demo vendors
vendors_data = {
    'vendor_id': ['V001', 'V002', 'V003', 'V004'],
    'vendor_name': ['SecureSys Solutions', 'Facilities First', 'NextGen Networks', 'DataGuard Analytics'],
    'contact_email': [
        'contact@securesys.io',
        'hello@facilitiesfirst.co',
        'sales@nextgennetworks.com',
        'info@dataguardanalytics.com'
    ],
    'contact_phone': ['+1-800-555-2177', '+1-800-555-3398', '+1-888-555-9821', '+1-888-555-4104'],
    'password': ['password1', 'password2', 'password3', 'password4']
}

# Create Bid Items sheet structure
bid_items_data = {
    'item_id': [],
    'bid_id': [],
    'item_name': [],
    'item_description': [],
    'quantity': [],
    'unit': []
}

# Create Vendor Bids sheet structure (legacy support for historical records)
vendor_bids_data = {
    'submission_id': ['SUB001'],
    'bid_id': ['BID003'],
    'vendor_id': ['V001'],
    'vendor_name': ['SecureSys Solutions'],
    'bid_amount': [91000],
    'bid_description': ['Detailed breakdown of the audit programme, staffing, and remediation playbook.'],
    'submission_date': ['2025-07-25 12:15:44'],
    'is_selected': [True]
}

# Create History/Comments sheet structure
history_data = {
    'history_id': [],
    'bid_id': [],
    'action_date': [],
    'action_by': [],
    'role': [],
    'action': [],
    'comment': [],
    'previous_status': [],
    'new_status': []
}

# Create Excel file with multiple sheets
with pd.ExcelWriter('database.xlsx', engine='openpyxl') as writer:
    pd.DataFrame(bids_data).to_excel(writer, sheet_name='Bids', index=False)
    pd.DataFrame(vendors_data).to_excel(writer, sheet_name='Vendors', index=False)
    pd.DataFrame(bid_items_data).to_excel(writer, sheet_name='BidItems', index=False)
    pd.DataFrame(vendor_bids_data).to_excel(writer, sheet_name='VendorBids', index=False)
    pd.DataFrame(history_data).to_excel(writer, sheet_name='History', index=False)

print("database.xlsx created successfully!")
print("\nDatabase Structure:")
print("\n1. Bids Sheet: Stores contract/bid information and approval workflow status")
print("2. Vendors Sheet: Stores vendor contact information and login credentials")
print("3. BidItems Sheet: Stores line items for each bid")
print("4. VendorBids Sheet: Stores historical vendor submissions (legacy support)")
print("5. History Sheet: Tracks all actions and comments throughout the approval process")
