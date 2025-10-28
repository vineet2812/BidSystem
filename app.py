"""
Flask Bid Management System
A web application for managing bids with approval workflow
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import db_helper as db
from datetime import datetime
import io
import math
import textwrap
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Role management
ROLES = ['Vendor', 'Buyer', 'Bidder', 'A1 Approver', 'A2 Approver']


def _is_missing_excel_value(value):
    """Detect whether a cell value from Excel should be treated as empty"""
    if value is None:
        return True
    try:
        if math.isnan(value):
            return True
    except (TypeError, ValueError):
        pass
    if isinstance(value, str) and value.strip().lower() in {'', 'nan', 'nat', 'none'}:
        return True
    return False


def sanitize_excel_value(value, default=''):
    """Return a safe default when Excel data is missing"""
    return default if _is_missing_excel_value(value) else value


def normalize_bid_record(bid_record):
    """Coerce optional bid fields to predictable defaults"""
    if not bid_record:
        return {}

    normalized = bid_record.copy()
    for key in [
        'selected_buyer_id',
        'selected_submission_id',
        'vendor_justification',
        'buyer_comment',
        'submission_date',
        'a1_comment',
        'a1_date',
        'a2_comment',
        'a2_date'
    ]:
        normalized[key] = sanitize_excel_value(normalized.get(key), '')
    return normalized


def _normalize_bool_flag(value):
    """Standardise truthy flags stored in Excel"""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return int(value) == 1
    return str(value).strip().lower() in {'true', '1', 'yes', 'selected'}


def prepare_buyer_bids(bid_id):
    """Fetch buyer submissions with consistent typing and metadata"""
    buyer_bids = db.get_buyer_bids_for_bid(bid_id)
    if buyer_bids.empty:
        return buyer_bids, {}

    buyer_bids = buyer_bids.copy()
    if 'submission_id' not in buyer_bids.columns:
        buyer_bids['submission_id'] = ''
    buyer_bids['submission_id'] = buyer_bids['submission_id'].fillna('').astype(str).str.strip()

    if 'buyer_id' not in buyer_bids.columns:
        buyer_bids['buyer_id'] = ''
    buyer_bids['buyer_id'] = buyer_bids['buyer_id'].fillna('').astype(str).str.strip()

    if 'is_selected' not in buyer_bids.columns:
        buyer_bids['is_selected'] = False
    buyer_bids['is_selected'] = buyer_bids['is_selected'].apply(_normalize_bool_flag)

    buyer_lookup = {}
    for vid in buyer_bids['buyer_id'].unique():
        buyer = db.get_buyer_by_id(vid)
        if buyer:
            buyer_lookup[vid] = buyer

    return buyer_bids, buyer_lookup


def get_selected_submission(bid_record, buyer_bids):
    """Locate the DataFrame row for the winning submission"""
    if buyer_bids.empty:
        return buyer_bids

    selected_submission_id = str(sanitize_excel_value(bid_record.get('selected_submission_id'), '')).strip()
    selected_buyer_id = str(sanitize_excel_value(bid_record.get('selected_buyer_id'), '')).strip()

    if selected_submission_id:
        selected_rows = buyer_bids[buyer_bids['submission_id'] == selected_submission_id]
        if not selected_rows.empty:
            return selected_rows

    selected_rows = buyer_bids[buyer_bids['is_selected'] == True]
    if not selected_rows.empty:
        if selected_buyer_id:
            buyer_match = selected_rows[selected_rows['buyer_id'] == selected_buyer_id]
            if not buyer_match.empty:
                return buyer_match
        return selected_rows

    if selected_buyer_id:
        fallback = buyer_bids[buyer_bids['buyer_id'] == selected_buyer_id]
        if not fallback.empty:
            return fallback

    return buyer_bids.iloc[0:0]

@app.route('/')
def index():
    """Home page - redirect to dashboard based on role"""
    if 'role' not in session:
        session['role'] = 'Vendor'
        session['user_name'] = 'Admin User'
    
    role = session.get('role', 'Vendor')
    
    if role == 'Vendor':
        return redirect(url_for('vendor_dashboard'))
    elif role == 'Buyer':
        # Check if buyer is logged in
        if 'buyer_id' not in session:
            return redirect(url_for('buyer_login_page'))
        return redirect(url_for('buyer_dashboard'))
    elif role == 'Bidder':
        # Check if bidder is logged in
        if 'bidder_id' not in session:
            return redirect(url_for('bidder_login_page'))
        return redirect(url_for('bidder_dashboard'))
    elif role == 'A1 Approver':
        return redirect(url_for('a1_dashboard'))
    elif role == 'A2 Approver':
        return redirect(url_for('a2_dashboard'))
    
    return redirect(url_for('vendor_dashboard'))

@app.route('/switch_role/<role>')
def switch_role(role):
    """Switch between roles"""
    if role in ROLES:
        session['role'] = role
        
        # Set appropriate user name based on role
        if role == 'Vendor':
            session['user_name'] = 'Admin User'
        elif role == 'Buyer':
            # Clear buyer session when switching to buyer role
            if 'buyer_id' in session:
                del session['buyer_id']
                del session['buyer_name']
            session['user_name'] = 'Buyer User'
        elif role == 'Bidder':
            # Clear bidder session when switching to bidder role
            if 'bidder_id' in session:
                del session['bidder_id']
                del session['bidder_name']
            session['user_name'] = 'Bidder User'
        elif role == 'A1 Approver':
            session['user_name'] = 'A1 Approver'
        elif role == 'A2 Approver':
            session['user_name'] = 'A2 Approver'
        
        flash(f'Switched to {role} role', 'success')
    
    return redirect(url_for('index'))

# Buyer Login/Registration Routes
@app.route('/buyer/login', methods=['GET', 'POST'])
def buyer_login_page():
    """Buyer login page"""
    buyers_df = db.get_all_buyers()
    buyers = buyers_df.to_dict('records') if not buyers_df.empty else []
    
    if request.method == 'POST':
        buyer_id = request.form['buyer_id']
        
        buyer = db.get_buyer_by_id(buyer_id)
        if buyer:
            session['buyer_id'] = buyer['buyer_id']
            session['buyer_name'] = buyer['buyer_name']
            session['user_name'] = buyer['buyer_name']
            flash(f'Welcome, {buyer["buyer_name"]}!', 'success')
            return redirect(url_for('buyer_dashboard'))
        else:
            flash('Invalid buyer selection!', 'danger')
    
    return render_template('buyer_login.html', role=session.get('role'), buyers=buyers)

@app.route('/buyer/register', methods=['GET', 'POST'])
def buyer_register():
    """Buyer registration page"""
    if request.method == 'POST':
        buyer_name = request.form['buyer_name']
        contact_email = request.form['contact_email']
        contact_phone = request.form['contact_phone']
        password = request.form['password']
        
        buyer_id = db.create_buyer(buyer_name, contact_email, contact_phone, password)
        
        # Auto login after registration
        session['buyer_id'] = buyer_id
        session['buyer_name'] = buyer_name
        session['user_name'] = buyer_name
        
        flash(f'Registration successful! Your Buyer ID is: {buyer_id}', 'success')
        return redirect(url_for('buyer_dashboard'))
    
    return render_template('buyer_register.html', role=session.get('role'))

@app.route('/buyer/logout')
def buyer_logout():
    """Buyer logout"""
    if 'buyer_id' in session:
        del session['buyer_id']
        del session['buyer_name']
    flash('Logged out successfully!', 'success')
    return redirect(url_for('buyer_login_page'))

# Bidder Login/Registration Routes
@app.route('/bidder/login', methods=['GET', 'POST'])
def bidder_login_page():
    """Bidder login page"""
    bidders_df = db.get_all_bidders()
    bidders = bidders_df.to_dict('records') if not bidders_df.empty else []
    
    if request.method == 'POST':
        bidder_id = request.form['bidder_id']
        
        bidder = db.get_bidder_by_id(bidder_id)
        if bidder:
            session['bidder_id'] = bidder['bidder_id']
            session['bidder_name'] = bidder['bidder_name']
            session['user_name'] = bidder['bidder_name']
            flash(f'Welcome, {bidder["bidder_name"]}!', 'success')
            return redirect(url_for('bidder_dashboard'))
        else:
            flash('Invalid bidder selection!', 'danger')
    
    return render_template('bidder_login.html', role=session.get('role'), bidders=bidders)

@app.route('/bidder/register', methods=['GET', 'POST'])
def bidder_register():
    """Bidder registration page"""
    if request.method == 'POST':
        bidder_name = request.form['bidder_name']
        contact_email = request.form['contact_email']
        contact_phone = request.form['contact_phone']
        password = request.form['password']
        
        bidder_id = db.create_bidder(bidder_name, contact_email, contact_phone, password)
        
        # Auto login after registration
        session['bidder_id'] = bidder_id
        session['bidder_name'] = bidder_name
        session['user_name'] = bidder_name
        
        flash(f'Registration successful! Your Bidder ID is: {bidder_id}', 'success')
        return redirect(url_for('bidder_dashboard'))
    
    return render_template('bidder_register.html', role=session.get('role'))

@app.route('/bidder/logout')
def bidder_logout():
    """Bidder logout"""
    if 'bidder_id' in session:
        del session['bidder_id']
        del session['bidder_name']
    flash('Logged out successfully!', 'success')
    return redirect(url_for('bidder_login_page'))

@app.route('/bidder/dashboard')
def bidder_dashboard():
    """Bidder Dashboard - shows all bids available for bidding"""
    if session.get('role') != 'Bidder':
        flash('Access denied. Bidder role required.', 'danger')
        return redirect(url_for('index'))
    
    if 'bidder_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('bidder_login_page'))
    
    bids = db.get_all_bids()
    bidder_id = session.get('bidder_id', '')
    
    # Add submission status for each bid
    if not bids.empty:
        bids = bids.copy()
        has_submitted = []
        for _, bid in bids.iterrows():
            submission = db.get_bidder_submission_for_bid(bid['bid_id'], bidder_id)
            has_submitted.append(not submission.empty)
        bids['has_submitted'] = has_submitted
    
    return render_template('bidder_dashboard.html', bids=bids, role=session.get('role'))

@app.route('/bidder/submit_bid/<bid_id>', methods=['GET', 'POST'])
def bidder_submit_bid(bid_id):
    """Bidder submit item bids with unit rates"""
    if session.get('role') != 'Bidder':
        flash('Access denied. Bidder role required.', 'danger')
        return redirect(url_for('index'))
    
    if 'bidder_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('bidder_login_page'))
    
    bid = db.get_bid_by_id(bid_id)
    if not bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('bidder_dashboard'))
    
    items = db.get_items_for_bid(bid_id)
    if items.empty:
        flash('No items found for this bid. Cannot submit.', 'warning')
        return redirect(url_for('bidder_dashboard'))
    
    bidder_id = session.get('bidder_id')
    
    # Get existing submission if any
    existing_submission = db.get_bidder_submission_for_bid(bid_id, bidder_id)
    existing_rates = {}
    if not existing_submission.empty:
        for _, row in existing_submission.iterrows():
            existing_rates[row['item_id']] = row['unit_rate']
    
    if request.method == 'POST':
        item_rates = {}
        for _, item in items.iterrows():
            item_id = item['item_id']
            unit_rate = request.form.get(f'unit_rate_{item_id}')
            if unit_rate:
                try:
                    item_rates[item_id] = float(unit_rate)
                except ValueError:
                    flash(f'Invalid unit rate for {item["item_name"]}', 'danger')
                    return redirect(url_for('bidder_submit_bid', bid_id=bid_id))
        
        if len(item_rates) != len(items):
            flash('Please provide unit rates for all items.', 'danger')
            return redirect(url_for('bidder_submit_bid', bid_id=bid_id))
        
        db.submit_bidder_item_bids(bid_id, bidder_id, item_rates)
        flash('Bid submitted successfully!', 'success')
        return redirect(url_for('bidder_dashboard'))
    
    return render_template('bidder_submit_bid.html', bid=bid, items=items, 
                         role=session.get('role'), existing_rates=existing_rates)

@app.route('/vendor/dashboard')
def vendor_dashboard():
    """Admin Dashboard"""
    if session.get('role') != 'Vendor':
        flash('Access denied. Admin role required.', 'danger')
        return redirect(url_for('index'))
    
    bids = db.get_all_bids()
    
    # Enrich bids with buyer information
    if not bids.empty:
        buyer_names = []
        buyer_contacts = []
        for index, bid in bids.iterrows():
            buyer_id = str(bid.get('selected_buyer_id', '')).strip()
            if buyer_id:
                buyer = db.get_buyer_by_id(buyer_id)
                if buyer:
                    buyer_names.append(buyer.get('buyer_name', ''))
                    buyer_contacts.append(buyer.get('contact_email', ''))
                else:
                    buyer_names.append('')
                    buyer_contacts.append('')
            else:
                buyer_names.append('')
                buyer_contacts.append('')
        
        bids['buyer_name'] = buyer_names
        bids['buyer_contact'] = buyer_contacts
    
    return render_template('vendor_dashboard.html', bids=bids, role=session.get('role'))

@app.route('/vendor/create_bid', methods=['GET', 'POST'])
def create_bid():
    """Create new bid"""
    if session.get('role') != 'Vendor':
        flash('Access denied. Admin role required.', 'danger')
        return redirect(url_for('index'))

    buyers_df = db.get_all_buyers()
    buyers = buyers_df.to_dict('records') if not buyers_df.empty else []
    
    if request.method == 'POST':
        contract_name = request.form['contract_name']
        contract_description = request.form['contract_description']
        contract_value = float(request.form['contract_value'])
        assigned_buyer_id = request.form.get('assigned_buyer_id', '').strip()
        vendor_name = session.get('user_name', 'Vendor')
        
        if not assigned_buyer_id:
            flash('Please assign a buyer for this bid.', 'danger')
            return render_template('create_bid.html', role=session.get('role'), buyers=buyers)

        if not any(v['buyer_id'] == assigned_buyer_id for v in buyers):
            flash('Selected buyer could not be found. Please choose a valid buyer.', 'danger')
            return render_template('create_bid.html', role=session.get('role'), buyers=buyers)

        bid_id = db.create_bid(contract_name, contract_description, contract_value, vendor_name, assigned_buyer_id)
        
        # Add bid items if provided
        item_names = request.form.getlist('item_name[]')
        item_descriptions = request.form.getlist('item_description[]')
        quantities = request.form.getlist('quantity[]')
        units = request.form.getlist('unit[]')
        
        for i in range(len(item_names)):
            if item_names[i]:  # Only add if item name is provided
                db.add_bid_item(bid_id, item_names[i], item_descriptions[i], 
                              float(quantities[i]) if quantities[i] else 0, units[i])

        selected_buyer = next((v for v in buyers if v.get('buyer_id') == assigned_buyer_id), None)
        buyer_label = selected_buyer['buyer_name'] if selected_buyer else assigned_buyer_id

        flash(f'Bid {bid_id} created and assigned to {buyer_label}!', 'success')
        return redirect(url_for('vendor_dashboard'))

    return render_template('create_bid.html', role=session.get('role'), buyers=buyers)

@app.route('/vendor/view_bid/<bid_id>')
def vendor_view_bid(bid_id):
    """View bid details and buyer submissions"""
    if session.get('role') != 'Vendor':
        flash('Access denied. Admin role required.', 'danger')
        return redirect(url_for('index'))
    
    raw_bid = db.get_bid_by_id(bid_id)
    if not raw_bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('vendor_dashboard'))

    bid = normalize_bid_record(raw_bid)
    history = db.get_history_for_bid(bid_id)
    items = db.get_items_for_bid(bid_id)

    assigned_buyer = None
    assigned_buyer_id = str(bid.get('selected_buyer_id', '')).strip()
    if assigned_buyer_id:
        assigned_buyer = db.get_buyer_by_id(assigned_buyer_id)

    # Get all bidder submissions
    bidder_submissions = db.get_all_bidder_bids_with_totals(bid_id)
    num_bidders = len(bidder_submissions)

    return render_template(
        'vendor_view_bid.html',
        bid=bid,
        assigned_buyer=assigned_buyer,
        history=history,
        items=items,
        bidder_submissions=bidder_submissions,
        num_bidders=num_bidders,
        role=session.get('role')
    )

@app.route('/admin/select_buyer/<bid_id>', methods=['POST'])
def select_buyer(bid_id):
    """Select buyer and submit for A1 approval"""
    if session.get('role') != 'Vendor':
        flash('Access denied. Admin role required.', 'danger')
        return redirect(url_for('index'))
    
    submission_id = request.form['submission_id']
    justification = request.form['justification']
    vendor_name = session.get('user_name', 'Vendor')

    success, detail = db.select_buyer_and_submit_for_approval(bid_id, submission_id, justification, vendor_name)
    if not success:
        flash(detail, 'danger')
        return redirect(url_for('vendor_view_bid', bid_id=bid_id))

    buyer = db.get_buyer_by_id(detail)
    buyer_label = buyer['buyer_name'] if buyer else detail
    flash(f'Submission {submission_id} from {buyer_label} submitted for A1 approval!', 'success')
    
    return redirect(url_for('vendor_view_bid', bid_id=bid_id))

@app.route('/buyer/dashboard')
def buyer_dashboard():
    """Buyer Dashboard"""
    if session.get('role') != 'Buyer':
        flash('Access denied. Buyer role required.', 'danger')
        return redirect(url_for('index'))
    
    if 'buyer_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('buyer_login_page'))
    
    bids = db.get_all_bids()
    buyer_id = session.get('buyer_id', '')

    if bids.empty:
        assigned_bids = bids
    else:
        bids = bids.copy()
        if 'selected_buyer_id' not in bids.columns:
            bids['selected_buyer_id'] = ''
        if 'buyer_comment' not in bids.columns:
            bids['buyer_comment'] = ''
        if 'submission_date' not in bids.columns:
            bids['submission_date'] = ''
        if 'status' not in bids.columns:
            bids['status'] = ''
        assigned_bids = bids[bids['selected_buyer_id'].astype(str).str.strip() == str(buyer_id).strip()]

    if bids.empty:
        assigned_bids = bids

    return render_template('buyer_dashboard.html', bids=assigned_bids, role=session.get('role'))

@app.route('/buyer/view_bid/<bid_id>')
def buyer_view_bid(bid_id):
    """View bid details for buyer"""
    if session.get('role') != 'Buyer':
        flash('Access denied. Buyer role required.', 'danger')
        return redirect(url_for('index'))
    
    if 'buyer_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('buyer_login_page'))
    
    raw_bid = db.get_bid_by_id(bid_id)
    if not raw_bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('a2_dashboard'))

    bid = normalize_bid_record(raw_bid)
    items = db.get_items_for_bid(bid_id)
    buyer = db.get_buyer_by_id(session.get('buyer_id'))
    history = db.get_history_for_bid(bid_id)

    assigned_buyer_id = str(bid.get('selected_buyer_id', '')).strip()
    if assigned_buyer_id != str(session.get('buyer_id', '')).strip():
        flash('You are not assigned to this bid.', 'danger')
        return redirect(url_for('buyer_dashboard'))

    can_submit = bid.get('status') in {'Awaiting Buyer', 'Draft', 'Under Review'}
    
    # Get all bidder submissions
    bidder_submissions = db.get_all_bidder_bids_with_totals(bid_id)
    num_bidders = len(bidder_submissions)
    
    return render_template('buyer_view_bid.html', bid=bid, items=items, 
                          buyer=buyer, history=history, role=session.get('role'), can_submit=can_submit,
                          bidder_submissions=bidder_submissions, num_bidders=num_bidders)

@app.route('/buyer/submit_bid/<bid_id>', methods=['POST'])
def submit_bid(bid_id):
    """Submit buyer bid"""
    if session.get('role') != 'Buyer':
        flash('Access denied. Buyer role required.', 'danger')
        return redirect(url_for('index'))
    
    buyer_id = session.get('buyer_id')
    buyer_comment = request.form.get('buyer_comment', '').strip()

    if not buyer_comment:
        flash('Please provide a comment before submitting.', 'danger')
        return redirect(url_for('buyer_view_bid', bid_id=bid_id))

    success, error = db.buyer_submit_comment(bid_id, buyer_id, buyer_comment)
    if not success:
        flash(error, 'danger')
        return redirect(url_for('buyer_view_bid', bid_id=bid_id))

    flash('Response submitted successfully! Bid sent to A1 approval.', 'success')
    
    return redirect(url_for('buyer_dashboard'))

@app.route('/a1/dashboard')
def a1_dashboard():
    """A1 Approver Dashboard"""
    if session.get('role') != 'A1 Approver':
        flash('Access denied. A1 Approver role required.', 'danger')
        return redirect(url_for('index'))
    
    bids = db.get_all_bids()
    # Show all bids with priority to pending ones
    return render_template('a1_dashboard.html', bids=bids, role=session.get('role'))

@app.route('/a1/view_bid/<bid_id>')
def a1_view_bid(bid_id):
    """View bid for A1 approval"""
    if session.get('role') != 'A1 Approver':
        flash('Access denied. A1 Approver role required.', 'danger')
        return redirect(url_for('index'))
    
    raw_bid = db.get_bid_by_id(bid_id)
    if not raw_bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('a1_dashboard'))

    bid = normalize_bid_record(raw_bid)
    
    history = db.get_history_for_bid(bid_id)
    items = db.get_items_for_bid(bid_id)
    assigned_buyer = None
    assigned_buyer_id = str(bid.get('selected_buyer_id', '')).strip()
    if assigned_buyer_id:
        assigned_buyer = db.get_buyer_by_id(assigned_buyer_id)
    
    # Get all bidder submissions
    bidder_submissions = db.get_all_bidder_bids_with_totals(bid_id)
    num_bidders = len(bidder_submissions)
    
    return render_template('a1_view_bid.html', bid=bid, assigned_buyer=assigned_buyer,
                          history=history, items=items, role=session.get('role'),
                          bidder_submissions=bidder_submissions, num_bidders=num_bidders)

@app.route('/a1/approve/<bid_id>', methods=['POST'])
def a1_approve_bid(bid_id):
    """A1 approve bid"""
    if session.get('role') != 'A1 Approver':
        flash('Access denied. A1 Approver role required.', 'danger')
        return redirect(url_for('index'))
    
    # Check if bid has been submitted for approval
    bid = db.get_bid_by_id(bid_id)
    if not bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('a1_dashboard'))
    if bid['status'] != 'Pending A1':
        flash('This bid has not been submitted for approval yet!', 'danger')
        return redirect(url_for('a1_dashboard'))
    
    comment = request.form['comment']
    approver_name = session.get('user_name', 'A1 Approver')
    
    db.a1_approve(bid_id, comment, approver_name)
    flash('Bid approved and sent to A2 Approver!', 'success')
    
    return redirect(url_for('a1_dashboard'))

@app.route('/a1/reject/<bid_id>', methods=['POST'])
def a1_reject_bid(bid_id):
    """A1 reject bid"""
    if session.get('role') != 'A1 Approver':
        flash('Access denied. A1 Approver role required.', 'danger')
        return redirect(url_for('index'))
    
    # Check if bid has been submitted for approval
    bid = db.get_bid_by_id(bid_id)
    if not bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('a1_dashboard'))
    if bid['status'] != 'Pending A1':
        flash('This bid has not been submitted for approval yet!', 'danger')
        return redirect(url_for('a1_dashboard'))
    
    comment = request.form['comment']
    approver_name = session.get('user_name', 'A1 Approver')
    
    db.a1_reject(bid_id, comment, approver_name)
    flash('Bid rejected and sent back to Admin!', 'warning')
    
    return redirect(url_for('a1_dashboard'))

@app.route('/a2/dashboard')
def a2_dashboard():
    """A2 Approver Dashboard"""
    if session.get('role') != 'A2 Approver':
        flash('Access denied. A2 Approver role required.', 'danger')
        return redirect(url_for('index'))
    
    bids = db.get_all_bids()
    # Show all bids with priority to pending ones
    return render_template('a2_dashboard.html', bids=bids, role=session.get('role'))

@app.route('/a2/view_bid/<bid_id>')
def a2_view_bid(bid_id):
    """View bid for A2 approval"""
    if session.get('role') != 'A2 Approver':
        flash('Access denied. A2 Approver role required.', 'danger')
        return redirect(url_for('index'))
    
    bid = db.get_bid_by_id(bid_id)
    if not bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('a2_dashboard'))
    
    history = db.get_history_for_bid(bid_id)
    items = db.get_items_for_bid(bid_id)
    assigned_buyer = None
    assigned_buyer_id = str(bid.get('selected_buyer_id', '')).strip()
    if assigned_buyer_id:
        assigned_buyer = db.get_buyer_by_id(assigned_buyer_id)
    
    # Get all bidder submissions
    bidder_submissions = db.get_all_bidder_bids_with_totals(bid_id)
    num_bidders = len(bidder_submissions)
    
    return render_template('a2_view_bid.html', bid=bid, assigned_buyer=assigned_buyer,
                          history=history, items=items, role=session.get('role'),
                          bidder_submissions=bidder_submissions, num_bidders=num_bidders)

@app.route('/a2/approve/<bid_id>', methods=['POST'])
def a2_approve_bid(bid_id):
    """A2 approve bid (final approval)"""
    if session.get('role') != 'A2 Approver':
        flash('Access denied. A2 Approver role required.', 'danger')
        return redirect(url_for('index'))
    
    # Check if bid has been approved by A1
    bid = db.get_bid_by_id(bid_id)
    if not bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('a2_dashboard'))
    if bid['status'] != 'Pending A2':
        flash('This bid has not been approved by A1 yet!', 'danger')
        return redirect(url_for('a2_dashboard'))
    
    comment = request.form['comment']
    approver_name = session.get('user_name', 'A2 Approver')
    
    db.a2_approve(bid_id, comment, approver_name)
    flash('Bid approved! Final approval completed.', 'success')
    
    return redirect(url_for('a2_dashboard'))

@app.route('/a2/reject/<bid_id>', methods=['POST'])
def a2_reject_bid(bid_id):
    """A2 reject bid"""
    if session.get('role') != 'A2 Approver':
        flash('Access denied. A2 Approver role required.', 'danger')
        return redirect(url_for('index'))
    
    # Check if bid has been approved by A1
    bid = db.get_bid_by_id(bid_id)
    if not bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('a2_dashboard'))
    if bid['status'] != 'Pending A2':
        flash('This bid has not been approved by A1 yet!', 'danger')
        return redirect(url_for('a2_dashboard'))
    
    comment = request.form['comment']
    approver_name = session.get('user_name', 'A2 Approver')
    
    db.a2_reject(bid_id, comment, approver_name)
    flash('Bid rejected and sent back to A1 Approver!', 'warning')
    
    return redirect(url_for('a2_dashboard'))

@app.route('/a2/reopen/<bid_id>', methods=['POST'])
def a2_reopen_bid(bid_id):
    """A2 reopen approved bid for modifications"""
    if session.get('role') != 'A2 Approver':
        flash('Access denied. A2 Approver role required.', 'danger')
        return redirect(url_for('index'))
    
    # Check if bid is approved
    bid = db.get_bid_by_id(bid_id)
    if not bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('a2_dashboard'))
    if bid['status'] != 'Approved':
        flash('Only approved bids can be reopened!', 'danger')
        return redirect(url_for('a2_dashboard'))
    
    comment = request.form['comment']
    approver_name = session.get('user_name', 'A2 Approver')
    
    db.a2_reopen_bid(bid_id, comment, approver_name)
    flash('Bid has been reopened for modifications!', 'info')
    
    return redirect(url_for('a2_dashboard'))

@app.route('/download_pdf/<bid_id>')
def download_pdf(bid_id):
    """Download bid comparison PDF - Accessible by all roles"""
    bid = db.get_bid_by_id(bid_id)
    if not bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('index'))
    
    bid = normalize_bid_record(bid)
    history = db.get_history_for_bid(bid_id)
    items = db.get_items_for_bid(bid_id)
    
    # Get bidder submissions for each item
    bidder_submissions = {}
    all_bidders = set()
    if not items.empty:
        for _, item in items.iterrows():
            item_bids = db.get_bidder_bids_for_item(bid_id, item['item_id'])
            bidder_submissions[item['item_id']] = item_bids
            if not item_bids.empty:
                for _, bid_sub in item_bids.iterrows():
                    all_bidders.add(bid_sub['bidder_id'])
    
    # Get bidder names
    bidder_names = {}
    for bidder_id in all_bidders:
        bidder = db.get_bidder_by_id(bidder_id)
        if bidder:
            bidder_names[bidder_id] = bidder['bidder_name']
        else:
            bidder_names[bidder_id] = bidder_id
    
    # Create Professional PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    def draw_header(canvas_obj, y_start):
        """Draw professional header"""
        canvas_obj.setFillColorRGB(0.2, 0.3, 0.5)
        canvas_obj.rect(0, y_start - 0.8*inch, width, 0.8*inch, fill=1)
        canvas_obj.setFillColorRGB(1, 1, 1)
        canvas_obj.setFont("Helvetica-Bold", 20)
        canvas_obj.drawCentredString(width/2, y_start - 0.5*inch, "BID COMPARISON REPORT")
        canvas_obj.setFillColorRGB(0, 0, 0)
        return y_start - 1*inch
    
    def draw_section(canvas_obj, y_pos, title):
        """Draw section header"""
        canvas_obj.setFillColorRGB(0.2, 0.3, 0.5)
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(0.75*inch, y_pos, title)
        canvas_obj.setStrokeColorRGB(0.2, 0.3, 0.5)
        canvas_obj.setLineWidth(2)
        canvas_obj.line(0.75*inch, y_pos - 5, width - 0.75*inch, y_pos - 5)
        canvas_obj.setFillColorRGB(0, 0, 0)
        canvas_obj.setStrokeColorRGB(0, 0, 0)
        canvas_obj.setLineWidth(1)
        return y_pos - 0.3*inch
    
    def draw_field(canvas_obj, y_pos, label, value, bold_label=True):
        """Draw a label-value pair"""
        label_font = "Helvetica-Bold" if bold_label else "Helvetica"
        value_font = "Helvetica"
        font_size = 10

        label_text = f"{label}:" if label else ""
        canvas_obj.setFont(label_font, font_size)
        if label_text:
            canvas_obj.drawString(1 * inch, y_pos, label_text)

        value_str = str(value) if value not in (None, "") else "N/A"
        label_width = canvas_obj.stringWidth(label_text, label_font, font_size) if label_text else 0
        value_x = 1 * inch + label_width + (0.12 * inch if label_text else 0)
        
        canvas_obj.setFont(value_font, font_size)
        canvas_obj.drawString(value_x, y_pos, value_str)
        return y_pos - 0.25 * inch
    
    # PAGE 1
    y = draw_header(c, height)
    y -= 0.3*inch
    
    # Contract Information
    y = draw_section(c, y, "1. CONTRACT INFORMATION")
    y = draw_field(c, y, "Bid ID", bid['bid_id'])
    y = draw_field(c, y, "Contract Name", bid['contract_name'])
    y = draw_field(c, y, "Description", bid['contract_description'])
    y = draw_field(c, y, "Contract Value", f"${bid['contract_value']:,.2f}")
    y = draw_field(c, y, "Created By", bid['vendor_name'])
    y = draw_field(c, y, "Created Date", bid['created_date'])
    y = draw_field(c, y, "Status", bid['status'])
    
    # Get assigned buyer info
    selected_buyer_id = str(sanitize_excel_value(bid.get('selected_buyer_id'), '')).strip()
    assigned_buyer = db.get_buyer_by_id(selected_buyer_id) if selected_buyer_id else None
    if assigned_buyer:
        assigned_buyer_label = f"{assigned_buyer.get('buyer_name', 'N/A')} ({selected_buyer_id})"
    else:
        assigned_buyer_label = "Not Assigned"
    y = draw_field(c, y, "Assigned Buyer", assigned_buyer_label)
    y -= 0.3*inch
    
    # Bid Items and Comparison in Tabular Form
    if not items.empty and all_bidders:
        if y < 5*inch:
            c.showPage()
            y = draw_header(c, height) - 0.3*inch
            
        y = draw_section(c, y, "2. BID ITEMS & BIDDER COMPARISON")
        y -= 0.2*inch
        
        # Calculate column widths based on number of bidders
        bidders_list = sorted(list(all_bidders))
        num_bidders = len(bidders_list)
        
        # Improved table layout
        item_col_width = 2.5*inch
        qty_col_width = 0.4*inch
        unit_col_width = 0.6*inch
        available_width = width - 2*0.75*inch - item_col_width - qty_col_width - unit_col_width
        bidder_col_width = available_width / num_bidders if num_bidders > 0 else 1.5*inch
        
        x_start = 0.75*inch
        table_width = width - 1.5*inch
        
        # Draw table header with better styling
        header_height = 0.5*inch
        c.setFillColorRGB(0.2, 0.3, 0.5)  # Dark blue header
        c.rect(x_start, y - header_height, table_width, header_height, fill=1, stroke=1)
        c.setFillColorRGB(1, 1, 1)  # White text
        c.setFont("Helvetica-Bold", 9)
        
        x = x_start + 0.05*inch
        # Multi-line header for Item column
        c.drawString(x, y - 0.2*inch, "Item Name")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x, y - 0.35*inch, "Description")
        
        x += item_col_width
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x, y - 0.27*inch, "Qty")
        
        x += qty_col_width
        c.drawString(x, y - 0.27*inch, "Unit")
        
        x += unit_col_width
        
        # Bidder columns with better formatting
        c.setFont("Helvetica-Bold", 8)
        for bidder_id in bidders_list:
            bidder_name = bidder_names.get(bidder_id, bidder_id)
            # Smart truncation
            if len(bidder_name) > 18:
                bidder_name = bidder_name[:15] + "..."
            c.drawString(x + 0.05*inch, y - 0.18*inch, bidder_name)
            c.setFont("Helvetica", 7)
            c.drawString(x + 0.05*inch, y - 0.35*inch, "Rate | Total")
            c.setFont("Helvetica-Bold", 8)
            x += bidder_col_width
        
        y -= (header_height + 0.05*inch)
        
        # Draw items rows with improved formatting
        for idx, item in items.iterrows():
            if y < 1.5*inch:
                c.showPage()
                y = draw_header(c, height) - 0.3*inch
                # Redraw header on new page
                c.setFillColorRGB(0.2, 0.3, 0.5)
                c.rect(x_start, y - header_height, table_width, header_height, fill=1, stroke=1)
                c.setFillColorRGB(1, 1, 1)
                c.setFont("Helvetica-Bold", 9)
                x = x_start + 0.05*inch
                c.drawString(x, y - 0.2*inch, "Item Name")
                c.setFont("Helvetica-Bold", 8)
                c.drawString(x, y - 0.35*inch, "Description")
                x += item_col_width
                c.setFont("Helvetica-Bold", 9)
                c.drawString(x, y - 0.27*inch, "Qty")
                x += qty_col_width
                c.drawString(x, y - 0.27*inch, "Unit")
                x += unit_col_width
                c.setFont("Helvetica-Bold", 8)
                for bidder_id in bidders_list:
                    bidder_name = bidder_names.get(bidder_id, bidder_id)
                    if len(bidder_name) > 18:
                        bidder_name = bidder_name[:15] + "..."
                    c.drawString(x + 0.05*inch, y - 0.18*inch, bidder_name)
                    c.setFont("Helvetica", 7)
                    c.drawString(x + 0.05*inch, y - 0.35*inch, "Rate | Total")
                    c.setFont("Helvetica-Bold", 8)
                    x += bidder_col_width
                y -= (header_height + 0.05*inch)
            
            row_height = 0.45*inch
            
            # Draw row background with alternating colors
            if idx % 2 == 0:
                c.setFillColorRGB(0.97, 0.97, 0.97)
            else:
                c.setFillColorRGB(1, 1, 1)
            c.rect(x_start, y - row_height, table_width, row_height, fill=1, stroke=0)
            
            # Draw row border
            c.setFillColorRGB(0, 0, 0)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.setLineWidth(0.5)
            c.rect(x_start, y - row_height, table_width, row_height, fill=0, stroke=1)
            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(1)
            
            x = x_start + 0.05*inch
            
            # Item name and description with better formatting
            c.setFont("Helvetica-Bold", 9)
            item_name = str(item['item_name'])
            if len(item_name) > 35:
                item_name = item_name[:32] + "..."
            c.drawString(x, y - 0.17*inch, item_name)
            
            c.setFont("Helvetica", 7)
            item_desc = str(item['item_description'])
            if len(item_desc) > 45:
                item_desc = item_desc[:42] + "..."
            c.drawString(x, y - 0.32*inch, item_desc)
            
            x += item_col_width
            
            # Quantity
            c.setFont("Helvetica", 9)
            c.drawString(x, y - 0.25*inch, f"{item['quantity']}")
            x += qty_col_width
            
            # Unit
            unit_text = str(item['unit'])
            if len(unit_text) > 6:
                unit_text = unit_text[:5] + "."
            c.drawString(x, y - 0.25*inch, unit_text)
            x += unit_col_width
            
            # Bidder rates with better formatting
            item_bids = bidder_submissions.get(item['item_id'])
            for bidder_id in bidders_list:
                rate_text = "N/A"
                total_text = ""
                
                if item_bids is not None and not item_bids.empty:
                    bidder_bid = item_bids[item_bids['bidder_id'] == bidder_id]
                    if not bidder_bid.empty:
                        unit_rate = float(bidder_bid.iloc[0]['unit_rate'])
                        total = unit_rate * float(item['quantity'])
                        rate_text = f"${unit_rate:,.2f}"
                        total_text = f"${total:,.2f}"
                
                c.setFont("Helvetica-Bold", 8)
                c.drawString(x + 0.05*inch, y - 0.17*inch, rate_text)
                if total_text:
                    c.setFont("Helvetica", 7)
                    c.setFillColorRGB(0.3, 0.3, 0.3)
                    c.drawString(x + 0.05*inch, y - 0.32*inch, total_text)
                    c.setFillColorRGB(0, 0, 0)
                
                x += bidder_col_width
            
            y -= row_height
        
        # Add total row
        c.setFillColorRGB(0.9, 0.9, 0.9)
        total_row_height = 0.35*inch
        c.rect(x_start, y - total_row_height, table_width, total_row_height, fill=1, stroke=1)
        c.setFillColorRGB(0, 0, 0)
        
        x = x_start + 0.05*inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y - 0.22*inch, "TOTAL BID AMOUNTS:")
        
        x = x_start + item_col_width + qty_col_width + unit_col_width
        
        # Calculate and show totals for each bidder
        for bidder_id in bidders_list:
            total_amount = 0
            if not items.empty:
                for _, item in items.iterrows():
                    item_bids = bidder_submissions.get(item['item_id'])
                    if item_bids is not None and not item_bids.empty:
                        bidder_bid = item_bids[item_bids['bidder_id'] == bidder_id]
                        if not bidder_bid.empty:
                            unit_rate = float(bidder_bid.iloc[0]['unit_rate'])
                            total_amount += unit_rate * float(item['quantity'])
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(x + 0.05*inch, y - 0.22*inch, f"${total_amount:,.2f}")
            x += bidder_col_width
        
        y -= (total_row_height + 0.3*inch)
    
    # Check if we need a new page
    if y < 4*inch:
        c.showPage()
        y = draw_header(c, height) - 0.3*inch
    
    # Approval Workflow
    y = draw_section(c, y, "3. APPROVAL WORKFLOW")
    y -= 0.1*inch
    
    # Buyer Comments
    buyer_comment = bid.get('buyer_comment', '').strip()
    if buyer_comment:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*inch, y, "Buyer Comments")
        y -= 0.2*inch
        y = draw_field(c, y, "Buyer", assigned_buyer_label if assigned_buyer else "N/A")
        y = draw_field(c, y, "Comment", buyer_comment)
        y = draw_field(c, y, "Submitted On", bid.get('submission_date') or 'Not submitted')
        y -= 0.2*inch
    
    # A1 Approval
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1*inch, y, "Level 1 Approval (A1)")
    y -= 0.2*inch
    y = draw_field(c, y, "Status", bid['a1_status'])
    y = draw_field(c, y, "Comment", bid['a1_comment'])
    y = draw_field(c, y, "Date", bid['a1_date'])
    y -= 0.2*inch
    
    # A2 Approval
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1*inch, y, "Level 2 Approval (A2) - FINAL")
    y -= 0.2*inch
    y = draw_field(c, y, "Status", bid['a2_status'])
    y = draw_field(c, y, "Comment", bid['a2_comment'])
    y = draw_field(c, y, "Date", bid['a2_date'])
    y -= 0.3*inch
    
    # Final Status Box
    final_status = bid.get('status', 'Unknown')
    
    # Determine status color
    status_color = (0.9, 0.9, 0.9)  # Default gray
    if final_status == 'Approved':
        status_color = (0.2, 0.7, 0.3)  # Green
    elif final_status == 'Rejected':
        status_color = (0.8, 0.2, 0.2)  # Red
    elif final_status in ['Pending', 'Submitted', 'Under Review']:
        status_color = (0.95, 0.7, 0.2)  # Orange
    
    # Draw final status box with border
    box_width = 3*inch
    box_height = 0.5*inch
    x_center = (width - box_width) / 2
    
    # Draw outer border (darker)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(2)
    c.setFillColorRGB(*status_color)
    c.rect(x_center, y - box_height, box_width, box_height, fill=1, stroke=1)
    
    # Draw text
    c.setFillColorRGB(1, 1, 1)  # White text
    c.setFont("Helvetica-Bold", 14)
    text_width = c.stringWidth(f"FINAL STATUS: {final_status.upper()}", "Helvetica-Bold", 14)
    c.drawString(x_center + (box_width - text_width) / 2, y - 0.32*inch, f"FINAL STATUS: {final_status.upper()}")
    
    # Reset colors
    c.setFillColorRGB(0, 0, 0)
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    
    y -= (box_height + 0.3*inch)
    
    # Check if we need a new page for audit trail
    if y < 3*inch:
        c.showPage()
        y = draw_header(c, height) - 0.3*inch
    
    # Audit Trail
    y = draw_section(c, y, "4. AUDIT TRAIL")
    y -= 0.1*inch
    
    if not history.empty:
        c.setFont("Helvetica", 8)
        for idx, record in history.iterrows():
            if y < 1.5*inch:
                c.showPage()
                y = draw_header(c, height) - 0.3*inch
            
            c.setFont("Helvetica-Bold", 9)
            c.drawString(1*inch, y, f"{record['action_date']} - {record['action']}")
            y -= 0.15*inch
            c.setFont("Helvetica", 8)
            c.drawString(1.2*inch, y, f"By: {record['action_by']} ({record['role']})")
            y -= 0.12*inch
            if record['comment']:
                comment_str = str(record['comment'])
                if len(comment_str) > 80:
                    comment_str = comment_str[:77] + "..."
                c.drawString(1.2*inch, y, f"Comment: {comment_str}")
                y -= 0.12*inch
            if record['previous_status'] or record['new_status']:
                prev_status = record['previous_status'] if record['previous_status'] else 'None'
                new_status = record['new_status'] if record['new_status'] else 'None'
                c.drawString(1.2*inch, y, f"Status: {prev_status} → {new_status}")
                y -= 0.12*inch
            y -= 0.1*inch
    else:
        c.setFont("Helvetica-Oblique", 9)
        c.drawString(1*inch, y, "No audit trail records found")
        y -= 0.3*inch
    
    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(0.75*inch, 0.5*inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawRightString(width - 0.75*inch, 0.5*inch, f"Document: {bid['bid_id']}_Comparison.pdf")
    
    c.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"bid_{bid_id}_comparison.pdf", 
                     mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
