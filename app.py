import os
import random
import string
import urllib.parse
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from database import get_db, close_db, init_db, query_db, execute_db
from smart_analyzer import analyze_issue, detect_duplicate_issue

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Register teardown
app.teardown_appcontext(close_db)


# ==========================================
# Helpers & Context Processors
# ==========================================

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def generate_ticket_id():
    """Generate unique ticket ID like CC-2026-9842"""
    year = datetime.now().year
    random_digits = ''.join(random.choices(string.digits, k=4))
    ticket_id = f"CC-{year}-{random_digits}"
    while query_db("SELECT id FROM issues WHERE ticket_id = ?", (ticket_id,), one=True):
        random_digits = ''.join(random.choices(string.digits, k=4))
        ticket_id = f"CC-{year}-{random_digits}"
    return ticket_id

# Alias for backwards-compatibility
generate_tracking_id = generate_ticket_id

@app.context_processor
def inject_user_and_counts():
    """Inject current user and high-level counts into all templates"""
    user = None
    if 'user_id' in session:
        user = query_db("SELECT * FROM users WHERE id = ?", (session['user_id'],), one=True)
    return {
        'current_user': user,
        'now': datetime.now()
    }

@app.template_filter('format_dt')
def format_dt(value, fmt='%Y-%m-%d %H:%M'):
    """Format datetime or string safely"""
    if value is None:
        return ''
    if hasattr(value, 'strftime'):
        return value.strftime(fmt)
    return str(value)[:16]

@app.template_filter('format_date')
def format_date(value, fmt='%Y-%m-%d'):
    """Format date or string safely"""
    if value is None:
        return ''
    if hasattr(value, 'strftime'):
        return value.strftime(fmt)
    return str(value)[:10]

DEPARTMENT_MAP = {
    'Electrical': 'Electrical & Power Wing',
    'Water & Plumbing': 'Plumbing & Water Works',
    'Internet/Wi-Fi': 'Campus IT & Networks',
    'Sanitation/Housekeeping': 'Housekeeping & Facilities',
    'Classroom Infrastructure': 'Estate & Civil Works'
}

