import sqlite3
import sys
import os
from werkzeug.security import generate_password_hash
from config import Config
from database import init_db

def seed_database(reset=False):
    """Populate database with rich realistic demo data for hackathon evaluation."""
    do_reset = reset or '--reset' in sys.argv or '-r' in sys.argv
    if do_reset:
        print("Reset flag detected. Re-initializing database tables from scratch...")
        if os.path.exists(Config.DATABASE):
            try:
                conn = sqlite3.connect(Config.DATABASE)
                conn.execute("PRAGMA foreign_keys = OFF")
                conn.execute("DROP VIEW IF EXISTS complaints")
                for entity in ['comments', 'issues', 'announcements', 'users']:
                    conn.execute(f"DROP TABLE IF EXISTS {entity}")
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Notice while clearing tables: {e}")

    init_db()
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if data already exists
    if not do_reset:
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            cursor.execute("SELECT COUNT(*) FROM issues")
            if cursor.fetchone()[0] > 0:
                print("Database already contains issues. Use 'python seed_data.py --reset' if you wish to reset demo data.")
                conn.close()
                return

    print("Seeding database with demo users, issues, comments, and announcements...")

    # 1. Seed Users
    users_data = [
        (
            'Campus Administrator',
            'admin@campuscare.edu',
            'ADM-001',
            'Campus Facilities & Operations',
            'admin',
            generate_password_hash('admin123')
        ),
        (
            'Aarav Mehta',
            'student@campuscare.edu',
            'CS2024-042',
            'Computer Science & Engineering',
            'student',
            generate_password_hash('student123')
        ),
        (
            'Priya Iyer',
            'priya@campuscare.edu',
            'EC2024-118',
            'Electronics & Communication',
            'student',
            generate_password_hash('student123')
        ),
        (
            'Rohan Verma',
            'rohan@campuscare.edu',
            'ME2024-075',
            'Mechanical Engineering',
            'student',
            generate_password_hash('student123')
        )
    ]

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
        INSERT INTO users (name, email, student_id, department, role, password_hash)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', users_data)
        conn.commit()

    # Fetch user IDs
    cursor.execute("SELECT id, email FROM users")
    user_map = {row['email']: row['id'] for row in cursor.fetchall()}
    admin_id = user_map.get('admin@campuscare.edu', 1)
    student_id = user_map.get('student@campuscare.edu', 2)
    priya_id = user_map.get('priya@campuscare.edu', 3)
    rohan_id = user_map.get('rohan@campuscare.edu', 4)

    # 2. Seed Issues
    issues_data = [
        (
            'CC-2026-1001',
            student_id,
            'Severe Spark and Burning Smell from Switchboard',
            'The main electrical switchboard near Lab 4 entrance is throwing continuous sparks with a strong burning plastic smell. Poses an electric shock hazard.',
            'Electrical',
            'Urgent',
            'In Progress',
            'Science Block B',
            'Room 204 (Lab 4)',
            None,
            'Electrician team dispatched. Breaker tripped for safety. Wire replacement currently underway.',
            '2026-10-28 09:15:00',
            '2026-10-28 10:00:00',
            None
        ),
        (
            'CC-2026-1002',
            student_id,
            'Frequent Wi-Fi Disconnection during Online Proctored Exam',
            'Wi-Fi signal keeps dropping every 2 minutes in the Central Library reading hall. Students are unable to submit digital assignments and access research databases.',
            'Internet/Wi-Fi',
            'High',
            'Reported',
            'Central Library',
            '2nd Floor Reading Hall',
            None,
            None,
            '2026-10-29 11:30:00',
            '2026-10-29 11:30:00',
            None
        ),
        (
            'CC-2026-1003',
            student_id,
            'Water Overflow and Flooding in 1st Floor Restroom',
            'The flush valve is completely broken and clean water is overflowing into the hallway, causing slippery dangerous stairs.',
            'Water & Plumbing',
            'High',
            'Resolved',
            'Academic Block A',
            '1st Floor Boys Restroom',
            None,
            'Plumbing technician replaced the broken dual-flush valve. Floor thoroughly dried and sanitized by housekeeping staff.',
            '2026-10-27 08:45:00',
            '2026-10-27 12:20:00',
            '2026-10-27 12:20:00'
        ),
        (
            'CC-2026-1004',
            priya_id,
            'Overhead Projector Display Flickering and Blurry',
            'The HDMI connection or projector lamp is malfunctioning. Color shifts heavily to green and screen flickers during lectures.',
            'Classroom Infrastructure',
            'Medium',
            'Under Review',
            'Main Lecture Hall',
            'Room LH-101',
            None,
            'AV technician scheduled to replace the projector lamp module and test HDMI cable.',
            '2026-10-29 14:10:00',
            '2026-10-29 16:30:00',
            None
        ),
        (
            'CC-2026-1005',
            rohan_id,
            'Overflowing Dustbin and Litter around Cafeteria Lawn',
            'Garbage bins near the food court patio are overflowing since yesterday afternoon. Stray dogs and crows are scattering waste.',
            'Sanitation/Housekeeping',
            'Medium',
            'Resolved',
            'Campus Cafeteria',
            'Outdoor Lawn Patio',
            None,
            'Sanitation supervisors cleared all waste and stationed two additional segregated recycling bins.',
            '2026-10-26 13:00:00',
            '2026-10-26 15:45:00',
            '2026-10-26 15:45:00'
        ),
        (
            'CC-2026-1006',
            priya_id,
            'Loose Door Handle and Jammed Key Lock',
            'The lock of Room 312 faculty conference room is stuck and the external handle came off.',
            'Classroom Infrastructure',
            'Low',
            'Reported',
            'Admin Block',
            '3rd Floor, Room 312',
            None,
            None,
            '2026-10-30 09:20:00',
            '2026-10-30 09:20:00',
            None
        ),
        (
            'CC-2026-1007',
            rohan_id,
            'Passenger Lift Stuck Between 2nd and 3rd Floor',
            'Lift No. 2 made a loud screeching noise and halted. Emergency alarm was triggered. Need urgent elevator technician.',
            'Classroom Infrastructure',
            'Urgent',
            'In Progress',
            'Engineering Block C',
            'Central Elevator Shaft',
            None,
            'Elevator maintenance contract team on-site. Passengers safely evacuated. Safety brake inspection ongoing.',
            '2026-10-30 14:05:00',
            '2026-10-30 14:25:00',
            None
        )
    ]

    cursor.execute("SELECT COUNT(*) FROM issues")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
        INSERT INTO issues (
            ticket_id, student_id, title, description, category, priority,
            status, location_block, location_room, image_url, resolution_notes,
            created_at, updated_at, resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', issues_data)
        conn.commit()

    # 3. Seed Comments
    cursor.execute("SELECT id FROM issues WHERE ticket_id = 'CC-2026-1001'")
    issue_1 = cursor.fetchone()
    if issue_1:
        cursor.execute("SELECT COUNT(*) FROM comments WHERE issue_id = ?", (issue_1['id'],))
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO comments (issue_id, user_id, comment, created_at)
                VALUES (?, ?, 'Electrician team has isolated the main circuit breaker. Technicians are on site.', '2026-10-28 09:40:00')
            ''', (issue_1['id'], admin_id))
            cursor.execute('''
                INSERT INTO comments (issue_id, user_id, comment, created_at)
                VALUES (?, ?, 'Thank you for the quick action! The burning smell has subsided.', '2026-10-28 10:15:00')
            ''', (issue_1['id'], student_id))
            conn.commit()

    # 4. Seed Announcements
    announcements_data = [
        (
            'Campus-wide Wi-Fi Core Switch Upgrade Notice',
            'The IT Infrastructure team will be upgrading core fiber distribution switches this Saturday between 11:00 PM and 3:00 AM. Internet access will be temporarily intermittent in Hostels and Labs.',
            'Important',
            admin_id,
            '2026-10-28 10:00:00'
        ),
        (
            'Precautionary Electrical & Safety Audit This Week',
            'Facilities Department is conducting thorough safety inspections of all laboratory breaker panels and backup generators. Please cooperate with the visiting maintenance engineers.',
            'Urgent',
            admin_id,
            '2026-10-29 09:30:00'
        ),
        (
            'Green Campus Cleanliness Drive & E-Waste Collection',
            'Join the student council and maintenance committee this Friday at 4 PM for the semester E-waste recycling drive near Main Plaza. Refreshments provided.',
            'General',
            admin_id,
            '2026-10-30 12:00:00'
        )
    ]

    cursor.execute("SELECT COUNT(*) FROM announcements")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
        INSERT INTO announcements (title, content, priority, author_id, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', announcements_data)
        conn.commit()

    conn.close()
    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed_database()
