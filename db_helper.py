"""
Excel Database Helper Functions for Bid Management System
"""
import pandas as pd
from datetime import datetime
import os

DATABASE_FILE = 'database.xlsx'


def current_timestamp():
    """Return the current timestamp string in a consistent format"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def reset_approval_columns(bids_df, bid_id):
    """Reset approval-related columns back to their default pending state"""
    reset_fields = {
        'a1_status': 'Pending',
        'a1_comment': '',
        'a1_date': '',
        'a2_status': 'Pending',
        'a2_comment': '',
        'a2_date': ''
    }
    for column, value in reset_fields.items():
        bids_df.loc[bids_df['bid_id'] == bid_id, column] = value


def _normalize_text_value(value):
    """Return a clean string for text-based Excel cells"""
    if pd.isna(value):
        return ''
    value_str = str(value).strip()
    return '' if value_str.lower() in {'nan', 'nat', 'none'} else value_str


def _clean_bids_dataframe(bids_df):
    """Drop deprecated columns and normalise text fields"""
    bids_df = bids_df.copy()
    if 'min_technical_capability' in bids_df.columns:
        bids_df = bids_df.drop(columns=['min_technical_capability'])

    if bids_df.empty:
        return bids_df

    text_columns = [
        'contract_name',
        'contract_description',
        'status',
        'selected_buyer_id',
        'selected_submission_id',
        'vendor_justification',
        'submission_date',
        'buyer_comment',
        'vendor_name',
        'a1_status',
        'a1_comment',
        'a1_date',
        'a2_status',
        'a2_comment',
        'a2_date'
    ]

    for column in text_columns:
        if column in bids_df.columns:
            bids_df[column] = bids_df[column].apply(_normalize_text_value)

    return bids_df

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
    """Generate next submission ID (legacy support)"""
    try:
        buyer_bids_df = read_sheet('BuyerBids')
        if buyer_bids_df.empty or len(buyer_bids_df) == 0:
            return 'SUB001'
        
        existing_ids = buyer_bids_df['submission_id'].dropna().tolist()
        if not existing_ids:
            return 'SUB001'
        
        max_num = max([int(sub_id.replace('SUB', '')) for sub_id in existing_ids if isinstance(sub_id, str)])
        return f'SUB{str(max_num + 1).zfill(3)}'
    except:
        return 'SUB001'

def get_next_history_id():
    """Generate next history ID"""
    history_df = read_sheet('History')
    if history_df.empty or len(history_df) == 0:
        return 1
    
    return history_df['history_id'].max() + 1

def get_next_buyer_id():
    """Generate next buyer ID"""
    buyers_df = read_sheet('Buyers')
    if buyers_df.empty or len(buyers_df) == 0:
        return 'V001'
    
    existing_ids = buyers_df['buyer_id'].dropna().tolist()
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

def create_bid(contract_name, contract_description, contract_value, vendor_name, assigned_buyer_id=None):
    """Create a new bid and optionally assign a buyer immediately"""
    bids_df = _clean_bids_dataframe(read_sheet('Bids'))

    initial_status = 'Awaiting Buyer' if assigned_buyer_id else 'Draft'

    new_bid = {
        'bid_id': get_next_bid_id(),
        'contract_name': contract_name,
        'contract_description': contract_description,
        'contract_value': contract_value,
        'created_date': current_timestamp(),
        'vendor_name': vendor_name,
        'status': initial_status,
        'selected_buyer_id': assigned_buyer_id or '',
        'selected_submission_id': '',
        'vendor_justification': '',
        'submission_date': '',
        'buyer_comment': '',
        'a1_status': 'Pending',
        'a1_comment': '',
        'a1_date': '',
        'a2_status': 'Pending',
        'a2_comment': '',
        'a2_date': ''
    }
    
    bids_df = pd.concat([bids_df, pd.DataFrame([new_bid])], ignore_index=True)
    write_sheet(bids_df, 'Bids')
    
    # Add to history
    add_history(new_bid['bid_id'], vendor_name, 'Vendor', 'Created Bid', 
                f"Created new bid: {contract_name}", None, initial_status)

    if assigned_buyer_id:
        buyer = get_buyer_by_id(assigned_buyer_id)
        buyer_label = buyer['buyer_name'] if buyer else assigned_buyer_id
        add_history(
            new_bid['bid_id'],
            vendor_name,
            'Vendor',
            'Assigned Buyer',
            f"Assigned buyer {buyer_label} ({assigned_buyer_id})",
            initial_status,
            'Awaiting Buyer'
        )
    
    return new_bid['bid_id']

def submit_buyer_bid(bid_id, buyer_id, buyer_name, bid_amount, bid_description):
    """Submit a buyer bid (legacy support)"""
    try:
        buyer_bids_df = read_sheet('BuyerBids')
        
        new_submission = {
            'submission_id': get_next_submission_id(),
            'bid_id': bid_id,
            'buyer_id': buyer_id,
            'buyer_name': buyer_name,
            'bid_amount': bid_amount,
            'bid_description': bid_description,
            'submission_date': current_timestamp(),
            'is_selected': False
        }
        
        buyer_bids_df = pd.concat([buyer_bids_df, pd.DataFrame([new_submission])], ignore_index=True)
        write_sheet(buyer_bids_df, 'BuyerBids')
        
        # Add to history
        add_history(bid_id, buyer_name, 'Buyer', 'Submitted Bid', 
                    f"Bid Amount: {bid_amount}", None, None)
    except Exception as e:
        print(f"Warning: BuyerBids sheet not found - legacy feature disabled: {e}")
    
    return new_submission['submission_id']


def buyer_submit_comment(bid_id, buyer_id, comment):
    """Assigned buyer submits a comment to trigger A1 approval"""
    bids_df = read_sheet('Bids')

    matched_bid = bids_df[bids_df['bid_id'] == bid_id]
    if matched_bid.empty:
        return False, "Bid not found."

    stored_buyer_id = str(matched_bid.iloc[0].get('selected_buyer_id', '')).strip()
    if stored_buyer_id != str(buyer_id).strip():
        return False, "You are not assigned to this bid."

    previous_status = matched_bid.iloc[0].get('status', '')

    bids_df.loc[bids_df['bid_id'] == bid_id, 'buyer_comment'] = comment
    bids_df.loc[bids_df['bid_id'] == bid_id, 'submission_date'] = current_timestamp()
    bids_df.loc[bids_df['bid_id'] == bid_id, 'selected_submission_id'] = 'ASSIGNED'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'status'] = 'Pending A1'

    reset_approval_columns(bids_df, bid_id)
    write_sheet(bids_df, 'Bids')

    buyer = get_buyer_by_id(buyer_id)
    buyer_name = buyer['buyer_name'] if buyer else buyer_id
    add_history(
        bid_id,
        buyer_name,
        'Buyer',
        'Submitted for A1 Approval',
        comment,
        previous_status,
        'Pending A1'
    )

    return True, None

def select_buyer_and_submit_for_approval(bid_id, submission_id, justification, vendor_name):
    """Admin selects a specific buyer submission and submits for A1 approval (legacy support)"""
    try:
        bids_df = read_sheet('Bids')
        buyer_bids_df = read_sheet('BuyerBids')

        bid_row = bids_df[bids_df['bid_id'] == bid_id]
        if bid_row.empty:
            return False, f"Bid {bid_id} not found"

        normalized_submission_id = str(submission_id).strip()
        normalized_bid_id = str(bid_id).strip()

        submission_row = buyer_bids_df[
            (buyer_bids_df['bid_id'].astype(str) == normalized_bid_id) &
            (buyer_bids_df['submission_id'].astype(str) == normalized_submission_id)
        ]

        if submission_row.empty:
            return False, "Selected submission could not be located for this bid"

        buyer_id = submission_row.iloc[0]['buyer_id']
        current_status = bid_row.iloc[0]['status']

        bids_df.loc[bids_df['bid_id'] == bid_id, 'selected_buyer_id'] = buyer_id
        bids_df.loc[bids_df['bid_id'] == bid_id, 'selected_submission_id'] = normalized_submission_id
        bids_df.loc[bids_df['bid_id'] == bid_id, 'vendor_justification'] = justification
        bids_df.loc[bids_df['bid_id'] == bid_id, 'submission_date'] = current_timestamp()
        bids_df.loc[bids_df['bid_id'] == bid_id, 'status'] = 'Pending A1'

        reset_approval_columns(bids_df, bid_id)
        write_sheet(bids_df, 'Bids')

        buyer_bids_df.loc[buyer_bids_df['bid_id'] == bid_id, 'is_selected'] = False
        buyer_bids_df.loc[
            (buyer_bids_df['bid_id'].astype(str) == normalized_bid_id) &
            (buyer_bids_df['submission_id'].astype(str) == normalized_submission_id),
            'is_selected'
        ] = True
        write_sheet(buyer_bids_df, 'BuyerBids')

        action_text = 'Resubmitted for A1 Approval' if current_status == 'Under Review' else 'Selected Submission & Submitted for A1 Approval'
        add_history(
            bid_id,
            vendor_name,
            'Vendor',
            action_text,
            f"Selected Submission: {normalized_submission_id} (Buyer: {buyer_id}), Justification: {justification}",
            current_status,
            'Pending A1'
        )

        return True, buyer_id
    except Exception as e:
        print(f"Warning: BuyerBids sheet not found - legacy feature disabled: {e}")
        return False, "BuyerBids feature not available"

def a1_approve(bid_id, comment, approver_name):
    """A1 Approver approves the bid"""
    bids_df = read_sheet('Bids')
    
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_status'] = 'Approved'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_comment'] = comment
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_date'] = current_timestamp()
    bids_df.loc[bids_df['bid_id'] == bid_id, 'status'] = 'Pending A2'
    
    write_sheet(bids_df, 'Bids')
    
    # Add to history
    add_history(bid_id, approver_name, 'A1 Approver', 'Approved', comment, 'Pending A1', 'Pending A2')

def a1_reject(bid_id, comment, approver_name):
    """A1 Approver rejects the bid"""
    bids_df = read_sheet('Bids')
    
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_status'] = 'Rejected'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_comment'] = comment
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_date'] = current_timestamp()
    bids_df.loc[bids_df['bid_id'] == bid_id, 'status'] = 'Awaiting Buyer'
    
    write_sheet(bids_df, 'Bids')
    
    # Add to history
    add_history(bid_id, approver_name, 'A1 Approver', 'Rejected', comment, 'Pending A1', 'Awaiting Buyer')

def a2_approve(bid_id, comment, approver_name):
    """A2 Approver approves the bid"""
    bids_df = read_sheet('Bids')
    
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_status'] = 'Approved'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_comment'] = comment
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_date'] = current_timestamp()
    bids_df.loc[bids_df['bid_id'] == bid_id, 'status'] = 'Approved'
    
    write_sheet(bids_df, 'Bids')
    
    # Add to history
    add_history(bid_id, approver_name, 'A2 Approver', 'Approved - Final', comment, 'Pending A2', 'Approved')

def a2_reject(bid_id, comment, approver_name):
    """A2 Approver rejects the bid"""
    bids_df = read_sheet('Bids')
    
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_status'] = 'Rejected'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_comment'] = comment
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a2_date'] = current_timestamp()
    bids_df.loc[bids_df['bid_id'] == bid_id, 'status'] = 'Pending A1'
    bids_df.loc[bids_df['bid_id'] == bid_id, 'a1_status'] = 'Pending'
    
    write_sheet(bids_df, 'Bids')
    
    # Add to history
    add_history(bid_id, approver_name, 'A2 Approver', 'Rejected - Sent back to A1', comment, 'Pending A2', 'Pending A1')

def a2_reopen_bid(bid_id, comment, approver_name):
    """A2 Approver reopens an approved bid for modifications"""
    bids_df = read_sheet('Bids')

    # Reset bid to Open for Bidding status so admin can edit and resubmit
    bids_df.loc[bids_df['bid_id'] == bid_id, 'status'] = 'Awaiting Buyer'
    reset_approval_columns(bids_df, bid_id)
    bids_df.loc[bids_df['bid_id'] == bid_id, 'selected_submission_id'] = ''
    bids_df.loc[bids_df['bid_id'] == bid_id, 'vendor_justification'] = ''
    bids_df.loc[bids_df['bid_id'] == bid_id, 'submission_date'] = ''
    bids_df.loc[bids_df['bid_id'] == bid_id, 'buyer_comment'] = ''

    write_sheet(bids_df, 'Bids')

    # Add to history
    add_history(bid_id, approver_name, 'A2 Approver', 'Reopened Bid for Modifications', comment, 'Approved', 'Awaiting Buyer')

def add_history(bid_id, action_by, role, action, comment, previous_status, new_status):
    """Add entry to history"""
    history_df = read_sheet('History')
    
    new_history = {
        'history_id': get_next_history_id(),
        'bid_id': bid_id,
        'action_date': current_timestamp(),
        'action_by': action_by,
        'role': role,
        'action': action,
        'comment': comment,
        'previous_status': previous_status,
        'new_status': new_status
    }
    
    history_df = pd.concat([history_df, pd.DataFrame([new_history])], ignore_index=True)
    write_sheet(history_df, 'History')

def get_all_buyers():
    """Get all buyers without legacy capability column"""
    buyers_df = read_sheet('Buyers')
    if 'technical_capability' in buyers_df.columns:
        buyers_df = buyers_df.drop(columns=['technical_capability'])
    return buyers_df

def get_all_bids():
    """Get all bids"""
    return _clean_bids_dataframe(read_sheet('Bids'))

def get_bid_by_id(bid_id):
    """Get specific bid by ID with vendor name"""
    bids_df = _clean_bids_dataframe(read_sheet('Bids'))
    bid = bids_df[bids_df['bid_id'] == bid_id]
    if not bid.empty:
        bid_dict = bid.iloc[0].to_dict()
        # Get vendor name
        vendor_id = bid_dict.get('admin_name', '')
        if vendor_id:
            vendor = get_vendor_by_id(vendor_id)
            if vendor:
                bid_dict['vendor_name'] = vendor.get('vendor_name', vendor_id)
            else:
                bid_dict['vendor_name'] = vendor_id
        else:
            bid_dict['vendor_name'] = 'N/A'
        return bid_dict
    return None

def get_buyer_bids_for_bid(bid_id):
    """Get all buyer submissions for a specific bid (legacy support)"""
    try:
        buyer_bids_df = read_sheet('BuyerBids')
        return buyer_bids_df[buyer_bids_df['bid_id'] == bid_id]
    except:
        # Return empty dataframe if BuyerBids sheet doesn't exist
        return pd.DataFrame()

def get_history_for_bid(bid_id):
    """Get history for a specific bid"""
    history_df = read_sheet('History')
    return history_df[history_df['bid_id'] == bid_id].sort_values('action_date', ascending=False)

# Vendor Management Functions
def get_vendor_by_id(vendor_id):
    """Get vendor by ID"""
    vendors_df = read_sheet('Vendors')
    vendor = vendors_df[vendors_df['vendor_id'] == vendor_id]
    if not vendor.empty:
        return vendor.iloc[0].to_dict()
    return None

# Buyer Management Functions
def buyer_login(buyer_id, password):
    """Authenticate buyer login"""
    buyers_df = read_sheet('Buyers')
    if 'technical_capability' in buyers_df.columns:
        buyers_df = buyers_df.drop(columns=['technical_capability'])
    buyer = buyers_df[(buyers_df['buyer_id'] == buyer_id) & (buyers_df['password'] == password)]
    if not buyer.empty:
        return buyer.iloc[0].to_dict()
    return None

def create_buyer(buyer_name, contact_email, contact_phone, password):
    """Create a new buyer"""
    buyers_df = read_sheet('Buyers')

    if 'technical_capability' in buyers_df.columns:
        buyers_df = buyers_df.drop(columns=['technical_capability'])

    new_buyer = {
        'buyer_id': get_next_buyer_id(),
        'buyer_name': buyer_name,
        'contact_email': contact_email,
        'contact_phone': contact_phone,
        'password': password
    }

    buyers_df = pd.concat([buyers_df, pd.DataFrame([new_buyer])], ignore_index=True)
    write_sheet(buyers_df, 'Buyers')

    return new_buyer['buyer_id']

def get_buyer_by_id(buyer_id):
    """Get buyer by ID"""
    buyers_df = read_sheet('Buyers')
    if 'technical_capability' in buyers_df.columns:
        buyers_df = buyers_df.drop(columns=['technical_capability'])
    buyer = buyers_df[buyers_df['buyer_id'] == buyer_id]
    if not buyer.empty:
        return buyer.iloc[0].to_dict()
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

# Bidder Management Functions
def get_next_bidder_id():
    """Generate next bidder ID"""
    bidders_df = read_sheet('Bidders')
    if bidders_df.empty or len(bidders_df) == 0:
        return 'BIDDER001'
    
    existing_ids = bidders_df['bidder_id'].dropna().tolist()
    if not existing_ids:
        return 'BIDDER001'
    
    max_num = max([int(b_id.replace('BIDDER', '')) for b_id in existing_ids if isinstance(b_id, str)])
    return f'BIDDER{str(max_num + 1).zfill(3)}'

def get_next_bidder_bid_id():
    """Generate next bidder bid ID"""
    bidder_bids_df = read_sheet('BidderItemBids')
    if bidder_bids_df.empty or len(bidder_bids_df) == 0:
        return 'BB001'
    
    existing_ids = bidder_bids_df['bidder_bid_id'].dropna().tolist()
    if not existing_ids:
        return 'BB001'
    
    max_num = max([int(bb_id.replace('BB', '')) for bb_id in existing_ids if isinstance(bb_id, str)])
    return f'BB{str(max_num + 1).zfill(3)}'

def create_bidder(bidder_name, contact_email, contact_phone, password):
    """Create a new bidder"""
    bidders_df = read_sheet('Bidders')
    
    new_bidder = {
        'bidder_id': get_next_bidder_id(),
        'bidder_name': bidder_name,
        'contact_email': contact_email,
        'contact_phone': contact_phone,
        'password': password
    }
    
    bidders_df = pd.concat([bidders_df, pd.DataFrame([new_bidder])], ignore_index=True)
    write_sheet(bidders_df, 'Bidders')
    
    return new_bidder['bidder_id']

def get_all_bidders():
    """Get all bidders"""
    return read_sheet('Bidders')

def get_bidder_by_id(bidder_id):
    """Get bidder by ID"""
    bidders_df = read_sheet('Bidders')
    bidder = bidders_df[bidders_df['bidder_id'] == bidder_id]
    if not bidder.empty:
        return bidder.iloc[0].to_dict()
    return None

def bidder_login(bidder_id, password):
    """Authenticate bidder login"""
    bidders_df = read_sheet('Bidders')
    bidder = bidders_df[(bidders_df['bidder_id'] == bidder_id) & (bidders_df['password'] == password)]
    if not bidder.empty:
        return bidder.iloc[0].to_dict()
    return None

def submit_bidder_item_bids(bid_id, bidder_id, item_rates):
    """
    Submit unit rates for multiple items by a bidder
    item_rates: dict with item_id as key and unit_rate as value
    """
    bidder_bids_df = read_sheet('BidderItemBids')
    
    # Remove any existing bids from this bidder for this bid
    bidder_bids_df = bidder_bids_df[~((bidder_bids_df['bid_id'] == bid_id) & 
                                      (bidder_bids_df['bidder_id'] == bidder_id))]
    
    # Add new bids
    new_bids = []
    for item_id, unit_rate in item_rates.items():
        new_bid = {
            'bidder_bid_id': get_next_bidder_bid_id(),
            'bid_id': bid_id,
            'bidder_id': bidder_id,
            'item_id': item_id,
            'unit_rate': float(unit_rate),
            'submission_date': current_timestamp()
        }
        new_bids.append(new_bid)
    
    bidder_bids_df = pd.concat([bidder_bids_df, pd.DataFrame(new_bids)], ignore_index=True)
    write_sheet(bidder_bids_df, 'BidderItemBids')
    
    # Add to history
    bidder = get_bidder_by_id(bidder_id)
    bidder_name = bidder['bidder_name'] if bidder else bidder_id
    add_history(bid_id, bidder_name, 'Bidder', 'Submitted Item Bids', 
                f"Submitted unit rates for {len(item_rates)} items", None, None)
    
    return True

def get_bidder_bids_for_bid(bid_id):
    """Get all bidder item bids for a specific bid"""
    bidder_bids_df = read_sheet('BidderItemBids')
    return bidder_bids_df[bidder_bids_df['bid_id'] == bid_id]

def get_bidder_bids_for_item(bid_id, item_id):
    """Get all bidder bids for a specific item in a bid"""
    bidder_bids_df = read_sheet('BidderItemBids')
    return bidder_bids_df[(bidder_bids_df['bid_id'] == bid_id) & 
                         (bidder_bids_df['item_id'] == item_id)]

def get_bidder_submission_for_bid(bid_id, bidder_id):
    """Get specific bidder's submission for a bid"""
    bidder_bids_df = read_sheet('BidderItemBids')
    return bidder_bids_df[(bidder_bids_df['bid_id'] == bid_id) & 
                         (bidder_bids_df['bidder_id'] == bidder_id)]