@app.template_filter('timeago')
def timeago_filter(value):
    """Format relative time (e.g. '12m ago', '2h ago')"""
    if value is None:
        return ''
    dt = None
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace(' ', 'T'))
        except Exception:
            return value[:16]
    elif hasattr(value, 'year'):
        dt = value
    else:
        return str(value)
    now = datetime.now()
    diff = (now - dt).total_seconds()
    if diff < 0 or diff < 60:
        return "Just now"
    elif diff < 3600:
        return f"{int(diff // 60)}m ago"
    elif diff < 86400:
        return f"{int(diff // 3600)}h ago"
    else:
        days = int(diff // 86400)
        return f"{days}d ago" if days < 30 else dt.strftime('%b %d')

@app.template_filter('department_for')
def department_for_filter(category):
    return DEPARTMENT_MAP.get(category, 'Facilities & Maintenance')

def login_required(view_func):
    """Decorator to enforce authenticated session"""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.path))
        return view_func(*args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper

def admin_required(view_func):
    """Decorator to enforce admin role"""
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("Admin login required.", "warning")
            return redirect(url_for('login', next=request.path))
        user = query_db("SELECT role FROM users WHERE id = ?", (session['user_id'],), one=True)
        if not user or user['role'] != 'admin':
            flash("Access denied: Administrative privileges required.", "danger")
            return redirect(url_for('student_dashboard'))
        return view_func(*args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ==========================================
# Public & Authentication Routes
# ==========================================

@app.route('/')
def index():
    """Modern Hackathon Landing Page"""
    total_issues = query_db("SELECT COUNT(*) as count FROM issues", one=True)['count']
    resolved_issues = query_db("SELECT COUNT(*) as count FROM issues WHERE status = 'Resolved'", one=True)['count']
    active_students = query_db("SELECT COUNT(*) as count FROM users WHERE role = 'student'", one=True)['count']
    
    resolution_rate = round((resolved_issues / total_issues * 100), 1) if total_issues > 0 else 100.0

    announcements = query_db("""
        SELECT a.*, u.name as author_name 
        FROM announcements a
        JOIN users u ON a.author_id = u.id
        ORDER BY a.created_at DESC LIMIT 3
    """)

    return render_template(
        'index.html',
        total_complaints=total_issues,
        total_issues=total_issues,
        resolved_complaints=resolved_issues,
        resolved_issues=resolved_issues,
        active_students=active_students,
        resolution_rate=resolution_rate,
        announcements=announcements
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login with 1-click Demo credentials for Hackathon Judges"""
    demo_type = request.args.get('demo')
    if demo_type == 'admin':
        admin_user = query_db("SELECT * FROM users WHERE role = 'admin' LIMIT 1", one=True)
        if admin_user:
            session.clear()
            session['user_id'] = admin_user['id']
            session['user_name'] = admin_user['name']
            session['user_role'] = admin_user['role']
            flash(f"Welcome back, {admin_user['name']}! (Demo Admin Access)", "success")
            return redirect(url_for('admin_dashboard'))
    elif demo_type == 'student':
        student_user = query_db("SELECT * FROM users WHERE role = 'student' LIMIT 1", one=True)
        if student_user:
            session.clear()
            session['user_id'] = student_user['id']
            session['user_name'] = student_user['name']
            session['user_role'] = student_user['role']
            flash(f"Welcome back, {student_user['name']}! (Demo Student Access)", "success")
            return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        if not identifier or not password:
            flash("Please enter your email/student ID and password.", "danger")
            return render_template('login.html')

        user = query_db(
            "SELECT * FROM users WHERE email = ? OR student_id = ?",
            (identifier, identifier),
            one=True
        )

        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            flash(f"Logged in successfully. Welcome, {user['name']}!", "success")
            
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid credentials. Please verify your details or use demo quick-login.", "danger")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Student registration route with full validation"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        student_id = request.form.get('student_id', '').strip().upper()
        department = request.form.get('department', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not (name and email and student_id and department and password):
            flash("All fields are mandatory.", "danger")
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html')

        existing_email = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
        if existing_email:
            flash("An account with this email address already exists.", "danger")
            return render_template('register.html')

        existing_sid = query_db("SELECT id FROM users WHERE student_id = ?", (student_id,), one=True)
        if existing_sid:
            flash("An account with this Student ID already exists.", "danger")
            return render_template('register.html')

        password_hash = generate_password_hash(password)
        user_id = execute_db(
            """INSERT INTO users (name, email, student_id, department, role, password_hash)
               VALUES (?, ?, ?, ?, 'student', ?)""",
            (name, email, student_id, department, password_hash)
        )

        session.clear()
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_role'] = 'student'

        flash("Registration successful! Welcome to CampusCare.", "success")
        return redirect(url_for('student_dashboard'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('index'))


# ==========================================
# Student Dashboard & Issue Workflow
# ==========================================

@app.route('/dashboard')
@login_required
def student_dashboard():
    """Student dashboard with stats, recent reports, and announcements"""
    user_id = session['user_id']
    
    total_count = query_db("SELECT COUNT(*) as count FROM issues WHERE student_id = ?", (user_id,), one=True)['count']
    reported_count = query_db("SELECT COUNT(*) as count FROM issues WHERE student_id = ? AND status IN ('Reported', 'Pending')", (user_id,), one=True)['count']
    in_progress_count = query_db("SELECT COUNT(*) as count FROM issues WHERE student_id = ? AND status IN ('In Progress', 'Under Review', 'Assigned')", (user_id,), one=True)['count']
    resolved_count = query_db("SELECT COUNT(*) as count FROM issues WHERE student_id = ? AND status IN ('Resolved', 'Closed')", (user_id,), one=True)['count']

    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('q', '').strip()

    sql = "SELECT * FROM issues WHERE student_id = ?"
    params = [user_id]

    if status_filter == 'Reported' or status_filter == 'Pending':
        sql += " AND status IN ('Reported', 'Pending')"
    elif status_filter == 'In Progress':
        sql += " AND status IN ('In Progress', 'Under Review', 'Assigned')"
    elif status_filter == 'Resolved':
        sql += " AND status IN ('Resolved', 'Closed')"

    if search_query:
        sql += " AND (title LIKE ? OR description LIKE ? OR ticket_id LIKE ? OR location_block LIKE ? OR location_room LIKE ?)"
        term = f"%{search_query}%"
        params.extend([term, term, term, term, term])

    sql += " ORDER BY created_at DESC"
    raw_issues = query_db(sql, tuple(params))

    # Enrich issues with department, SLA countdown, and relative times
    issues_enriched = []
    now = datetime.now()
    for row in raw_issues:
        item = dict(row)
        item['assigned_dept'] = DEPARTMENT_MAP.get(item.get('category'), 'Facilities & Maintenance')
        created_at_dt = None
        if item.get('created_at'):
            try:
                if isinstance(item['created_at'], str):
                    created_at_dt = datetime.fromisoformat(item['created_at'].replace(' ', 'T'))
                else:
                    created_at_dt = item['created_at']
            except Exception:
                created_at_dt = None

        if created_at_dt and item.get('status') not in ('Resolved', 'Closed'):
            elapsed_hours = (now - created_at_dt).total_seconds() / 3600.0
            sla_limit = 4 if item.get('priority') == 'Urgent' else (24 if item.get('priority') == 'High' else 48)
            remaining = sla_limit - elapsed_hours
            item['elapsed_hours'] = round(elapsed_hours, 1)
            item['sla_limit'] = sla_limit
            item['sla_breached'] = remaining < 0
            if remaining <= 0:
                item['sla_countdown'] = f"Overdue {round(abs(remaining), 1)}h"
                item['sla_countdown_class'] = "breached"
            elif remaining < 4:
                item['sla_countdown'] = f"{round(remaining, 1)}h left (Critical)"
                item['sla_countdown_class'] = "warning"
            else:
                item['sla_countdown'] = f"{round(remaining, 1)}h left"
                item['sla_countdown_class'] = "on-track"
        else:
            item['sla_countdown'] = "Completed" if item.get('status') in ('Resolved', 'Closed') else "--"
            item['sla_countdown_class'] = "resolved" if item.get('status') in ('Resolved', 'Closed') else "on-track"
        issues_enriched.append(item)

    # Fetch latest campus announcements
    announcements = query_db("""
        SELECT a.*, u.name as author_name 
        FROM announcements a
        JOIN users u ON a.author_id = u.id
        ORDER BY a.created_at DESC LIMIT 5
    """)

    return render_template(
        'student_dashboard.html',
        total_count=total_count,
        pending_count=reported_count,
        reported_count=reported_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        complaints=issues_enriched,
        issues=issues_enriched,
        announcements=announcements,
        current_filter=status_filter,
        search_query=search_query
    )

@app.route('/report', methods=['GET', 'POST'])
@login_required
def report_issue():
    """
    Report an issue with Smart Keyword Categorization, Priority Assignment,
    Location Parsing, QR-code URL prefill, and Duplicate Detection.
    """
    # Check for QR Code URL parameter auto-fill (e.g. /report?block=CSE&room=Lab-2)
    qr_block = request.args.get('block', '') or request.args.get('location_block', '')
    qr_room = request.args.get('room', '') or request.args.get('location_room', '')

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        # Location block and room handling
        location_block = request.form.get('location_block', '').strip() or request.form.get('block', '').strip()
        location_room = request.form.get('location_room', '').strip() or request.form.get('room', '').strip()
        
        # Backward compatibility fallback if legacy 'location' field submitted
        if not location_block and request.form.get('location'):
            raw_loc = request.form.get('location').strip()
            if ',' in raw_loc:
                parts = [p.strip() for p in raw_loc.split(',', 1)]
                location_block, location_room = parts[0], parts[1]
            else:
                location_block = raw_loc

        category = request.form.get('category', '').strip()
        priority = request.form.get('priority', 'Auto').strip()
        auto_classify = request.form.get('auto_classify') == 'true'

        if not title or not description or not location_block:
            flash("Please provide an Issue Title, Campus Block, and Detailed Description.", "danger")
            return render_template('report_issue.html', qr_block=location_block, qr_room=location_room)

        # Run Smart Analyzer
        analysis = analyze_issue(title, description, location_block, location_room)

        # Auto category resolution
        if not category or category in ('Auto-Detect', 'Auto') or auto_classify:
            category = analysis['suggested_category']

        # Auto priority resolution
        if not priority or priority == 'Auto':
            priority = analysis['suggested_priority']

        # Handle Image Upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                safe_name = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                image_filename = f"{timestamp}_{safe_name}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                image_url = image_filename

        ticket_id = generate_ticket_id()

        issue_id = execute_db("""
            INSERT INTO issues (
                ticket_id, student_id, title, description, category,
                priority, status, location_block, location_room, image_url
            ) VALUES (?, ?, ?, ?, ?, ?, 'Reported', ?, ?, ?)
        """, (
            ticket_id, session['user_id'], title, description,
            category, priority, location_block, location_room, image_url
        ))

        # Log initial creation entry into comments
        execute_db("""
            INSERT INTO comments (issue_id, user_id, comment)
            VALUES (?, ?, 'Issue filed by student via CampusCare web portal.')
        """, (issue_id, session['user_id']))

        # Duplicate check alert in flash if applicable
        dup_check = detect_duplicate_issue(category, location_block, location_room, title, description)
        if dup_check['is_duplicate']:
            flash(
                f"Ticket [{ticket_id}] submitted! Note: A similar open ticket ({dup_check['duplicate_ticket']['ticket_id']}) exists at this location and has been linked.",
                "warning"
            )
        else:
            flash(
                f"Grievance lodged successfully! Ticket ID: {ticket_id}. "
                f"Smart Triage assigned [{category}] with [{priority}] Priority.",
                "success"
            )

        return redirect(url_for('track_issue_detail', tracking_id=ticket_id))

    return render_template('report_issue.html', qr_block=qr_block, qr_room=qr_room)

@app.route('/api/analyze-issue', methods=['POST'])
def api_analyze_issue():
    """Real-time API endpoint for live typing smart assistance and duplicate detection in frontend"""
    data = request.get_json() or {}
    title = data.get('title', '')
    description = data.get('description', '')
    block = data.get('location_block', '') or data.get('block', '')
    room = data.get('location_room', '') or data.get('room', '')
    
    analysis = analyze_issue(title, description, block, room)
    
    # Run duplicate detection heuristic
    dup = detect_duplicate_issue(analysis['suggested_category'], block, room, title, description)
    analysis['duplicate'] = dup
    return jsonify(analysis)

@app.route('/api/check-duplicates', methods=['POST'])
def api_check_duplicates():
    """Dedicated endpoint to check for duplicate open issues by location and category"""
    data = request.get_json() or {}
    category = data.get('category', '')
    block = data.get('location_block', '') or data.get('block', '')
    room = data.get('location_room', '') or data.get('room', '')
    title = data.get('title', '')
    desc = data.get('description', '')

    result = detect_duplicate_issue(category, block, room, title, desc)
    return jsonify(result)


# ==========================================
# Issue Tracking & Comments Lifecycle
# ==========================================

@app.route('/track', methods=['GET', 'POST'])
def track_issue():
    """Search and track complaint status by unique Ticket / Tracking ID"""
    searched_id = request.args.get('id', '').strip()
    if request.method == 'POST':
        searched_id = request.form.get('tracking_id', '').strip() or request.form.get('ticket_id', '').strip()
        if searched_id:
            return redirect(url_for('track_issue_detail', tracking_id=searched_id))
        flash("Please enter a valid Ticket ID.", "warning")

    issue = None
    comments = []
    if searched_id:
        issue = query_db("""
            SELECT i.*, 
                   i.ticket_id as tracking_id,
                   i.image_url as image_filename,
                   i.resolution_notes as admin_notes,
                   (i.location_block || CASE WHEN i.location_room IS NOT NULL AND i.location_room != '' THEN ', ' || i.location_room ELSE '' END) as location,
                   u.name as student_name, u.student_id as student_code, u.department, u.email as student_email
            FROM issues i
            JOIN users u ON i.student_id = u.id
            WHERE i.ticket_id = ?
        """, (searched_id,), one=True)

        if not issue:
            flash(f"No grievance record found matching Ticket ID: {searched_id}", "danger")
        else:
            comments = query_db("""
                SELECT c.*, u.name as author_name, u.role as author_role
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.issue_id = ?
                ORDER BY c.created_at ASC
            """, (issue['id'],))

    return render_template('track_issue.html', complaint=issue, issue=issue, comments=comments, searched_id=searched_id)

@app.route('/track/<tracking_id>')
def track_issue_detail(tracking_id):
    """Direct track view for a specific ticket ID with vertical timeline state"""
    issue_row = query_db("""
        SELECT i.*, 
               i.ticket_id as tracking_id,
               i.image_url as image_filename,
               i.resolution_notes as admin_notes,
               (i.location_block || CASE WHEN i.location_room IS NOT NULL AND i.location_room != '' THEN ', ' || i.location_room ELSE '' END) as location,
               u.name as student_name, u.student_id as student_code, u.department, u.email as student_email
        FROM issues i
        JOIN users u ON i.student_id = u.id
        WHERE i.ticket_id = ?
    """, (tracking_id,), one=True)

    if not issue_row:
        flash(f"Grievance Ticket '{tracking_id}' not found.", "danger")
        return redirect(url_for('track_issue'))

    issue = dict(issue_row)
    issue['assigned_dept'] = DEPARTMENT_MAP.get(issue.get('category'), 'Facilities & Maintenance')
    
    st = issue.get('status', 'Reported')
    issue['step1_completed'] = True
    issue['step2_completed'] = st in ('Under Review', 'In Progress', 'Assigned', 'Resolved', 'Closed')
    issue['step2_active'] = (st == 'Under Review')
    issue['step3_completed'] = st in ('In Progress', 'Assigned', 'Resolved', 'Closed')
    issue['step3_active'] = st in ('In Progress', 'Assigned')
    issue['step4_completed'] = st in ('Resolved', 'Closed')
    issue['step4_active'] = (st in ('Resolved', 'Closed'))

    # SLA Calculations
    now = datetime.now()
    created_at_dt = None
    if issue.get('created_at'):
        try:
            if isinstance(issue['created_at'], str):
                created_at_dt = datetime.fromisoformat(issue['created_at'].replace(' ', 'T'))
            else:
                created_at_dt = issue['created_at']
        except Exception:
            created_at_dt = None

    if created_at_dt and st not in ('Resolved', 'Closed'):
        elapsed_hours = (now - created_at_dt).total_seconds() / 3600.0
        sla_limit = 4 if issue.get('priority') == 'Urgent' else (24 if issue.get('priority') == 'High' else 48)
        remaining = sla_limit - elapsed_hours
        issue['elapsed_hours'] = round(elapsed_hours, 1)
        issue['sla_limit'] = sla_limit
        issue['sla_breached'] = remaining < 0
        if remaining <= 0:
            issue['sla_countdown'] = f"Overdue by {round(abs(remaining), 1)}h"
            issue['sla_countdown_class'] = "breached"
        elif remaining < 4:
            issue['sla_countdown'] = f"{round(remaining, 1)}h left (Critical)"
            issue['sla_countdown_class'] = "warning"
        else:
            issue['sla_countdown'] = f"{round(remaining, 1)}h left"
            issue['sla_countdown_class'] = "on-track"
    else:
        issue['sla_countdown'] = "Completed" if st in ('Resolved', 'Closed') else "--"
        issue['sla_countdown_class'] = "resolved" if st in ('Resolved', 'Closed') else "on-track"

    comments = query_db("""
        SELECT c.*, u.name as author_name, u.role as author_role
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.issue_id = ?
        ORDER BY c.created_at ASC
    """, (issue['id'],))

    return render_template('track_issue.html', complaint=issue, issue=issue, comments=comments, searched_id=tracking_id)

@app.route('/issue/<int:issue_id>/comment', methods=['POST'])
@login_required
def add_issue_comment(issue_id):
    """Allow student or administrator to post a comment or update on an issue"""
    comment_text = request.form.get('comment', '').strip()
    if not comment_text:
        flash("Comment text cannot be empty.", "warning")
        return redirect(request.referrer or url_for('student_dashboard'))

    issue = query_db("SELECT id, ticket_id FROM issues WHERE id = ?", (issue_id,), one=True)
    if not issue:
        flash("Issue not found.", "danger")
        return redirect(url_for('student_dashboard'))

    execute_db("""
        INSERT INTO comments (issue_id, user_id, comment)
        VALUES (?, ?, ?)
    """, (issue_id, session['user_id'], comment_text))

    flash("Comment posted successfully.", "success")
    return redirect(url_for('track_issue_detail', tracking_id=issue['ticket_id']))


# ==========================================
# Admin Operations & Resolution Hub
# ==========================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Comprehensive Admin Panel for Campus Facility Management"""
    # High-level KPIs
    total_issues = query_db("SELECT COUNT(*) as count FROM issues", one=True)['count']
    reported_issues = query_db("SELECT COUNT(*) as count FROM issues WHERE status IN ('Reported', 'Pending')", one=True)['count']
    under_review_issues = query_db("SELECT COUNT(*) as count FROM issues WHERE status = 'Under Review'", one=True)['count']
    in_progress_issues = query_db("SELECT COUNT(*) as count FROM issues WHERE status IN ('In Progress', 'Assigned')", one=True)['count']
    resolved_issues = query_db("SELECT COUNT(*) as count FROM issues WHERE status IN ('Resolved', 'Closed')", one=True)['count']
    urgent_issues = query_db("SELECT COUNT(*) as count FROM issues WHERE priority = 'Urgent' AND status NOT IN ('Resolved', 'Closed')", one=True)['count']

    # Filter parameters
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', 'all')
    priority_filter = request.args.get('priority', 'all')
    search_query = request.args.get('q', '').strip()

    sql = """
        SELECT i.*, 
               i.ticket_id as tracking_id,
               i.image_url as image_filename,
               i.resolution_notes as admin_notes,
               (i.location_block || CASE WHEN i.location_room IS NOT NULL AND i.location_room != '' THEN ', ' || i.location_room ELSE '' END) as location,
               u.name as student_name, u.student_id as student_code, u.department, u.email as student_email
        FROM issues i
        JOIN users u ON i.student_id = u.id
        WHERE 1=1
    """
    params = []

    if status_filter != 'all':
        if status_filter in ('Reported', 'Pending'):
            sql += " AND i.status IN ('Reported', 'Pending')"
        elif status_filter in ('In Progress', 'Assigned'):
            sql += " AND i.status IN ('In Progress', 'Assigned')"
        elif status_filter in ('Resolved', 'Closed'):
            sql += " AND i.status IN ('Resolved', 'Closed')"
        else:
            sql += " AND i.status = ?"
            params.append(status_filter)

    if category_filter != 'all':
        sql += " AND i.category = ?"
        params.append(category_filter)

    if priority_filter != 'all':
        sql += " AND i.priority = ?"
        params.append(priority_filter)

    if search_query:
        sql += """ AND (
            i.ticket_id LIKE ? OR 
            i.title LIKE ? OR 
            i.description LIKE ? OR 
            i.location_block LIKE ? OR 
            i.location_room LIKE ? OR 
            u.name LIKE ? OR 
            u.student_id LIKE ?
        )"""
        term = f"%{search_query}%"
        params.extend([term, term, term, term, term, term, term])

    # Sort with Urgent & Critical first, followed by newest timestamp
    sql += """ ORDER BY 
        CASE i.priority 
            WHEN 'Urgent' THEN 1 
            WHEN 'High' THEN 2 
            WHEN 'Medium' THEN 3 
            ELSE 4 
        END, 
        i.created_at DESC"""
    issues = query_db(sql, tuple(params))

    # Calculate SLA status, countdown, and department for each issue
    issues_with_sla = []
    now = datetime.now()
    active_count = 0
    breached_count = 0

    for item in issues:
        item_dict = dict(item)
        item_dict['assigned_dept'] = DEPARTMENT_MAP.get(item_dict.get('category'), 'Facilities & Maintenance')
        created_at_dt = None
        if item_dict.get('created_at'):
            try:
                if isinstance(item_dict['created_at'], str):
                    created_at_dt = datetime.fromisoformat(item_dict['created_at'].replace(' ', 'T'))
                else:
                    created_at_dt = item_dict['created_at']
            except Exception:
                created_at_dt = None

        if created_at_dt and item_dict['status'] not in ('Resolved', 'Closed'):
            active_count += 1
            elapsed_hours = (now - created_at_dt).total_seconds() / 3600.0
            item_dict['elapsed_hours'] = round(elapsed_hours, 1)
            # SLA thresholds: Urgent = 4h, High = 24h, Medium = 48h, Low = 72h
            sla_limit = 4 if item_dict['priority'] == 'Urgent' else (24 if item_dict['priority'] == 'High' else 48)
            item_dict['sla_limit'] = sla_limit
            remaining = sla_limit - elapsed_hours
            item_dict['sla_remaining_hours'] = round(remaining, 1)
            is_breached = remaining < 0
            item_dict['sla_breached'] = is_breached
            if is_breached:
                breached_count += 1
                item_dict['sla_countdown'] = f"Overdue {round(abs(remaining), 1)}h"
                item_dict['sla_countdown_class'] = "breached"
            elif remaining < 4:
                item_dict['sla_countdown'] = f"{round(remaining, 1)}h left"
                item_dict['sla_countdown_class'] = "warning"
            else:
                item_dict['sla_countdown'] = f"{round(remaining, 1)}h left"
                item_dict['sla_countdown_class'] = "on-track"
        else:
            item_dict['elapsed_hours'] = 0
            item_dict['sla_limit'] = 48
            item_dict['sla_breached'] = False
            item_dict['sla_countdown'] = "Completed" if item_dict.get('status') in ('Resolved', 'Closed') else "--"
            item_dict['sla_countdown_class'] = "resolved" if item_dict.get('status') in ('Resolved', 'Closed') else "on-track"

        issues_with_sla.append(item_dict)

    on_track_count = active_count - breached_count
    sla_compliance_pct = round((on_track_count / active_count * 100), 1) if active_count > 0 else 100.0
    active_issues_count = reported_issues + under_review_issues + in_progress_issues

    # Campus Geographic Heatmap Zones
    CAMPUS_ZONES = [
        {'name': 'Tech Block A', 'code': 'Block A', 'desc': 'CS, IT & Robotics Labs', 'icon': 'fa-laptop-code'},
        {'name': 'Science Block B', 'code': 'Block B', 'desc': 'Physics & Chemistry Labs', 'icon': 'fa-flask-vial'},
        {'name': 'Admin Block C', 'code': 'Block C', 'desc': 'Dean & Registrar Offices', 'icon': 'fa-building-columns'},
        {'name': 'Central Library', 'code': 'Library', 'desc': 'Reading Halls & Study Pods', 'icon': 'fa-book-bookmark'},
        {'name': 'Hostel Block H1', 'code': 'Hostel H1', 'desc': 'North Wing Dormitories', 'icon': 'fa-bed'},
        {'name': 'Hostel Block H2', 'code': 'Hostel H2', 'desc': 'South Wing Dormitories', 'icon': 'fa-bed'},
        {'name': 'Lab Complex', 'code': 'Lab', 'desc': 'Heavy Machinery Workshops', 'icon': 'fa-gears'},
        {'name': 'Student Cafeteria', 'code': 'Cafeteria', 'desc': 'Dining Commons & Food Court', 'icon': 'fa-utensils'},
    ]

    zone_counts = query_db("""
        SELECT location_block,
               COUNT(*) as count,
               SUM(CASE WHEN priority = 'Urgent' THEN 1 ELSE 0 END) as urgent_count,
               SUM(CASE WHEN priority = 'High' THEN 1 ELSE 0 END) as high_count
        FROM issues
        WHERE status NOT IN ('Resolved', 'Closed')
        GROUP BY location_block
    """)

    heatmap_data = []
    for z in CAMPUS_ZONES:
        match = next((row for row in zone_counts if z['code'].lower() in (row['location_block'] or '').lower() or (row['location_block'] or '').lower() in z['code'].lower()), None)
        cnt = match['count'] if match else 0
        urg = match['urgent_count'] if match else 0
        high = match['high_count'] if match else 0

        if urg > 0:
            heat_level = 'hazard'
            heat_label = 'Safety Hazard'
        elif cnt >= 3 or high > 0:
            heat_level = 'warning'
            heat_label = f'{cnt} Active'
        elif cnt > 0:
            heat_level = 'moderate'
            heat_label = f'{cnt} Active'
        else:
            heat_level = 'clear'
            heat_label = 'Operational'

        heatmap_data.append({
            'name': z['name'],
            'code': z['code'],
            'desc': z['desc'],
            'icon': z['icon'],
            'count': cnt,
            'urgent_count': urg,
            'heat_level': heat_level,
            'heat_label': heat_label
        })

    # Live Incident Activity Stream
    activity_stream = query_db("""
        SELECT i.id, i.ticket_id, i.title, i.category, i.priority, i.status, 
               i.location_block, i.location_room, i.created_at, u.name as actor_name
        FROM issues i
        JOIN users u ON i.student_id = u.id
        ORDER BY i.created_at DESC
        LIMIT 6
    """)

    # All standardized categories
    categories = [
        'Electrical',
        'Water & Plumbing',
        'Internet/Wi-Fi',
        'Sanitation/Housekeeping',
        'Classroom Infrastructure'
    ]

    return render_template(
        'admin_dashboard.html',
        total_complaints=total_issues,
        total_issues=total_issues,
        pending_complaints=reported_issues,
        reported_issues=reported_issues,
        under_review_issues=under_review_issues,
        in_progress_complaints=in_progress_issues,
        in_progress_issues=in_progress_issues,
        resolved_complaints=resolved_issues,
        resolved_issues=resolved_issues,
        urgent_complaints=urgent_issues,
        urgent_issues=urgent_issues,
        active_issues_count=active_issues_count,
        on_track_count=on_track_count,
        breached_count=breached_count,
        sla_compliance_pct=sla_compliance_pct,
        heatmap_data=heatmap_data,
        activity_stream=activity_stream,
        complaints=issues_with_sla,
        issues=issues_with_sla,
        categories=categories,
        current_status=status_filter,
        current_category=category_filter,
        current_priority=priority_filter,
        search_query=search_query
    )

@app.route('/admin/issue/<int:issue_id>/quick-status', methods=['POST'])
@admin_required
def admin_quick_status(issue_id):
    """
    Rapid 1-click status transition handler for admin operations:
    Transitions: Reported -> Under Review -> In Progress -> Resolved -> Closed
    """
    new_status = request.form.get('new_status')
    resolution_notes = request.form.get('resolution_notes', '').strip()

    valid_statuses = ['Reported', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Closed']
    if new_status not in valid_statuses:
        flash("Invalid status transition requested.", "danger")
        return redirect(request.referrer or url_for('admin_dashboard'))

    issue = query_db("SELECT * FROM issues WHERE id = ?", (issue_id,), one=True)
    if not issue:
        flash("Grievance record not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    now = datetime.now()
    resolved_at = now if new_status in ('Resolved', 'Closed') else (issue['resolved_at'] if new_status in ('Resolved', 'Closed') else None)
    notes = resolution_notes or issue['resolution_notes']

    execute_db("""
        UPDATE issues 
        SET status = ?, resolution_notes = ?, updated_at = ?, resolved_at = ?
        WHERE id = ?
    """, (new_status, notes, now, resolved_at, issue_id))

    # Log transition into comments
    log_text = f"Status advanced to [{new_status}] by campus facilities administrator."
    if resolution_notes:
        log_text += f" Resolution notes: {resolution_notes}"
    execute_db("""
        INSERT INTO comments (issue_id, user_id, comment)
        VALUES (?, ?, ?)
    """, (issue_id, session['user_id'], log_text))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'new_status': new_status, 'ticket_id': issue['ticket_id']})

    flash(f"Ticket {issue['ticket_id']} successfully moved to [{new_status}].", "success")
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/issue/<int:issue_id>/update', methods=['POST'])
@admin_required
def admin_update_issue(issue_id):
    """Admin updates status, priority, and resolution remarks"""
    status = request.form.get('status')
    priority = request.form.get('priority')
    resolution_notes = request.form.get('admin_notes', '').strip() or request.form.get('resolution_notes', '').strip()

    issue = query_db("SELECT * FROM issues WHERE id = ?", (issue_id,), one=True)
    if not issue:
        flash("Issue not found.", "danger")
        return redirect(url_for('admin_dashboard'))

    now = datetime.now()
    resolved_at = now if status in ('Resolved', 'Closed') else (issue['resolved_at'] if status in ('Resolved', 'Closed') else None)

    execute_db("""
        UPDATE issues 
        SET status = ?, priority = ?, resolution_notes = ?, updated_at = ?, resolved_at = ?
        WHERE id = ?
    """, (status, priority, resolution_notes, now, resolved_at, issue_id))

    if resolution_notes and resolution_notes != issue['resolution_notes']:
        execute_db("""
            INSERT INTO comments (issue_id, user_id, comment)
            VALUES (?, ?, ?)
        """, (issue_id, session['user_id'], f"Admin remark: {resolution_notes}"))

    flash(f"Ticket {issue['ticket_id']} updated successfully.", "success")
    return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/complaint/<int:complaint_id>/update', endpoint='admin_update_complaint', methods=['POST'])
@admin_required
def admin_update_complaint(complaint_id):
    return admin_update_issue(complaint_id)

@app.route('/admin/issue/<int:issue_id>/delete', methods=['POST'])
@admin_required
def admin_delete_issue(issue_id):
    """Admin deletes test or inappropriate reports"""
    issue = query_db("SELECT * FROM issues WHERE id = ?", (issue_id,), one=True)
    if issue:
        if issue['image_url']:
            img_path = os.path.join(app.config['UPLOAD_FOLDER'], issue['image_url'])
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except OSError:
                    pass

        execute_db("DELETE FROM issues WHERE id = ?", (issue_id,))
        flash(f"Ticket {issue['ticket_id']} deleted successfully.", "info")
    else:
        flash("Record not found.", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/complaint/<int:complaint_id>/delete', endpoint='admin_delete_complaint', methods=['POST'])
@admin_required
def admin_delete_complaint(complaint_id):
    return admin_delete_issue(complaint_id)

@app.route('/admin/export/csv')
@admin_required
def admin_export_csv():
    """Export all campus issues as a downloadable CSV report for campus facility review"""
    import csv
    import io
    from flask import Response

    issues = query_db("""
        SELECT i.*, u.name as student_name, u.student_id as student_code, u.department, u.email as student_email
        FROM issues i
        JOIN users u ON i.student_id = u.id
        ORDER BY i.created_at DESC
    """)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Ticket ID', 'Title', 'Category', 'Priority', 'Status',
        'Campus Block', 'Room/Landmark', 'Reported By', 'Student ID',
        'Department', 'Resolution Remarks', 'Date Reported', 'Date Resolved'
    ])

    for row in issues:
        writer.writerow([
            row['ticket_id'],
            row['title'],
            row['category'],
            row['priority'],
            row['status'],
            row['location_block'],
            row['location_room'] or '',
            row['student_name'],
            row['student_code'] or '',
            row['department'] or '',
            row['resolution_notes'] or '',
            row['created_at'],
            row['resolved_at'] or ''
        ])

    csv_data = output.getvalue()
    filename = f"CampusCare_Audit_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


# ==========================================
# Announcements Management
# ==========================================

@app.route('/admin/announcements')
@admin_required
def admin_announcements():
    """List & manage campus broadcasts"""
    announcements = query_db("""
        SELECT a.*, u.name as author_name 
        FROM announcements a
        JOIN users u ON a.author_id = u.id
        ORDER BY a.created_at DESC
    """)
    return render_template('admin_announcements.html', announcements=announcements)

@app.route('/admin/announcements/create', methods=['POST'])
@admin_required
def admin_create_announcement():
    """Publish a new campus announcement"""
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    priority = request.form.get('priority', 'General').strip()

    if not title or not content:
        flash("Title and Content are required for announcements.", "danger")
        return redirect(url_for('admin_announcements'))

    execute_db("""
        INSERT INTO announcements (title, content, priority, author_id)
        VALUES (?, ?, ?, ?)
    """, (title, content, priority, session['user_id']))

    flash("Campus announcement published successfully!", "success")
    return redirect(url_for('admin_announcements'))

@app.route('/admin/announcements/<int:announcement_id>/delete', methods=['POST'])
@admin_required
def admin_delete_announcement(announcement_id):
    """Delete an announcement"""
    execute_db("DELETE FROM announcements WHERE id = ?", (announcement_id,))
    flash("Announcement deleted successfully.", "info")
    return redirect(url_for('admin_announcements'))


# ==========================================
# Analytics Dashboard & Data API
# ==========================================

@app.route('/analytics')
def analytics():
    """Visual Analytics Dashboard with Chart.js"""
    total_issues = query_db("SELECT COUNT(*) as count FROM issues", one=True)['count']
    resolved_issues = query_db("SELECT COUNT(*) as count FROM issues WHERE status IN ('Resolved', 'Closed')", one=True)['count']
    reported_issues = query_db("SELECT COUNT(*) as count FROM issues WHERE status IN ('Reported', 'Pending')", one=True)['count']
    in_progress_issues = query_db("SELECT COUNT(*) as count FROM issues WHERE status IN ('In Progress', 'Under Review', 'Assigned')", one=True)['count']
    urgent_count = query_db("SELECT COUNT(*) as count FROM issues WHERE priority = 'Urgent'", one=True)['count']

    resolution_rate = round((resolved_issues / total_issues * 100), 1) if total_issues > 0 else 0

    return render_template(
        'analytics.html',
        total_complaints=total_issues,
        total_issues=total_issues,
        resolved_complaints=resolved_issues,
        resolved_issues=resolved_issues,
        pending_complaints=reported_issues,
        reported_issues=reported_issues,
        in_progress_complaints=in_progress_issues,
        in_progress_issues=in_progress_issues,
        urgent_count=urgent_count,
        resolution_rate=resolution_rate
    )

@app.route('/api/analytics-data')
def api_analytics_data():
    """Provides structured data for Chart.js charts dynamically from issues table"""
    # 1. Category Distribution
    category_rows = query_db("""
        SELECT category, COUNT(*) as count 
        FROM issues 
        GROUP BY category 
        ORDER BY count DESC
    """)
    category_labels = [row['category'] for row in category_rows]
    category_counts = [row['count'] for row in category_rows]

    # 2. Status Breakdown
    status_rows = query_db("""
        SELECT status, COUNT(*) as count 
        FROM issues 
        GROUP BY status
    """)
    status_dict = {'Reported': 0, 'Under Review': 0, 'In Progress': 0, 'Resolved': 0}
    for row in status_rows:
        st = row['status']
        if st in ('Pending', 'Reported'):
            status_dict['Reported'] += row['count']
        elif st in ('Assigned', 'Under Review'):
            status_dict['Under Review'] += row['count']
        elif st == 'In Progress':
            status_dict['In Progress'] += row['count']
        elif st in ('Resolved', 'Closed'):
            status_dict['Resolved'] += row['count']

    # 3. Priority Breakdown
    priority_rows = query_db("""
        SELECT priority, COUNT(*) as count 
        FROM issues 
        GROUP BY priority
    """)
    priority_dict = {'Urgent': 0, 'High': 0, 'Medium': 0, 'Low': 0}
    for row in priority_rows:
        priority_dict[row['priority']] = row['count']

    # 4. Department Breakdown
    dept_rows = query_db("""
        SELECT u.department, COUNT(i.id) as count 
        FROM issues i 
        JOIN users u ON i.student_id = u.id 
        GROUP BY u.department 
        ORDER BY count DESC 
        LIMIT 5
    """)
    dept_labels = [row['department'] or 'General' for row in dept_rows]
    dept_counts = [row['count'] for row in dept_rows]

    return jsonify({
        'categories': {
            'labels': category_labels,
            'data': category_counts
        },
        'status': {
            'labels': list(status_dict.keys()),
            'data': list(status_dict.values())
        },
        'priority': {
            'labels': list(priority_dict.keys()),
            'data': list(priority_dict.values())
        },
        'departments': {
            'labels': dept_labels,
            'data': dept_counts
        }
    })


# ==========================================
# QR Code Station & Placard Engine
# ==========================================

def generate_qr_base64(data_url):
    """Generates PNG base64 data URI of a QR code matching Midnight Mineral palette"""
    try:
        import qrcode
        import io
        import base64
        qr = qrcode.QRCode(box_size=7, border=2)
        qr.add_data(data_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='#10191B', back_color='#F0F2E9')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        # Fallback to public QR server if library fails
        encoded = urllib.parse.quote(data_url)
        return f"https://api.qrserver.com/v1/create-qr-code/?size=220x220&data={encoded}&color=10-25-27&bgcolor=240-242-233"

@app.route('/qr-station')
def qr_station():
    """Interactive Campus QR Placard Station & Generator"""
    base_url = request.host_url.rstrip('/')
    campus_placards = [
        {
            'block': 'Tech Block A',
            'room': 'Lab 204 (AI Lab)',
            'desc': 'Computer Science, AI & Robotics Labs',
            'icon': 'fa-microchip',
            'accent': '#70D6C6'
        },
        {
            'block': 'Science Block B',
            'room': 'Room 302 (Physics Wing)',
            'desc': 'Applied Physics & Chemistry Research',
            'icon': 'fa-atom',
            'accent': '#C3E88D'
        },
        {
            'block': 'Central Library',
            'room': '2nd Floor Reading Room',
            'desc': 'Quiet Study Zones & Digital Archives',
            'icon': 'fa-book-open',
            'accent': '#70C9A0'
        },
        {
            'block': 'Hostel Block H1',
            'room': 'Room 102 (Ground Floor)',
            'desc': 'Men’s Residential Complex Wing 1',
            'icon': 'fa-bed',
            'accent': '#E5B45C'
        },
        {
            'block': 'Student Cafeteria',
            'room': 'Dining Hall Counter 3',
            'desc': 'Central Dining, Food Court & Kitchens',
            'icon': 'fa-utensils',
            'accent': '#F07868'
        },
        {
            'block': 'Admin Block C',
            'room': 'Dean Academic Office 101',
            'desc': 'Admissions, Registrars & Student Welfare',
            'icon': 'fa-landmark',
            'accent': '#A7B6B0'
        }
    ]

    for p in campus_placards:
        target_path = f"/report?block={urllib.parse.quote(p['block'])}&room={urllib.parse.quote(p['room'])}"
        full_url = f"{base_url}{target_path}"
        p['target_path'] = target_path
        p['full_url'] = full_url
        p['qr_b64'] = generate_qr_base64(full_url)

    return render_template('qr_station.html', placards=campus_placards, base_url=base_url)

@app.route('/api/generate-qr', methods=['POST'])
def api_generate_qr():
    """Dynamic QR Generator API for any Block and Room"""
    data = request.get_json() or {}
    block = data.get('block', 'Tech Block A').strip()
    room = data.get('room', 'Lab 101').strip()

    base_url = request.host_url.rstrip('/')
    target_path = f"/report?block={urllib.parse.quote(block)}&room={urllib.parse.quote(room)}"
    full_url = f"{base_url}{target_path}"
    qr_b64 = generate_qr_base64(full_url)

    return jsonify({
        'success': True,
        'block': block,
        'room': room,
        'target_path': target_path,
        'full_url': full_url,
        'qr_data_url': qr_b64
    })


# ==========================================
# Run Server
# ==========================================


if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)
