"""
Excel Database Helper Functions for Bid Management System
"""
import pandas as pd
from datetime import datetime
import os

DATABASE_FILE = 'database.xlsx'

def read_sheet(sheet_name):
    """Read data from a specific sheet"""
    try:
        df = pd.read_excel(DATABASE_FILE, sheet_name=sheet_name)
        return df
    except Exception as e:
        print(f"Error reading {sheet_name}: {e}")
        return pd.DataFrame()

def write_sheet(df, sheet_name):
    """Write data to a specific sheet"""
    try:
        # Read all sheets
        with pd.ExcelFile(DATABASE_FILE) as xls:
            sheets = {sheet: pd.read_excel(xls, sheet) for sheet in xls.sheet_names}
        
        # Update the specific sheet
        sheets[sheet_name] = df
        
        # Write all sheets back
        with pd.ExcelWriter(DATABASE_FILE, engine='openpyxl') as writer:
            for sheet, data in sheets.items():
                data.to_excel(writer, sheet_name=sheet, index=False)
        return True
    except Exception as e:
        print(f"Error writing to {sheet_name}: {e}")
        return False

def get_next_bid_id():
    """Generate next bid ID"""
    bids_df = read_sheet('Bids')
    if bids_df.empty or len(bids_df) == 0:
        return 'BID001'
    
    # Extract numbers from existing IDs and find max
    existing_ids = bids_df['bid_id'].dropna().tolist()
    if not existing_ids:
        return 'BID001'
    
    max_num = max([int(bid_id.replace('BID', '')) for bid_id in existing_ids if isinstance(bid_id, str)])
    return f'BID{str(max_num + 1).zfill(3)}'

def get_next_submission_id():
    """Generate next submission ID"""
    vendor_bids_df = read_sheet('VendorBids')
    if vendor_bids_df.empty or len(vendor_bids_df) == 0:
        return 'SUB001'
    
    existing_ids = vendor_bids_df['submission_id'].dropna().tolist()
    if not existing_ids:
        return 'SUB001'
    
    max_num = max([int(sub_id.replace('SUB', '')) for sub_id in existing_ids if isinstance(sub_id, str)])
    return f'SUB{str(max_num + 1).zfill(3)}'

def get_next_history_id():
    """Generate next history ID"""
    history_df = read_sheet('History')
    if history_df.empty or len(history_df) == 0:
        return 1
    
    return history_df['history_id'].max() + 1

def get_next_vendor_id():
    """Generate next vendor ID"""
    vendors_df = read_sheet('Vendors')
    if vendors_df.empty or len(vendors_df) == 0:
        return 'V001'
    
    existing_ids = vendors_df['vendor_id'].dropna().tolist()
    if not existing_ids:
        return 'V001'
    
    max_num = max([int(v_id.replace('V', '')) for v_id in existing_ids if isinstance(v_id, str)])
    return f'V{str(max_num + 1).zfill(3)}'

def get_next_item_id():
    """Generate next item ID"""
    items_df = read_sheet('BidItems')
    if items_df.empty or len(items_df) == 0:
        return 'ITEM001'
    
    existing_ids = items_df['item_id'].dropna().tolist()
    if not existing_ids:
        return 'ITEM001'
    
    max_num = max([int(item_id.replace('ITEM', '')) for item_id in existing_ids if isinstance(item_id, str)])
    return f'ITEM{str(max_num + 1).zfill(3)}'

def create_bid(contract_name, contract_description, contract_value, admin_name, min_technical_capability=0):
    """Create a new bid"""
    bids_df = read_sheet('Bids')
    
    new_bid = {
        'bid_id': get_next_bid_id(),
        'contract_name': contract_name,
        'contract_description': contract_description,
        'contract_value': contract_value,
        'min_technical_capability': min_technical_capability,
        'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'admin_name': admin_name,
        'status': 'Open for Bidding',
        'selected_vendor_id': None,
        'admin_justification': None,
        'submission_date': None,
        'a1_status': 'Pending',
        'a1_comment': None,
        'a1_date': None,
        'a2_status': 'Pending',
        'a2_comment': None,
        'a2_date': None
    }
    
    bids_df = pd.concat([bids_df, pd.DataFrame([new_bid])], ignore_index=True)
    write_sheet(bids_df, 'Bids')
    
    # Add to history
    add_history(new_bid['bid_id'], admin_name, 'Admin', 'Created Bid', 
                f"Created new bid: {contract_name}", None, 'Open for Bidding')
    
    return new_bid['bid_id']

