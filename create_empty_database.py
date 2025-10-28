"""
Script to create a database.xlsx structure for the Bid Management System
Creates all necessary sheets with sample data including buyers, bidders, and bid comparison
"""
import pandas as pd
from datetime import datetime

# Create Bids sheet with sample data
bids_data = {
    'bid_id': ['BID001'],
    'contract_name': ['Office Furniture Supply Contract'],
    'contract_description': ['Supply and installation of office furniture for new branch office'],
    'contract_value': [250000],
    'created_date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
    'admin_name': ['vendor1'],
    'status': ['Awaiting Buyer'],
    'selected_vendor_id': [''],
    'selected_submission_id': [''],
    'admin_justification': [''],
    'submission_date': [''],
    'vendor_comment': ['Initial bid created for office furniture requirements'],
    'selected_buyer_id': ['V001'],
    'a1_status': ['Pending'],
    'a1_comment': [''],
    'a1_date': [''],
    'a2_status': ['Pending'],
    'a2_comment': [''],
    'a2_date': ['']
}

# Create Vendors sheet with sample data (1 vendor who created the bid)
vendors_data = {
    'vendor_id': ['vendor1'],
    'vendor_name': ['ABC Procurement Services'],
    'contact_email': ['vendor1@abc.com'],
    'contact_phone': ['+1-555-0101'],
    'password': ['vendor123']
}

# Create Buyers sheet with 2 sample buyers
buyers_data = {
    'buyer_id': ['V001', 'V002'],
    'buyer_name': ['John Smith - Procurement Manager', 'Sarah Johnson - Supply Chain Lead'],
    'contact_email': ['john.smith@company.com', 'sarah.johnson@company.com'],
    'contact_phone': ['+1-555-0301', '+1-555-0302'],
    'password': ['buyer123', 'buyer456']
}

# Create Bid Items sheet with 2 sample items
bid_items_data = {
    'item_id': [1, 2],
    'bid_id': ['BID001', 'BID001'],
    'item_name': ['Executive Office Desk', 'Ergonomic Office Chair'],
    'item_description': ['Solid wood executive desk with drawers, 72"x36"', 'Adjustable height ergonomic chair with lumbar support'],
    'quantity': [25, 50],
    'unit': ['pieces', 'pieces']
}

# Create empty Vendor Bids sheet structure (legacy support)
vendor_bids_data = {
    'submission_id': [],
    'bid_id': [],
    'vendor_id': [],
    'vendor_name': [],
    'bid_amount': [],
    'bid_description': [],
    'submission_date': [],
    'is_selected': []
}

# Create empty Buyer Bids sheet structure (legacy support)
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

# Create History sheet with bid creation record
history_data = {
    'history_id': [1, 2],
    'bid_id': ['BID001', 'BID001'],
    'action_date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
    'action_by': ['vendor1', 'vendor1'],
    'role': ['Vendor', 'Vendor'],
    'action': ['Created Bid', 'Assigned Buyer'],
    'comment': ['Bid created with 2 items for office furniture supply', 'Assigned buyer John Smith - Procurement Manager (V001)'],
    'previous_status': ['', 'Open'],
    'new_status': ['Open', 'Awaiting Buyer']
}

# Create Bidders sheet with 2 sample bidders (buyers)
bidders_data = {
    'bidder_id': ['bidder1', 'bidder2'],
    'bidder_name': ['Premium Furniture Co.', 'Quality Office Solutions'],
    'contact_email': ['bidder1@premiumfurniture.com', 'bidder2@qualityoffice.com'],
    'contact_phone': ['+1-555-0201', '+1-555-0202'],
    'password': ['bidder123', 'bidder456']
}

# Create BidderItemBids sheet with bids from both bidders for both items
bidder_item_bids_data = {
    'bidder_bid_id': [1, 2, 3, 4],
    'bid_id': ['BID001', 'BID001', 'BID001', 'BID001'],
    'bidder_id': ['bidder1', 'bidder1', 'bidder2', 'bidder2'],
    'item_id': [1, 2, 1, 2],
    'unit_rate': [850.00, 320.00, 790.00, 295.00],
    'submission_date': [
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ]
}

# Create Bid Comparison sheet for PDF generation
bid_comparison_data = {
    'bid_id': ['BID001', 'BID001'],
    'item_id': [1, 2],
    'item_name': ['Executive Office Desk', 'Ergonomic Office Chair'],
    'quantity': [25, 50],
    'unit': ['pieces', 'pieces'],
    'bidder1_name': ['Premium Furniture Co.', 'Premium Furniture Co.'],
    'bidder1_rate': [850.00, 320.00],
    'bidder1_total': [21250.00, 16000.00],
    'bidder2_name': ['Quality Office Solutions', 'Quality Office Solutions'],
    'bidder2_rate': [790.00, 295.00],
    'bidder2_total': [19750.00, 14750.00],
    'lowest_bidder': ['bidder2', 'bidder2'],
    'savings': [1500.00, 1250.00]
}

