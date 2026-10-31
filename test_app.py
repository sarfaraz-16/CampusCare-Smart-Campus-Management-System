import os
import tempfile
import sqlite3
from werkzeug.security import generate_password_hash

from app import app
from database import init_db, query_db

def test_full_application():
    """Run non-destructive test suite on a temporary in-memory/temp database"""
    fd, temp_db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    app.config['DATABASE'] = temp_db_path
    app.config['TESTING'] = True

    try:
        with app.app_context():
            init_db()
            conn = sqlite3.connect(temp_db_path)
            cur = conn.cursor()
            
            # Seed test users
            cur.execute("""
                INSERT INTO users (name, email, student_id, department, role, password_hash)
                VALUES ('Admin User', 'admin@campuscare.edu', 'ADM-1', 'Facilities', 'admin', ?)
            """, (generate_password_hash('admin123'),))

            cur.execute("""
                INSERT INTO users (name, email, student_id, department, role, password_hash)
                VALUES ('Test Student', 'student@campuscare.edu', 'STU-1', 'Computer Science', 'student', ?)
            """, (generate_password_hash('student123'),))
            conn.commit()
            conn.close()

        client = app.test_client()

        print("=== Running Non-Destructive Automated Tests on Isolated Temp DB ===")

        # 1. Landing page
        res = client.get('/')
        assert res.status_code == 200, "Landing page failed"
        print("[PASS] 1. Landing page loaded (200 OK)")

        # 2. Student Demo Login
        res = client.get('/login?demo=student', follow_redirects=True)
        assert res.status_code == 200
        print("[PASS] 2. Student Demo 1-Click Login successful")

        # 3. Student Dashboard
        res = client.get('/dashboard')
        assert res.status_code == 200
        print("[PASS] 3. Student Dashboard loaded (200 OK)")

        # 4. API Smart Analyzer with Category & Priority Heuristics
        res = client.post('/api/analyze-issue', json={
            'title': 'Severe electrical spark in room 101 switchboard',
            'description': 'The power socket threw sparks with burning smell.',
            'location_block': 'Engineering Block A',
            'location_room': 'Lab 101'
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data['suggested_category'] == 'Electrical'
        assert data['suggested_priority'] == 'Urgent'
        print(f"[PASS] 4. Smart Analyzer Rule Engine: {data['suggested_category']} -> {data['suggested_priority']}")

        # 5. Lodging an Issue
        res = client.post('/report', data={
            'title': 'Severe electrical spark in room 101 switchboard',
            'description': 'The power socket threw sparks with burning smell.',
            'location_block': 'Lab Block A',
            'location_room': 'Room 101',
            'category': 'Auto-Detect',
            'priority': 'Auto',
            'auto_classify': 'true'
        }, follow_redirects=True)
        assert res.status_code == 200
        print("[PASS] 5. Report Issue form submitted successfully")

        with app.app_context():
            latest = query_db("SELECT * FROM issues ORDER BY id DESC LIMIT 1", one=True)
            assert latest is not None
            ticket_id = latest['ticket_id']
            issue_id = latest['id']
            assert latest['category'] == 'Electrical'
            assert latest['priority'] == 'Urgent'
            assert latest['status'] == 'Reported'

        # 6. Duplicate Detection Heuristic Test
        dup_res = client.post('/api/analyze-issue', json={
            'title': 'Another spark reported',
            'description': 'Sparking switchboard in the same lab room.',
            'location_block': 'Lab Block A',
            'location_room': 'Room 101'
        })
        dup_data = dup_res.get_json()
        assert dup_data['duplicate']['is_duplicate'] is True
        print(f"[PASS] 6. Duplicate Detection Flagged Ticket: {dup_data['duplicate']['duplicate_ticket']['ticket_id']}")

        # 7. QR-Code Autofill GET parameters
        qr_res = client.get('/report?block=CSE&room=Lab-2')
        assert qr_res.status_code == 200
        assert b'CSE' in qr_res.data
        assert b'Lab-2' in qr_res.data
        print("[PASS] 7. QR-code URL parameters pre-populated in form")

        # 8. Issue Tracking by ID
        res = client.get(f'/track/{ticket_id}')
        assert res.status_code == 200
        assert ticket_id.encode() in res.data
        print(f"[PASS] 8. Tracking view validated for Ticket ID {ticket_id}")

        # 9. Posting a Comment on Issue
        comment_res = client.post(f'/issue/{issue_id}/comment', data={
            'comment': 'Maintenance crew please carry spare 16A circuit breaker.'
        }, follow_redirects=True)
        assert comment_res.status_code == 200
        with app.app_context():
            comment_row = query_db("SELECT * FROM comments WHERE issue_id = ? ORDER BY id DESC LIMIT 1", (issue_id,), one=True)
            assert comment_row is not None
            assert '16A circuit breaker' in comment_row['comment']
        print("[PASS] 9. Follow-up comment lifecycle validated")

        # 10. Admin Demo Login
        res = client.get('/login?demo=admin', follow_redirects=True)
        assert res.status_code == 200
        print("[PASS] 10. Admin Demo 1-Click Login successful")

        # 11. 1-Click Quick Status Transition: Reported -> Under Review -> In Progress
        res = client.post(f'/admin/issue/{issue_id}/quick-status', data={
            'new_status': 'In Progress'
        }, follow_redirects=True)
        assert res.status_code == 200
        with app.app_context():
            issue_check = query_db("SELECT * FROM issues WHERE id = ?", (issue_id,), one=True)
            assert issue_check['status'] == 'In Progress'
        print("[PASS] 11. 1-Click Status transition to 'In Progress' verified")

        # 12. Marking Issue as Resolved with Resolution Notes
        res = client.post(f'/admin/issue/{issue_id}/quick-status', data={
            'new_status': 'Resolved',
            'resolution_notes': 'Breaker panel replaced, wire insulated, certified safe by electrical inspector.'
        }, follow_redirects=True)
        assert res.status_code == 200

        with app.app_context():
            updated = query_db("SELECT * FROM issues WHERE id = ?", (issue_id,), one=True)
            assert updated['status'] == 'Resolved'
            assert updated['resolved_at'] is not None
            assert 'inspected' in updated['resolution_notes'].lower() or 'certified' in updated['resolution_notes'].lower()
        print("[PASS] 12. Admin marked issue 'Resolved' with resolution notes and timestamp")

        # 13. Admin Announcement Broadcast
        res = client.post('/admin/announcements/create', data={
            'title': 'Campus Power Grid Maintenance',
            'content': 'Routine inspection will be carried out this Sunday morning.',
            'priority': 'Urgent'
        }, follow_redirects=True)
        assert res.status_code == 200
        print("[PASS] 13. Admin announcement broadcast published")

        # 14. Analytics Data API (Dynamic from issues)
        res = client.get('/api/analytics-data')
        assert res.status_code == 200
        analytics = res.get_json()
        assert len(analytics['categories']['labels']) > 0
        assert 'Electrical' in analytics['categories']['labels']
        print("[PASS] 14. Analytics Chart.js endpoint returned valid dynamic statistics")

        # 15. Admin Export Issues CSV
        res = client.get('/admin/export/csv')
        assert res.status_code == 200
        assert b'Ticket ID,Title,Category' in res.data
        assert b'Severe electrical spark' in res.data
        print("[PASS] 15. Admin downloadable CSV report exported successfully")

        print("\n>>> ALL 15 TESTS PASSED CLEANLY ON ISOLATED TEST DB! <<<\n")

    finally:
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except OSError:
                pass

if __name__ == '__main__':
    test_full_application()
