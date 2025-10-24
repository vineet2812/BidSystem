"""
Script to create the initial database.xlsx structure for the Bid Management System
"""
import pandas as pd
from datetime import datetime

# Create Bids sheet structure
bids_data = {
    'bid_id': [],
    'contract_name': [],
    'contract_description': [],
    'contract_value': [],
    'min_technical_capability': [],  # Minimum technical rating required (1-5)
    'created_date': [],
    'admin_name': [],
    'status': [],  # Draft, Open for Bidding, Under Review, Pending A1, Pending A2, Approved, Rejected
    'selected_vendor_id': [],
    'admin_justification': [],
    'submission_date': [],
    'a1_status': [],  # Pending, Approved, Rejected
    'a1_comment': [],
    'a1_date': [],
    'a2_status': [],  # Pending, Approved, Rejected
    'a2_comment': [],
    'a2_date': []
}

# Create Vendors sheet structure
vendors_data = {
    'vendor_id': ['V001', 'V002', 'V003'],
    'vendor_name': ['Vendor One', 'Vendor Two', 'Vendor Three'],
    'contact_email': ['vendor1@example.com', 'vendor2@example.com', 'vendor3@example.com'],
    'contact_phone': ['1234567890', '0987654321', '1122334455'],
    'technical_capability': [4, 3, 5],  # Rating 1-5
    'password': ['password1', 'password2', 'password3']  # Simple password (for demo)
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

# Create Vendor Bids sheet structure
vendor_bids_data = {
    'submission_id': [],
    'bid_id': [],
    'vendor_id': [],
    'vendor_name': [],
    'bid_amount': [],
    'bid_description': [],
    'submission_date': [],
    'is_selected': []  # TRUE/FALSE
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
print("2. Vendors Sheet: Stores vendor information with technical capability rating and login credentials")
print("3. BidItems Sheet: Stores line items for each bid")
print("4. VendorBids Sheet: Stores vendor bid submissions")
print("5. History Sheet: Tracks all actions and comments throughout the approval process")