# Create Excel file with multiple sheets including sample data
with pd.ExcelWriter('database.xlsx', engine='openpyxl') as writer:
    pd.DataFrame(bids_data).to_excel(writer, sheet_name='Bids', index=False)
    pd.DataFrame(vendors_data).to_excel(writer, sheet_name='Vendors', index=False)
    pd.DataFrame(buyers_data).to_excel(writer, sheet_name='Buyers', index=False)
    pd.DataFrame(bid_items_data).to_excel(writer, sheet_name='BidItems', index=False)
    pd.DataFrame(vendor_bids_data).to_excel(writer, sheet_name='VendorBids', index=False)
    pd.DataFrame(buyer_bids_data).to_excel(writer, sheet_name='BuyerBids', index=False)
    pd.DataFrame(history_data).to_excel(writer, sheet_name='History', index=False)
    pd.DataFrame(bidders_data).to_excel(writer, sheet_name='Bidders', index=False)
    pd.DataFrame(bidder_item_bids_data).to_excel(writer, sheet_name='BidderItemBids', index=False)
    pd.DataFrame(bid_comparison_data).to_excel(writer, sheet_name='BidComparison', index=False)

print("✓ Database.xlsx created successfully with sample data!")
print("\nDatabase Structure:")
print("\n1. Bids Sheet: Contains 1 sample bid for Office Furniture Supply")
print("2. Vendors Sheet: Contains 1 vendor who created the bid")
print("3. Buyers Sheet: Contains 2 buyers (procurement personnel)")
print("4. BidItems Sheet: Contains 2 items (Office Desk & Office Chair)")
print("5. VendorBids Sheet: Empty (legacy support)")
print("6. History Sheet: Contains bid creation and buyer assignment records")
print("7. Bidders Sheet: Contains 2 bidders (companies submitting quotes)")
print("8. BidderItemBids Sheet: Contains bid submissions from both bidders for both items")
print("9. BidComparison Sheet: Contains comparison data for PDF generation")
print("\n" + "="*80)
print("SAMPLE DATA SUMMARY:")
print("="*80)
print("\n📋 BID: BID001 - Office Furniture Supply Contract")
print("   Created by: ABC Procurement Services (vendor1)")
print("   Assigned to: John Smith - Procurement Manager (V001)")
print("   Status: Awaiting Buyer | A1 Status: Pending | A2 Status: Pending")
print("\n📦 ITEMS:")
print("   Item 1: Executive Office Desk (25 pieces)")
print("   Item 2: Ergonomic Office Chair (50 pieces)")
print("\n� BUYERS (Procurement Personnel):")
print("   Buyer 1: John Smith - Procurement Manager (V001) ✓ ASSIGNED")
print("   Buyer 2: Sarah Johnson - Supply Chain Lead (V002)")
print("\n🏢 BIDDERS (Companies Submitting Quotes):")
print("   Bidder 1: Premium Furniture Co. (bidder1@premiumfurniture.com)")
print("   Bidder 2: Quality Office Solutions (bidder2@qualityoffice.com)")
print("\n💰 BID SUBMISSIONS:")
print("   Item 1 - Executive Office Desk:")
print("      • Premium Furniture Co.: $850/unit × 25 = $21,250")
print("      • Quality Office Solutions: $790/unit × 25 = $19,750 ✓ LOWEST")
print("      • Savings: $1,500")
print("\n   Item 2 - Ergonomic Office Chair:")
print("      • Premium Furniture Co.: $320/unit × 50 = $16,000")
print("      • Quality Office Solutions: $295/unit × 50 = $14,750 ✓ LOWEST")
print("      • Savings: $1,250")
print("\n   TOTAL SAVINGS with Quality Office Solutions: $2,750")
print("\n" + "="*80)
print("\n📊 BidComparison sheet ready for PDF generation!")
print("\nLogin Credentials:")
print("   Vendor: vendor1 / vendor123")
print("   Buyer 1: V001 / buyer123")
print("   Buyer 2: V002 / buyer456")
print("   Bidder 1: bidder1 / bidder123")
print("   Bidder 2: bidder2 / bidder456")
print("\nYou can now run the application and test the complete workflow!")

