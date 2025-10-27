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
ROLES = ['Admin', 'Vendor', 'A1 Approver', 'A2 Approver']


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
        'selected_vendor_id',
        'selected_submission_id',
        'admin_justification',
        'vendor_comment',
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


def prepare_vendor_bids(bid_id):
    """Fetch vendor submissions with consistent typing and metadata"""
    vendor_bids = db.get_vendor_bids_for_bid(bid_id)
    if vendor_bids.empty:
        return vendor_bids, {}

    vendor_bids = vendor_bids.copy()
    if 'submission_id' not in vendor_bids.columns:
        vendor_bids['submission_id'] = ''
    vendor_bids['submission_id'] = vendor_bids['submission_id'].fillna('').astype(str).str.strip()

    if 'vendor_id' not in vendor_bids.columns:
        vendor_bids['vendor_id'] = ''
    vendor_bids['vendor_id'] = vendor_bids['vendor_id'].fillna('').astype(str).str.strip()

    if 'is_selected' not in vendor_bids.columns:
        vendor_bids['is_selected'] = False
    vendor_bids['is_selected'] = vendor_bids['is_selected'].apply(_normalize_bool_flag)

    vendor_lookup = {}
    for vid in vendor_bids['vendor_id'].unique():
        vendor = db.get_vendor_by_id(vid)
        if vendor:
            vendor_lookup[vid] = vendor

    return vendor_bids, vendor_lookup


def get_selected_submission(bid_record, vendor_bids):
    """Locate the DataFrame row for the winning submission"""
    if vendor_bids.empty:
        return vendor_bids

    selected_submission_id = str(sanitize_excel_value(bid_record.get('selected_submission_id'), '')).strip()
    selected_vendor_id = str(sanitize_excel_value(bid_record.get('selected_vendor_id'), '')).strip()

    if selected_submission_id:
        selected_rows = vendor_bids[vendor_bids['submission_id'] == selected_submission_id]
        if not selected_rows.empty:
            return selected_rows

    selected_rows = vendor_bids[vendor_bids['is_selected'] == True]
    if not selected_rows.empty:
        if selected_vendor_id:
            vendor_match = selected_rows[selected_rows['vendor_id'] == selected_vendor_id]
            if not vendor_match.empty:
                return vendor_match
        return selected_rows

    if selected_vendor_id:
        fallback = vendor_bids[vendor_bids['vendor_id'] == selected_vendor_id]
        if not fallback.empty:
            return fallback

    return vendor_bids.iloc[0:0]

@app.route('/')
def index():
    """Home page - redirect to dashboard based on role"""
    if 'role' not in session:
        session['role'] = 'Admin'
        session['user_name'] = 'Admin User'
    
    role = session.get('role', 'Admin')
    
    if role == 'Admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'Vendor':
        # Check if vendor is logged in
        if 'vendor_id' not in session:
            return redirect(url_for('vendor_login_page'))
        return redirect(url_for('vendor_dashboard'))
    elif role == 'A1 Approver':
        return redirect(url_for('a1_dashboard'))
    elif role == 'A2 Approver':
        return redirect(url_for('a2_dashboard'))
    
    return redirect(url_for('admin_dashboard'))

@app.route('/switch_role/<role>')
def switch_role(role):
    """Switch between roles"""
    if role in ROLES:
        session['role'] = role
        
        # Set appropriate user name based on role
        if role == 'Admin':
            session['user_name'] = 'Admin User'
        elif role == 'Vendor':
            # Clear vendor session when switching to vendor role
            if 'vendor_id' in session:
                del session['vendor_id']
                del session['vendor_name']
            session['user_name'] = 'Vendor User'
        elif role == 'A1 Approver':
            session['user_name'] = 'A1 Approver'
        elif role == 'A2 Approver':
            session['user_name'] = 'A2 Approver'
        
        flash(f'Switched to {role} role', 'success')
    
    return redirect(url_for('index'))

# Vendor Login/Registration Routes
@app.route('/vendor/login', methods=['GET', 'POST'])
def vendor_login_page():
    """Vendor login page"""
    vendors_df = db.get_all_vendors()
    vendors = vendors_df.to_dict('records') if not vendors_df.empty else []
    
    if request.method == 'POST':
        vendor_id = request.form['vendor_id']
        
        vendor = db.get_vendor_by_id(vendor_id)
        if vendor:
            session['vendor_id'] = vendor['vendor_id']
            session['vendor_name'] = vendor['vendor_name']
            session['user_name'] = vendor['vendor_name']
            flash(f'Welcome, {vendor["vendor_name"]}!', 'success')
            return redirect(url_for('vendor_dashboard'))
        else:
            flash('Invalid vendor selection!', 'danger')
    
    return render_template('vendor_login.html', role=session.get('role'), vendors=vendors)

