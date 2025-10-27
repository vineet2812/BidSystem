"""
Script to create an empty database.xlsx structure for the Bid Management System
Creates all necessary sheets with proper column structure but no data
"""
import pandas as pd

# Create empty Bids sheet structure
bids_data = {
    'bid_id': [],
    'contract_name': [],
    'contract_description': [],
    'contract_value': [],
    'created_date': [],
    'vendor_name': [],
    'status': [],
    'selected_buyer_id': [],
    'selected_submission_id': [],
    'vendor_justification': [],
    'submission_date': [],
    'buyer_comment': [],
    'a1_status': [],
    'a1_comment': [],
    'a1_date': [],
    'a2_status': [],
    'a2_comment': [],
    'a2_date': []
}

# Create empty Buyers sheet structure
buyers_data = {
    'buyer_id': [],
    'buyer_name': [],
    'contact_email': [],
    'contact_phone': [],
    'password': []
}

# Create empty Bid Items sheet structure
bid_items_data = {
    'item_id': [],
    'bid_id': [],
    'item_name': [],
    'item_description': [],
    'quantity': [],
    'unit': []
}

# Create empty Buyer Bids sheet structure
buyer_bids_data = {
    'submission_id': [],
    'bid_id': [],
    'buyer_id': [],
    'buyer_name': [],
    'bid_amount': [],
    'bid_description': [],
    'submission_date': [],
    'is_selected': []
}

# Create empty History/Comments sheet structure
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

# Create Excel file with multiple empty sheets
with pd.ExcelWriter('database.xlsx', engine='openpyxl') as writer:
    pd.DataFrame(bids_data).to_excel(writer, sheet_name='Bids', index=False)
    pd.DataFrame(buyers_data).to_excel(writer, sheet_name='Buyers', index=False)
    pd.DataFrame(bid_items_data).to_excel(writer, sheet_name='Items', index=False)
    pd.DataFrame(buyer_bids_data).to_excel(writer, sheet_name='BuyerBids', index=False)
    pd.DataFrame(history_data).to_excel(writer, sheet_name='History', index=False)

print("✓ Empty database.xlsx created successfully!")
print("\nDatabase Structure:")
print("\n1. Bids Sheet: Stores contract/bid information and approval workflow status")
print("2. Buyers Sheet: Stores buyer contact information and login credentials")
print("3. Items Sheet: Stores line items for each bid")
print("4. BuyerBids Sheet: Stores buyer submissions for bids")
print("5. History Sheet: Tracks all actions and comments throughout the approval process")
print("\nAll sheets created with proper column structure but no data.")
print("You can now populate the database with your own data.")