def submit_vendor_bid(bid_id, vendor_id, vendor_name, bid_amount, bid_description):
    """Submit a vendor bid"""
    vendor_bids_df = read_sheet('VendorBids')
    
    new_submission = {
        'submission_id': get_next_submission_id(),
        'bid_id': bid_id,
        'vendor_id': vendor_id,
        'vendor_name': vendor_name,
        'bid_amount': bid_amount,
        'bid_description': bid_description,
        'submission_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'is_selected': False
    }
    
    vendor_bids_df = pd.concat([vendor_bids_df, pd.DataFrame([new_submission])], ignore_index=True)
    write_sheet(vendor_bids_df, 'VendorBids')
    
    # Add to history
    add_history(bid_id, vendor_name, 'Vendor', 'Submitted Bid', 
                f"Bid Amount: {bid_amount}", None, None)
    
    return new_submission['submission_id']

def select_vendor_and_submit_for_approval(bid_id, vendor_id, justification, admin_name):
    """Admin selects vendor and submits for A1 approval"""
    bids_df = read_sheet('Bids')
    vendor_bids_df = read_sheet('VendorBids')
    
    # Get current status for history
    current_status = bids_df.loc[bids_df['bid_id'] == bid_id, 'status'].values[0]
    
    # Update bid status and reset approval statuses
    bids_df.loc[bids_df['bid_id'] == bid_id, 'selected_vendor_id'] = vendor_id
    bids_df.loc[bids_df['bid_id'] == bid_id, 'admin_justification'] = justification
    bids_df.loc[bids_df['bid_id'] == bid_id, 'submission_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    bids_df.loc[bids_df['bid_id'] == bid_id, 'status'] = 'Pending A1'
    
    # Reset A1 and A2 approval statuses for resubmission
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_status'] = 'Pending'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_comment'] = ''
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_date'] = ''
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_status'] = 'Pending'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_comment'] = ''
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_date'] = ''
    
    write_sheet(bids_df, 'Bids')
    
    # Reset all vendor selections first, then mark the selected one
    vendor_bids_df.loc[vendor_bids_df['bid_id'] == bid_id, 'is_selected'] = False
    vendor_bids_df.loc[(vendor_bids_df['bid_id'] == bid_id) & 
                       (vendor_bids_df['vendor_id'] == vendor_id), 'is_selected'] = True
    write_sheet(vendor_bids_df, 'VendorBids')
    
    # Add to history
    action_text = 'Resubmitted for A1 Approval' if current_status == 'Under Review' else 'Selected Vendor & Submitted for A1 Approval'
    add_history(bid_id, admin_name, 'Admin', action_text, 
                f"Selected Vendor: {vendor_id}, Justification: {justification}", 
                current_status, 'Pending A1')

def a1_approve(bid_id, comment, approver_name):
    """A1 Approver approves the bid"""
    bids_df = read_sheet('Bids')
    
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_status'] = 'Approved'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_comment'] = comment
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    bids_df.loc[bids_df['bid_id'] == bid_id, 'status'] = 'Pending A2'
    
    write_sheet(bids_df, 'Bids')
    
    # Add to history
    add_history(bid_id, approver_name, 'A1 Approver', 'Approved', comment, 'Pending A1', 'Pending A2')

def a1_reject(bid_id, comment, approver_name):
    """A1 Approver rejects the bid"""
    bids_df = read_sheet('Bids')
    
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_status'] = 'Rejected'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_comment'] = comment
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    bids_df.loc[bids_df['bid_id'] == bid_id, 'status'] = 'Under Review'
    
    write_sheet(bids_df, 'Bids')
    
    # Add to history
    add_history(bid_id, approver_name, 'A1 Approver', 'Rejected', comment, 'Pending A1', 'Under Review')

def a2_approve(bid_id, comment, approver_name):
    """A2 Approver approves the bid"""
    bids_df = read_sheet('Bids')
    
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_status'] = 'Approved'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_comment'] = comment
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    bids_df.loc[bids_df['bid_id'] == bid_id, 'status'] = 'Approved'
    
    write_sheet(bids_df, 'Bids')
    
    # Add to history
    add_history(bid_id, approver_name, 'A2 Approver', 'Approved - Final', comment, 'Pending A2', 'Approved')