def get_all_bidder_bids_with_totals(bid_id):
    """
    Get all bidder bids for a bid with calculated totals
    Returns a structured dict with bidder info and their total bid amounts
    """
    bidder_bids_df = read_sheet('BidderItemBids')
    items_df = read_sheet('BidItems')
    bidders_df = read_sheet('Bidders')
    
    # Filter for this bid
    bid_submissions = bidder_bids_df[bidder_bids_df['bid_id'] == bid_id]
    bid_items = items_df[items_df['bid_id'] == bid_id]
    
    if bid_submissions.empty:
        return []
    
    # Calculate totals for each bidder
    bidder_totals = []
    for bidder_id in bid_submissions['bidder_id'].unique():
        bidder_items = bid_submissions[bid_submissions['bidder_id'] == bidder_id]
        bidder_info = bidders_df[bidders_df['bidder_id'] == bidder_id]
        
        if bidder_info.empty:
            continue
        
        total = 0
        item_details = []
        
        for _, bid_item in bid_items.iterrows():
            item_bid = bidder_items[bidder_items['item_id'] == bid_item['item_id']]
            if not item_bid.empty:
                unit_rate = float(item_bid.iloc[0]['unit_rate'])
                quantity = float(bid_item['quantity'])
                item_total = unit_rate * quantity
                total += item_total
                
                item_details.append({
                    'item_id': bid_item['item_id'],
                    'item_name': bid_item['item_name'],
                    'item_description': bid_item['item_description'],
                    'quantity': quantity,
                    'unit': bid_item['unit'],
                    'unit_rate': unit_rate,
                    'total': item_total
                })
        
        bidder_totals.append({
            'bidder_id': bidder_id,
            'bidder_name': bidder_info.iloc[0]['bidder_name'],
            'contact_email': bidder_info.iloc[0]['contact_email'],
            'contact_phone': bidder_info.iloc[0]['contact_phone'],
            'total_bid_amount': total,
            'bid_items': item_details,
            'submission_date': bidder_items.iloc[0]['submission_date'] if not bidder_items.empty else ''
        })
    
    # Sort by total bid amount (lowest first)
    bidder_totals.sort(key=lambda x: x['total_bid_amount'])
    
    return bidder_totals

