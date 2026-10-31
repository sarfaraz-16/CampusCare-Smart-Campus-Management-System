import sqlite3
import os
import re
from flask import g, current_app
from config import Config

def get_db_path():
    try:
        if current_app:
            return current_app.config.get('DATABASE', Config.DATABASE)
    except RuntimeError:
        pass
    return Config.DATABASE

def get_db():
    """Get or create SQLite database connection in request context with dict-like row factory."""
    if 'db' not in g:
        g.db = sqlite3.connect(get_db_path(), detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    """Close the database connection when application context tears down."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(db_path=None):
    """
    Initialize database tables for CampusCare.
    Ensures tables: users, issues, comments, announcements.
    Includes backward-compatible migration from legacy complaints table.
    """
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        student_id TEXT UNIQUE,
        department TEXT,
        role TEXT NOT NULL DEFAULT 'student',
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Issues Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT UNIQUE NOT NULL,
        student_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        priority TEXT NOT NULL CHECK(priority IN ('Urgent', 'High', 'Medium', 'Low')) DEFAULT 'Medium',
        status TEXT NOT NULL CHECK(status IN ('Reported', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Closed')) DEFAULT 'Reported',
        location_block TEXT NOT NULL,
        location_room TEXT,
        image_url TEXT,
        resolution_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # 3. Comments Table (Audit and follow-up communication)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (issue_id) REFERENCES issues (id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # 4. Announcements Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'General',
        author_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (author_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')

    # Create Indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_issues_ticket ON issues (ticket_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_issues_student ON issues (student_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_issues_status ON issues (status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_issues_category ON issues (category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_issues_location ON issues (location_block, location_room)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_issue ON comments (issue_id)')

    # Check for legacy complaints table migration
    cursor.execute("SELECT name, type FROM sqlite_master WHERE name = 'complaints'")
    complaints_entity = cursor.fetchone()

    category_map = {
        'Electricity': 'Electrical',
        'Water Supply': 'Water & Plumbing',
        'Wi-Fi & Network': 'Internet/Wi-Fi',
        'Cleanliness & Hygiene': 'Sanitation/Housekeeping',
        'Classroom & Labs': 'Classroom Infrastructure',
        'Infrastructure & Maintenance': 'Classroom Infrastructure',
        'Security & Safety': 'Classroom Infrastructure'
    }

    if complaints_entity and complaints_entity['type'] == 'table':
        cursor.execute("SELECT COUNT(*) as count FROM complaints")
        complaints_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM issues")
        issues_count = cursor.fetchone()['count']

        if complaints_count > 0 and issues_count == 0:
            cursor.execute("SELECT * FROM complaints")
            old_rows = cursor.fetchall()
            for row in old_rows:
                # Parse location into block and room
                loc = (row['location'] or '').strip()
                block = loc
                room = ''
                if ',' in loc:
                    parts = [p.strip() for p in loc.split(',', 1)]
                    block = parts[0]
                    room = parts[1]

                # Map status
                old_status = row['status']
                new_status = 'Reported' if old_status in ('Pending', 'Submitted') else old_status
                if new_status not in ('Reported', 'Under Review', 'Assigned', 'In Progress', 'Resolved', 'Closed'):
                    new_status = 'Reported'

                # Map category
                cat = category_map.get(row['category'], row['category'])

                cursor.execute('''
                INSERT INTO issues (
                    id, ticket_id, student_id, title, description, category,
                    priority, status, location_block, location_room, image_url,
                    resolution_notes, created_at, updated_at, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['id'],
                    row['tracking_id'],
                    row['user_id'],
                    row['title'],
                    row['description'],
                    cat,
                    row['priority'],
                    new_status,
                    block,
                    room,
                    row['image_filename'],
                    row['admin_notes'],
                    row['created_at'],
                    row['updated_at'],
                    row['resolved_at']
                ))

            # Drop the old complaints table and replace with backward-compatible VIEW
            cursor.execute("DROP TABLE complaints")
            cursor.execute('''
            CREATE VIEW IF NOT EXISTS complaints AS
            SELECT 
                id,
                ticket_id AS tracking_id,
                student_id AS user_id,
                title,
                description,
                category,
                (location_block || CASE WHEN location_room IS NOT NULL AND location_room != '' THEN ', ' || location_room ELSE '' END) AS location,
                priority,
                status,
                image_url AS image_filename,
                resolution_notes AS admin_notes,
                created_at,
                updated_at,
                resolved_at
            FROM issues
            ''')
    elif not complaints_entity:
        # Create complaints VIEW pointing to issues for complete compatibility
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS complaints AS
        SELECT 
            id,
            ticket_id AS tracking_id,
            student_id AS user_id,
            title,
            description,
            category,
            (location_block || CASE WHEN location_room IS NOT NULL AND location_room != '' THEN ', ' || location_room ELSE '' END) AS location,
            priority,
            status,
            image_url AS image_filename,
            resolution_notes AS admin_notes,
            created_at,
            updated_at,
            resolved_at
        FROM issues
        ''')

    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    """Convenient query helper returning sqlite3.Row dict-like objects."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """Convenient execute helper committing changes and returning lastrowid."""
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    lastrowid = cur.lastrowid
    cur.close()
    return lastrowid