def a2_reject(bid_id, comment, approver_name):
    """A2 Approver rejects the bid"""
    bids_df = read_sheet('Bids')
    
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_status'] = 'Rejected'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_comment'] = comment
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    bids_df.loc[bids_df['bid_id'] == bid_id, 'status'] = 'Pending A1'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_status'] = 'Pending'
    
    write_sheet(bids_df, 'Bids')
    
    # Add to history
    add_history(bid_id, approver_name, 'A2 Approver', 'Rejected - Sent back to A1', comment, 'Pending A2', 'Pending A1')

def add_history(bid_id, action_by, role, action, comment, previous_status, new_status):
    """Add entry to history"""
    history_df = read_sheet('History')
    
    new_history = {
        'history_id': get_next_history_id(),
        'bid_id': bid_id,
        'action_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'action_by': action_by,
        'role': role,
        'action': action,
        'comment': comment,
        'previous_status': previous_status,
        'new_status': new_status
    }
    
    history_df = pd.concat([history_df, pd.DataFrame([new_history])], ignore_index=True)
    write_sheet(history_df, 'History')

def get_all_vendors():
    """Get all vendors"""
    return read_sheet('Vendors')

def get_all_bids():
    """Get all bids"""
    return read_sheet('Bids')

def get_bid_by_id(bid_id):
    """Get specific bid by ID"""
    bids_df = read_sheet('Bids')
    bid = bids_df[bids_df['bid_id'] == bid_id]
    if not bid.empty:
        return bid.iloc[0].to_dict()
    return None

def get_vendor_bids_for_bid(bid_id):
    """Get all vendor submissions for a specific bid"""
    vendor_bids_df = read_sheet('VendorBids')
    return vendor_bids_df[vendor_bids_df['bid_id'] == bid_id]

def get_history_for_bid(bid_id):
    """Get history for a specific bid"""
    history_df = read_sheet('History')
    return history_df[history_df['bid_id'] == bid_id].sort_values('action_date', ascending=False)

# Vendor Management Functions
def vendor_login(vendor_id, password):
    """Authenticate vendor login"""
    vendors_df = read_sheet('Vendors')
    vendor = vendors_df[(vendors_df['vendor_id'] == vendor_id) & (vendors_df['password'] == password)]
    if not vendor.empty:
        return vendor.iloc[0].to_dict()
    return None

def create_vendor(vendor_name, contact_email, contact_phone, technical_capability, password):
    """Create a new vendor"""
    vendors_df = read_sheet('Vendors')
    
    new_vendor = {
        'vendor_id': get_next_vendor_id(),
        'vendor_name': vendor_name,
        'contact_email': contact_email,
        'contact_phone': contact_phone,
        'technical_capability': technical_capability,
        'password': password
    }
    
    vendors_df = pd.concat([vendors_df, pd.DataFrame([new_vendor])], ignore_index=True)
    write_sheet(vendors_df, 'Vendors')
    
    return new_vendor['vendor_id']

def get_vendor_by_id(vendor_id):
    """Get vendor by ID"""
    vendors_df = read_sheet('Vendors')
    vendor = vendors_df[vendors_df['vendor_id'] == vendor_id]
    if not vendor.empty:
        return vendor.iloc[0].to_dict()
    return None

# Bid Items Functions
def add_bid_item(bid_id, item_name, item_description, quantity, unit):
    """Add item to a bid"""
    items_df = read_sheet('BidItems')
    
    new_item = {
        'item_id': get_next_item_id(),
        'bid_id': bid_id,
        'item_name': item_name,
        'item_description': item_description,
        'quantity': quantity,
        'unit': unit
    }
    
    items_df = pd.concat([items_df, pd.DataFrame([new_item])], ignore_index=True)
    write_sheet(items_df, 'BidItems')
    
    return new_item['item_id']

def get_items_for_bid(bid_id):
    """Get all items for a specific bid"""
    items_df = read_sheet('BidItems')
    return items_df[items_df['bid_id'] == bid_id]

def delete_bid_item(item_id):
    """Delete a bid item"""
    items_df = read_sheet('BidItems')
    items_df = items_df[items_df['item_id'] != item_id]
    write_sheet(items_df, 'BidItems')