@app.route('/vendor/register', methods=['GET', 'POST'])
def vendor_register():
    """Vendor registration page"""
    if request.method == 'POST':
        vendor_name = request.form['vendor_name']
        contact_email = request.form['contact_email']
        contact_phone = request.form['contact_phone']
        password = request.form['password']
        
        vendor_id = db.create_vendor(vendor_name, contact_email, contact_phone, password)
        
        # Auto login after registration
        session['vendor_id'] = vendor_id
        session['vendor_name'] = vendor_name
        session['user_name'] = vendor_name
        
        flash(f'Registration successful! Your Vendor ID is: {vendor_id}', 'success')
        return redirect(url_for('vendor_dashboard'))
    
    return render_template('vendor_register.html', role=session.get('role'))

@app.route('/vendor/logout')
def vendor_logout():
    """Vendor logout"""
    if 'vendor_id' in session:
        del session['vendor_id']
        del session['vendor_name']
    flash('Logged out successfully!', 'success')
    return redirect(url_for('vendor_login_page'))

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin Dashboard"""
    if session.get('role') != 'Admin':
        flash('Access denied. Admin role required.', 'danger')
        return redirect(url_for('index'))
    
    bids = db.get_all_bids()
    
    # Enrich bids with vendor information
    if not bids.empty:
        vendor_names = []
        vendor_contacts = []
        for index, bid in bids.iterrows():
            vendor_id = str(bid.get('selected_vendor_id', '')).strip()
            if vendor_id:
                vendor = db.get_vendor_by_id(vendor_id)
                if vendor:
                    vendor_names.append(vendor.get('vendor_name', ''))
                    vendor_contacts.append(vendor.get('contact_email', ''))
                else:
                    vendor_names.append('')
                    vendor_contacts.append('')
            else:
                vendor_names.append('')
                vendor_contacts.append('')
        
        bids['vendor_name'] = vendor_names
        bids['vendor_contact'] = vendor_contacts
    
    return render_template('admin_dashboard.html', bids=bids, role=session.get('role'))

@app.route('/admin/create_bid', methods=['GET', 'POST'])
def create_bid():
    """Create new bid"""
    if session.get('role') != 'Admin':
        flash('Access denied. Admin role required.', 'danger')
        return redirect(url_for('index'))

    vendors_df = db.get_all_vendors()
    vendors = vendors_df.to_dict('records') if not vendors_df.empty else []
    
    if request.method == 'POST':
        contract_name = request.form['contract_name']
        contract_description = request.form['contract_description']
        contract_value = float(request.form['contract_value'])
        assigned_vendor_id = request.form.get('assigned_vendor_id', '').strip()
        admin_name = session.get('user_name', 'Admin')
        
        if not assigned_vendor_id:
            flash('Please assign a vendor for this bid.', 'danger')
            return render_template('create_bid.html', role=session.get('role'), vendors=vendors)

        if not any(v['vendor_id'] == assigned_vendor_id for v in vendors):
            flash('Selected vendor could not be found. Please choose a valid vendor.', 'danger')
            return render_template('create_bid.html', role=session.get('role'), vendors=vendors)

        bid_id = db.create_bid(contract_name, contract_description, contract_value, admin_name, assigned_vendor_id)
        
        # Add bid items if provided
        item_names = request.form.getlist('item_name[]')
        item_descriptions = request.form.getlist('item_description[]')
        quantities = request.form.getlist('quantity[]')
        units = request.form.getlist('unit[]')
        
        for i in range(len(item_names)):
            if item_names[i]:  # Only add if item name is provided
                db.add_bid_item(bid_id, item_names[i], item_descriptions[i], 
                              float(quantities[i]) if quantities[i] else 0, units[i])

        selected_vendor = next((v for v in vendors if v.get('vendor_id') == assigned_vendor_id), None)
        vendor_label = selected_vendor['vendor_name'] if selected_vendor else assigned_vendor_id

        flash(f'Bid {bid_id} created and assigned to {vendor_label}!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('create_bid.html', role=session.get('role'), vendors=vendors)

@app.route('/admin/view_bid/<bid_id>')
def admin_view_bid(bid_id):
    """View bid details and vendor submissions"""
    if session.get('role') != 'Admin':
        flash('Access denied. Admin role required.', 'danger')
        return redirect(url_for('index'))
    
    raw_bid = db.get_bid_by_id(bid_id)
    if not raw_bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    bid = normalize_bid_record(raw_bid)
    history = db.get_history_for_bid(bid_id)
    items = db.get_items_for_bid(bid_id)

    assigned_vendor = None
    assigned_vendor_id = str(bid.get('selected_vendor_id', '')).strip()
    if assigned_vendor_id:
        assigned_vendor = db.get_vendor_by_id(assigned_vendor_id)

    return render_template(
        'admin_view_bid.html',
        bid=bid,
        assigned_vendor=assigned_vendor,
        history=history,
        items=items,
        role=session.get('role')
    )

@app.route('/admin/select_vendor/<bid_id>', methods=['POST'])
def select_vendor(bid_id):
    """Select vendor and submit for A1 approval"""
    if session.get('role') != 'Admin':
        flash('Access denied. Admin role required.', 'danger')
        return redirect(url_for('index'))
    
    submission_id = request.form['submission_id']
    justification = request.form['justification']
    admin_name = session.get('user_name', 'Admin')

    success, detail = db.select_vendor_and_submit_for_approval(bid_id, submission_id, justification, admin_name)
    if not success:
        flash(detail, 'danger')
        return redirect(url_for('admin_view_bid', bid_id=bid_id))

    vendor = db.get_vendor_by_id(detail)
    vendor_label = vendor['vendor_name'] if vendor else detail
    flash(f'Submission {submission_id} from {vendor_label} submitted for A1 approval!', 'success')
    
    return redirect(url_for('admin_view_bid', bid_id=bid_id))

@app.route('/vendor/dashboard')
def vendor_dashboard():
    """Vendor Dashboard"""
    if session.get('role') != 'Vendor':
        flash('Access denied. Vendor role required.', 'danger')
        return redirect(url_for('index'))
    
    if 'vendor_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('vendor_login_page'))
    
    bids = db.get_all_bids()
    vendor_id = session.get('vendor_id', '')

    if bids.empty:
        assigned_bids = bids
    else:
        bids = bids.copy()
        if 'selected_vendor_id' not in bids.columns:
            bids['selected_vendor_id'] = ''
        if 'vendor_comment' not in bids.columns:
            bids['vendor_comment'] = ''
        if 'submission_date' not in bids.columns:
            bids['submission_date'] = ''
        if 'status' not in bids.columns:
            bids['status'] = ''
        assigned_bids = bids[bids['selected_vendor_id'].astype(str).str.strip() == str(vendor_id).strip()]

    if bids.empty:
        assigned_bids = bids

    return render_template('vendor_dashboard.html', bids=assigned_bids, role=session.get('role'))

@app.route('/vendor/view_bid/<bid_id>')
def vendor_view_bid(bid_id):
    """View bid details for vendor"""
    if session.get('role') != 'Vendor':
        flash('Access denied. Vendor role required.', 'danger')
        return redirect(url_for('index'))
    
    if 'vendor_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('vendor_login_page'))
    
    raw_bid = db.get_bid_by_id(bid_id)
    if not raw_bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('a2_dashboard'))

    bid = normalize_bid_record(raw_bid)
    items = db.get_items_for_bid(bid_id)
    vendor = db.get_vendor_by_id(session.get('vendor_id'))
    history = db.get_history_for_bid(bid_id)

    assigned_vendor_id = str(bid.get('selected_vendor_id', '')).strip()
    if assigned_vendor_id != str(session.get('vendor_id', '')).strip():
        flash('You are not assigned to this bid.', 'danger')
        return redirect(url_for('vendor_dashboard'))

    can_submit = bid.get('status') in {'Awaiting Vendor', 'Draft', 'Under Review'}
    
    return render_template('vendor_view_bid.html', bid=bid, items=items, 
                          vendor=vendor, history=history, role=session.get('role'), can_submit=can_submit)

@app.route('/vendor/submit_bid/<bid_id>', methods=['POST'])
def submit_bid(bid_id):
    """Submit vendor bid"""
    if session.get('role') != 'Vendor':
        flash('Access denied. Vendor role required.', 'danger')
        return redirect(url_for('index'))
    
    vendor_id = session.get('vendor_id')
    vendor_comment = request.form.get('vendor_comment', '').strip()

    if not vendor_comment:
        flash('Please provide a comment before submitting.', 'danger')
        return redirect(url_for('vendor_view_bid', bid_id=bid_id))

    success, error = db.vendor_submit_comment(bid_id, vendor_id, vendor_comment)
    if not success:
        flash(error, 'danger')
        return redirect(url_for('vendor_view_bid', bid_id=bid_id))

    flash('Response submitted successfully! Bid sent to A1 approval.', 'success')
    
    return redirect(url_for('vendor_dashboard'))

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

    # Check if bid has been submitted for approval
    if bid['status'] not in ['Pending A1', 'Pending A2', 'Approved', 'Rejected']:
        flash('This bid has not been submitted for approval yet!', 'warning')
        return redirect(url_for('a1_dashboard'))
    
    history = db.get_history_for_bid(bid_id)
    items = db.get_items_for_bid(bid_id)
    assigned_vendor = None
    assigned_vendor_id = str(bid.get('selected_vendor_id', '')).strip()
    if assigned_vendor_id:
        assigned_vendor = db.get_vendor_by_id(assigned_vendor_id)
    
    return render_template('a1_view_bid.html', bid=bid, assigned_vendor=assigned_vendor,
                          history=history, items=items, role=session.get('role'))

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
    
    # Check if bid has been approved by A1
    if bid['status'] not in ['Pending A2', 'Approved', 'Rejected']:
        flash('This bid has not been approved by A1 yet!', 'warning')
        return redirect(url_for('a2_dashboard'))
    
    history = db.get_history_for_bid(bid_id)
    items = db.get_items_for_bid(bid_id)
    assigned_vendor = None
    assigned_vendor_id = str(bid.get('selected_vendor_id', '')).strip()
    if assigned_vendor_id:
        assigned_vendor = db.get_vendor_by_id(assigned_vendor_id)
    
    return render_template('a2_view_bid.html', bid=bid, assigned_vendor=assigned_vendor,
                          history=history, items=items, role=session.get('role'))

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
    """Download bid approval PDF - Accessible by all roles"""
    bid = db.get_bid_by_id(bid_id)
    if not bid:
        flash('Bid not found.', 'danger')
        return redirect(url_for('index'))
    
    if bid['status'] != 'Approved':
        flash('PDF download only available for approved bids!', 'danger')
        return redirect(url_for('index'))
    
    bid = normalize_bid_record(bid)
    vendor_bids, vendors_dict = prepare_vendor_bids(bid_id)
    selected_vendor = get_selected_submission(bid, vendor_bids)
    selected_submission_id = str(sanitize_excel_value(bid.get('selected_submission_id'), '')).strip()
    selected_vendor_id = str(sanitize_excel_value(bid.get('selected_vendor_id'), '')).strip()
    history = db.get_history_for_bid(bid_id)
    items = db.get_items_for_bid(bid_id)
    
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
        canvas_obj.drawCentredString(width/2, y_start - 0.5*inch, "BID APPROVAL DOCUMENT")
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
        """Draw a label-value pair with automatic wrapping"""
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
        max_width_points = width - value_x - 0.75 * inch
        max_width_points = max(max_width_points, 2 * inch)

        approx_char_width = canvas_obj.stringWidth("X", value_font, font_size) or 5
        max_chars_per_line = max(int(max_width_points / approx_char_width), 10)

        wrapped_lines = textwrap.wrap(value_str, max_chars_per_line) or [value_str]
        canvas_obj.setFont(value_font, font_size)

        current_y = y_pos
        for idx, line in enumerate(wrapped_lines):
            if idx > 0:
                current_y -= 0.18 * inch
            canvas_obj.drawString(value_x, current_y, line)
        return current_y - 0.25 * inch
    
    # PAGE 1
    y = draw_header(c, height)
    y -= 0.3*inch
    
    # Contract Information
    y = draw_section(c, y, "1. CONTRACT INFORMATION")
    y = draw_field(c, y, "Bid ID", bid['bid_id'])
    y = draw_field(c, y, "Contract Name", bid['contract_name'])
    y = draw_field(c, y, "Description", bid['contract_description'])
    y = draw_field(c, y, "Contract Value", f"${bid['contract_value']:,.2f}")
    y = draw_field(c, y, "Created By", bid['admin_name'])
    y = draw_field(c, y, "Created Date", bid['created_date'])
    assigned_vendor = db.get_vendor_by_id(selected_vendor_id) if selected_vendor_id else None
    if assigned_vendor:
        assigned_vendor_label = f"{assigned_vendor.get('vendor_name', 'N/A')} ({selected_vendor_id})"
    else:
        assigned_vendor_label = "Not Assigned"
    y = draw_field(c, y, "Assigned Vendor", assigned_vendor_label)
    y -= 0.2*inch
    
    # Bid Items
    if not items.empty:
        y = draw_section(c, y, "2. BID ITEMS")
        c.setFont("Helvetica-Bold", 9)
        c.drawString(1*inch, y, "Item")
        c.drawString(3*inch, y, "Description")
        c.drawString(5*inch, y, "Quantity")
        c.drawString(6*inch, y, "Unit")
        y -= 0.15*inch
        c.setFont("Helvetica", 9)
        for idx, item in items.iterrows():
            if y < 1.5*inch:
                c.showPage()
                y = draw_header(c, height) - 0.3*inch
            c.drawString(1*inch, y, str(item['item_name'])[:20])
            c.drawString(3*inch, y, str(item['item_description'])[:20])
            c.drawString(5*inch, y, str(item['quantity']))
            c.drawString(6*inch, y, str(item['unit']))
            y -= 0.2*inch
        y -= 0.2*inch
    
    # Check if we need a new page
    if y < 3*inch:
        c.showPage()
        y = draw_header(c, height) - 0.3*inch
    
    # Bid Comparison Table
    y = draw_section(c, y, "3. BID COMPARISON & PROPOSALS")
    if not vendor_bids.empty:
        c.setFont("Helvetica", 9)
        c.drawString(1*inch, y, f"Total Submissions Received: {len(vendor_bids)}")
        y -= 0.3*inch
        
        for idx, vb in vendor_bids.iterrows():
            if y < 2.5*inch:
                c.showPage()
                y = draw_header(c, height) - 0.3*inch
            
            is_selected_vendor = False
            if selected_submission_id:
                is_selected_vendor = str(vb['submission_id']).strip() == selected_submission_id
            elif selected_vendor_id:
                is_selected_vendor = str(vb['vendor_id']).strip() == selected_vendor_id and vb.get('is_selected', False)
            else:
                is_selected_vendor = vb.get('is_selected', False)

            # Vendor header with selection indicator
            if is_selected_vendor:
                c.setFillColorRGB(0.9, 1, 0.9)
                c.rect(0.85*inch, y - 0.05*inch, width - 1.7*inch, 0.3*inch, fill=1)
                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica-Bold", 10)
                c.drawString(1*inch, y, f"★ {vb['vendor_name']} ({vb['vendor_id']}) - SELECTED")
            else:
                c.setFont("Helvetica-Bold", 10)
                c.drawString(1*inch, y, f"{vb['vendor_name']} ({vb['vendor_id']})")
            y -= 0.25*inch
            
            # Vendor details in two columns
            c.setFont("Helvetica", 9)
            c.drawString(1.2*inch, y, f"Bid Amount: ${vb['bid_amount']:,.2f}")
            y -= 0.2*inch
            
            # Proposal Summary
            c.setFont("Helvetica-Bold", 9)
            c.drawString(1.2*inch, y, "Proposal Summary:")
            y -= 0.15*inch
            c.setFont("Helvetica", 8)
            
            # Word wrap the proposal summary
            raw_proposal = sanitize_excel_value(vb.get('bid_description'), '')
            proposal = str(raw_proposal) if raw_proposal else "No proposal summary provided"
            max_width = 80
            words = proposal.split()
            line = ""
            for word in words:
                if len(line) + len(word) + 1 <= max_width:
                    line += word + " "
                else:
                    c.drawString(1.3*inch, y, line.strip())
                    y -= 0.12*inch
                    line = word + " "
                    if y < 1.5*inch:
                        c.showPage()
                        y = draw_header(c, height) - 0.3*inch
            if line:
                c.drawString(1.3*inch, y, line.strip())
                y -= 0.12*inch
            
            # Spacing between vendors
            y -= 0.15*inch
            c.setStrokeColorRGB(0.8, 0.8, 0.8)
            c.line(1*inch, y, width - 1*inch, y)
            c.setStrokeColorRGB(0, 0, 0)
            y -= 0.2*inch
        
        y -= 0.1*inch
    else:
        c.setFont("Helvetica", 10)
        c.drawString(1*inch, y, "No vendor submissions received.")
        y -= 0.3*inch
    
    # Selected Vendor Summary / Assigned Vendor Response
    if not vendor_bids.empty and not selected_vendor.empty:
        if y < 2.5*inch:
            c.showPage()
            y = draw_header(c, height) - 0.3*inch

        y = draw_section(c, y, "4. SELECTED VENDOR SUMMARY")
        selected_row = selected_vendor.iloc[0]
        vendor_info = vendors_dict.get(selected_row['vendor_id'], {})
        raw_summary = sanitize_excel_value(selected_row.get('bid_description'), '')
        proposal_summary = raw_summary if raw_summary else "No proposal summary provided"
        vendor_comment = bid.get('vendor_comment') or proposal_summary

        y = draw_field(c, y, "Submission ID", selected_row['submission_id'])
        y = draw_field(c, y, "Vendor ID", selected_row['vendor_id'])
        y = draw_field(c, y, "Vendor Name", selected_row['vendor_name'])
        bid_amount_value = selected_row['bid_amount'] if 'bid_amount' in selected_row else None
        if bid_amount_value is not None and bid_amount_value == bid_amount_value:
            y = draw_field(c, y, "Bid Amount", f"${bid_amount_value:,.2f}")
        y = draw_field(c, y, "Proposal Summary", vendor_comment)
        y = draw_field(c, y, "Submission Date", selected_row['submission_date'])
        y = draw_field(c, y, "Contact Email", vendor_info.get('contact_email', 'N/A'))
        y = draw_field(c, y, "Contact Phone", vendor_info.get('contact_phone', 'N/A'))
        y -= 0.1*inch
    else:
        if y < 2.5*inch:
            c.showPage()
            y = draw_header(c, height) - 0.3*inch

        y = draw_section(c, y, "4. ASSIGNED VENDOR RESPONSE")
        vendor_name = assigned_vendor.get('vendor_name') if assigned_vendor else None
        y = draw_field(c, y, "Vendor ID", selected_vendor_id or 'Not Assigned')
        y = draw_field(c, y, "Vendor Name", vendor_name or 'Not Assigned')
        y = draw_field(c, y, "Contact Email", (assigned_vendor or {}).get('contact_email', 'N/A'))
        y = draw_field(c, y, "Contact Phone", (assigned_vendor or {}).get('contact_phone', 'N/A'))
        y = draw_field(c, y, "Vendor Comment", bid.get('vendor_comment') or 'No comment submitted yet')
        y = draw_field(c, y, "Submitted On", bid.get('submission_date') or 'Not submitted')
        y -= 0.1*inch

    # Check if we need a new page
    if y < 2*inch:
        c.showPage()
        y = draw_header(c, height) - 0.3*inch
    
    # Admin Notes
    y = draw_section(c, y, "5. ADMIN NOTES")
    y = draw_field(c, y, "Notes", bid['admin_justification'])
    y = draw_field(c, y, "Submitted for Approval", bid['submission_date'])
    y -= 0.2*inch
    
    # Check if we need a new page
    if y < 3*inch:
        c.showPage()
        y = draw_header(c, height) - 0.3*inch
    
    # Approval Workflow
    y = draw_section(c, y, "6. APPROVAL WORKFLOW")
    
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
    
    # Final Status
    c.setFillColorRGB(0, 0.5, 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1*inch, y, f"FINAL STATUS: {bid['status']}")
    c.setFillColorRGB(0, 0, 0)
    y -= 0.5*inch
    
    # Check if we need a new page for history
    if y < 3*inch or not history.empty:
        c.showPage()
        y = draw_header(c, height) - 0.3*inch
    
    # Complete History
    y = draw_section(c, y, "7. COMPLETE AUDIT TRAIL")
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
            c.drawString(1.2*inch, y, f"Comment: {record['comment']}")
            y -= 0.12*inch
        if record['previous_status'] or record['new_status']:
            c.drawString(1.2*inch, y, f"Status: {record['previous_status']} → {record['new_status']}")
            y -= 0.12*inch
        y -= 0.1*inch
    
    # Footer
    c.setFont("Helvetica", 8)
    c.drawString(0.75*inch, 0.5*inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawRightString(width - 0.75*inch, 0.5*inch, f"Document: {bid['bid_id']}_Approval.pdf")
    
    c.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"bid_{bid_id}_approval.pdf", 
                     mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
