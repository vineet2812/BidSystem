"""
Flask Bid Management System
A web application for managing bids with approval workflow
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import db_helper as db
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Role management
ROLES = ['Admin', 'Vendor', 'A1 Approver', 'A2 Approver']

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
            session['technical_capability'] = vendor['technical_capability']
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
        technical_capability = int(request.form['technical_capability'])
        password = request.form['password']
        
        vendor_id = db.create_vendor(vendor_name, contact_email, contact_phone, technical_capability, password)
        
        # Auto login after registration
        session['vendor_id'] = vendor_id
        session['vendor_name'] = vendor_name
        session['user_name'] = vendor_name
        session['technical_capability'] = technical_capability
        
        flash(f'Registration successful! Your Vendor ID is: {vendor_id}', 'success')
        return redirect(url_for('vendor_dashboard'))
    
    return render_template('vendor_register.html', role=session.get('role'))

@app.route('/vendor/logout')
def vendor_logout():
    """Vendor logout"""
    if 'vendor_id' in session:
        del session['vendor_id']
        del session['vendor_name']
        del session['technical_capability']
    flash('Logged out successfully!', 'success')
    return redirect(url_for('vendor_login_page'))

@app.route('/admin/dashboard')
def admin_dashboard():
    """Admin Dashboard"""
    if session.get('role') != 'Admin':
        flash('Access denied. Admin role required.', 'danger')
        return redirect(url_for('index'))
    
    bids = db.get_all_bids()
    return render_template('admin_dashboard.html', bids=bids, role=session.get('role'))

@app.route('/admin/create_bid', methods=['GET', 'POST'])
def create_bid():
    """Create new bid"""
    if session.get('role') != 'Admin':
        flash('Access denied. Admin role required.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        contract_name = request.form['contract_name']
        contract_description = request.form['contract_description']
        contract_value = float(request.form['contract_value'])
        min_technical_capability = int(request.form.get('min_technical_capability', 0))
        admin_name = session.get('user_name', 'Admin')
        
        bid_id = db.create_bid(contract_name, contract_description, contract_value, admin_name, min_technical_capability)
        
        # Add bid items if provided
        item_names = request.form.getlist('item_name[]')
        item_descriptions = request.form.getlist('item_description[]')
        quantities = request.form.getlist('quantity[]')
        units = request.form.getlist('unit[]')
        
        for i in range(len(item_names)):
            if item_names[i]:  # Only add if item name is provided
                db.add_bid_item(bid_id, item_names[i], item_descriptions[i], 
                              float(quantities[i]) if quantities[i] else 0, units[i])
        
        flash(f'Bid {bid_id} created successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('create_bid.html', role=session.get('role'))

@app.route('/admin/view_bid/<bid_id>')
def admin_view_bid(bid_id):
    """View bid details and vendor submissions"""
    if session.get('role') != 'Admin':
        flash('Access denied. Admin role required.', 'danger')
        return redirect(url_for('index'))
    
    bid = db.get_bid_by_id(bid_id)
    vendor_bids = db.get_vendor_bids_for_bid(bid_id)
    history = db.get_history_for_bid(bid_id)
    items = db.get_items_for_bid(bid_id)
    
    # Add technical capability to vendor bids
    if not vendor_bids.empty:
        vendor_bids = vendor_bids.copy()
        vendor_bids['technical_capability'] = vendor_bids['vendor_id'].apply(
            lambda vid: db.get_vendor_by_id(vid).get('technical_capability', 'N/A') if db.get_vendor_by_id(vid) else 'N/A'
        )
    
    return render_template('admin_view_bid.html', bid=bid, vendor_bids=vendor_bids, 
                          history=history, items=items, role=session.get('role'))

@app.route('/admin/select_vendor/<bid_id>', methods=['POST'])
def select_vendor(bid_id):
    """Select vendor and submit for A1 approval"""
    if session.get('role') != 'Admin':
        flash('Access denied. Admin role required.', 'danger')
        return redirect(url_for('index'))
    
    vendor_id = request.form['vendor_id']
    justification = request.form['justification']
    admin_name = session.get('user_name', 'Admin')
    
    db.select_vendor_and_submit_for_approval(bid_id, vendor_id, justification, admin_name)
    flash('Vendor selected and submitted for A1 approval!', 'success')
    
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
    vendor_technical_capability = session.get('technical_capability', 0)
    
    # Filter bids that are open for bidding and meet technical capability requirement
    open_bids = bids[
        (bids['status'] == 'Open for Bidding') & 
        (bids['min_technical_capability'] <= vendor_technical_capability)
    ]
    
    return render_template('vendor_dashboard.html', bids=open_bids, role=session.get('role'),
                          vendor_capability=vendor_technical_capability)

@app.route('/vendor/view_bid/<bid_id>')
def vendor_view_bid(bid_id):
    """View bid details for vendor"""
    if session.get('role') != 'Vendor':
        flash('Access denied. Vendor role required.', 'danger')
        return redirect(url_for('index'))
    
    if 'vendor_id' not in session:
        flash('Please login first!', 'warning')
        return redirect(url_for('vendor_login_page'))
    
    bid = db.get_bid_by_id(bid_id)
    items = db.get_items_for_bid(bid_id)
    vendor = db.get_vendor_by_id(session.get('vendor_id'))
    
    return render_template('vendor_view_bid.html', bid=bid, items=items, 
                          vendor=vendor, role=session.get('role'))

@app.route('/vendor/submit_bid/<bid_id>', methods=['POST'])
def submit_bid(bid_id):
    """Submit vendor bid"""
    if session.get('role') != 'Vendor':
        flash('Access denied. Vendor role required.', 'danger')
        return redirect(url_for('index'))
    
    vendor_id = session.get('vendor_id')
    vendor_name = session.get('vendor_name')
    bid_amount = float(request.form['bid_amount'])
    bid_description = request.form['bid_description']
    
    submission_id = db.submit_vendor_bid(bid_id, vendor_id, vendor_name, bid_amount, bid_description)
    flash(f'Bid submitted successfully! Submission ID: {submission_id}', 'success')
    
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
    
    bid = db.get_bid_by_id(bid_id)
    
    # Check if bid has been submitted for approval
    if bid['status'] not in ['Pending A1', 'Pending A2', 'Approved', 'Rejected']:
        flash('This bid has not been submitted for approval yet!', 'warning')
        return redirect(url_for('a1_dashboard'))
    
    vendor_bids = db.get_vendor_bids_for_bid(bid_id)
    history = db.get_history_for_bid(bid_id)
    items = db.get_items_for_bid(bid_id)
    selected_vendor_bid = vendor_bids[vendor_bids['is_selected'] == True]
    
    # Add technical capability to vendor bids
    if not vendor_bids.empty:
        vendor_bids = vendor_bids.copy()
        vendor_bids['technical_capability'] = vendor_bids['vendor_id'].apply(
            lambda vid: db.get_vendor_by_id(vid).get('technical_capability', 'N/A') if db.get_vendor_by_id(vid) else 'N/A'
        )
    
    return render_template('a1_view_bid.html', bid=bid, vendor_bid=selected_vendor_bid, 
                          vendor_bids=vendor_bids, history=history, items=items, role=session.get('role'))

@app.route('/a1/approve/<bid_id>', methods=['POST'])
def a1_approve_bid(bid_id):
    """A1 approve bid"""
    if session.get('role') != 'A1 Approver':
        flash('Access denied. A1 Approver role required.', 'danger')
        return redirect(url_for('index'))
    
    # Check if bid has been submitted for approval
    bid = db.get_bid_by_id(bid_id)
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
    
    vendor_bids = db.get_vendor_bids_for_bid(bid_id)
    history = db.get_history_for_bid(bid_id)
    items = db.get_items_for_bid(bid_id)
    selected_vendor_bid = vendor_bids[vendor_bids['is_selected'] == True]
    
    # Add technical capability to vendor bids
    if not vendor_bids.empty:
        vendor_bids = vendor_bids.copy()
        vendor_bids['technical_capability'] = vendor_bids['vendor_id'].apply(
            lambda vid: db.get_vendor_by_id(vid).get('technical_capability', 'N/A') if db.get_vendor_by_id(vid) else 'N/A'
        )
    
    return render_template('a2_view_bid.html', bid=bid, vendor_bid=selected_vendor_bid, 
                          vendor_bids=vendor_bids, history=history, items=items, role=session.get('role'))

@app.route('/a2/approve/<bid_id>', methods=['POST'])
def a2_approve_bid(bid_id):
    """A2 approve bid (final approval)"""
    if session.get('role') != 'A2 Approver':
        flash('Access denied. A2 Approver role required.', 'danger')
        return redirect(url_for('index'))
    
    # Check if bid has been approved by A1
    bid = db.get_bid_by_id(bid_id)
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
    if bid['status'] != 'Pending A2':
        flash('This bid has not been approved by A1 yet!', 'danger')
        return redirect(url_for('a2_dashboard'))
    
    comment = request.form['comment']
    approver_name = session.get('user_name', 'A2 Approver')
    
    db.a2_reject(bid_id, comment, approver_name)
    flash('Bid rejected and sent back to A1 Approver!', 'warning')
    
    return redirect(url_for('a2_dashboard'))

@app.route('/download_pdf/<bid_id>')
def download_pdf(bid_id):
    """Download bid approval PDF - Accessible by all roles"""
    bid = db.get_bid_by_id(bid_id)
    
    if bid['status'] != 'Approved':
        flash('PDF download only available for approved bids!', 'danger')
        return redirect(url_for('index'))
    
    vendor_bids = db.get_vendor_bids_for_bid(bid_id)
    selected_vendor = vendor_bids[vendor_bids['is_selected'] == True]
    history = db.get_history_for_bid(bid_id)
    items = db.get_items_for_bid(bid_id)
    
    # Get vendor details for technical capability info
    vendors_dict = {}
    for _, vb in vendor_bids.iterrows():
        vendor = db.get_vendor_by_id(vb['vendor_id'])
        if vendor:
            vendors_dict[vb['vendor_id']] = vendor
    
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
        """Draw a label-value pair"""
        if bold_label:
            canvas_obj.setFont("Helvetica-Bold", 10)
        else:
            canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawString(1*inch, y_pos, f"{label}:")
        canvas_obj.setFont("Helvetica", 10)
        # Handle long values
        value_str = str(value) if value is not None else "N/A"
        if len(value_str) > 80:
            canvas_obj.drawString(3*inch, y_pos, value_str[:80])
            return draw_field(canvas_obj, y_pos - 0.2*inch, "", value_str[80:], False) - 0.05*inch
        canvas_obj.drawString(3*inch, y_pos, value_str)
        return y_pos - 0.25*inch
    
    # PAGE 1
    y = draw_header(c, height)
    y -= 0.3*inch
    
    # Contract Information
    y = draw_section(c, y, "1. CONTRACT INFORMATION")
    y = draw_field(c, y, "Bid ID", bid['bid_id'])
    y = draw_field(c, y, "Contract Name", bid['contract_name'])
    y = draw_field(c, y, "Description", bid['contract_description'])
    y = draw_field(c, y, "Contract Value", f"${bid['contract_value']:,.2f}")
    y = draw_field(c, y, "Min Technical Capability Required", f"{bid['min_technical_capability']}/5" if bid['min_technical_capability'] > 0 else "Not Specified")
    y = draw_field(c, y, "Created By", bid['admin_name'])
    y = draw_field(c, y, "Created Date", bid['created_date'])
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
            
            vendor_info = vendors_dict.get(vb['vendor_id'], {})
            tech_cap = vendor_info.get('technical_capability', 'N/A')
            
            # Vendor header with selection indicator
            if vb['is_selected']:
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
            c.drawString(1.2*inch, y, f"Technical Rating: {tech_cap}/5")
            c.drawString(3.5*inch, y, f"Bid Amount: ${vb['bid_amount']:,.2f}")
            y -= 0.2*inch
            
            # Proposal Summary
            c.setFont("Helvetica-Bold", 9)
            c.drawString(1.2*inch, y, "Proposal Summary:")
            y -= 0.15*inch
            c.setFont("Helvetica", 8)
            
            # Word wrap the proposal summary
            proposal = str(vb['bid_description']) if vb['bid_description'] else "No proposal summary provided"
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
    
    # Check if we need a new page
    if y < 2*inch:
        c.showPage()
        y = draw_header(c, height) - 0.3*inch
    
    # Admin Justification
    y = draw_section(c, y, "4. ADMIN SELECTION JUSTIFICATION")
    y = draw_field(c, y, "Justification", bid['admin_justification'])
    y = draw_field(c, y, "Submitted for Approval", bid['submission_date'])
    y -= 0.2*inch
    
    # Check if we need a new page
    if y < 3*inch:
        c.showPage()
        y = draw_header(c, height) - 0.3*inch
    
    # Approval Workflow
    y = draw_section(c, y, "5. APPROVAL WORKFLOW")
    
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
    y = draw_section(c, y, "6. COMPLETE AUDIT TRAIL")
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
