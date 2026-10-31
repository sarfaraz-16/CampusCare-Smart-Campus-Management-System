import re
import sqlite3
import os
from config import Config

# Primary categories mandated for CampusCare
CATEGORIES = {
    'Electrical': {
        'spark': 5, 'electric': 4, 'shock': 5, 'short circuit': 5, 'wire': 4,
        'wiring': 4, 'exposed wire': 5, 'live wire': 5, 'power': 3, 'switch': 3,
        'socket': 3, 'plug': 3, 'fuse': 4, 'light': 2, 'bulb': 3, 'tube light': 3,
        'tubelight': 3, 'ac': 3, 'air conditioner': 4, 'fan': 3, 'blackout': 4,
        'generator': 4, 'voltage': 3, 'tripping': 4, 'cable': 3, 'power cut': 4,
        'transformer': 5, 'mcb': 4, 'burning smell': 5
    },
    'Water & Plumbing': {
        'water': 3, 'leak': 4, 'leakage': 4, 'water leakage': 5, 'pipe': 4,
        'tap': 4, 'faucet': 4, 'sink': 3, 'washroom': 3, 'toilet': 3, 'restroom': 3,
        'flush': 4, 'overflow': 4, 'drain': 4, 'drainage': 4, 'sewage': 5,
        'drinking water': 4, 'cooler': 3, 'water cooler': 4, 'filter': 3,
        'tank': 3, 'clogged': 4, 'choked': 4, 'plumbing': 4, 'drip': 3,
        'dripping': 3, 'water shortage': 4, 'no water': 5
    },
    'Internet/Wi-Fi': {
        'wifi': 5, 'wi-fi': 5, 'internet': 4, 'network': 4, 'lan': 4,
        'ethernet': 4, 'router': 4, 'signal': 3, 'portal': 3, 'login': 2,
        'dns': 3, 'connection': 3, 'disconnect': 3, 'offline': 4, 'bandwidth': 3,
        'slow net': 4, 'speed': 2, 'latency': 3, 'ping': 3, 'packet loss': 4,
        'access point': 4, 'hotspot': 3
    },
    'Sanitation/Housekeeping': {
        'garbage': 4, 'trash': 4, 'dustbin': 4, 'dirty': 4, 'smell': 4,
        'stink': 4, 'odor': 4, 'clean': 3, 'cleaning': 3, 'mop': 3, 'litter': 4,
        'waste': 3, 'cockroach': 4, 'pest': 4, 'mosquito': 4, 'sanitary': 4,
        'hygiene': 4, 'dust': 2, 'bins': 3, 'food waste': 4, 'unhygienic': 4,
        'sweep': 3, 'restroom dirty': 4
    },
    'Classroom Infrastructure': {
        'projector': 5, 'screen': 3, 'mic': 4, 'microphone': 4, 'speaker': 4,
        'audio': 3, 'sound': 3, 'bench': 3, 'desk': 3, 'chair': 3, 'board': 3,
        'blackboard': 3, 'whiteboard': 3, 'podium': 3, 'marker': 3, 'duster': 3,
        'lab': 3, 'computer': 3, 'pc': 3, 'monitor': 3, 'keyboard': 3, 'mouse': 3,
        'display': 3, 'door': 3, 'window': 3, 'lock': 4, 'key': 3, 'handle': 3,
        'wall': 3, 'ceiling': 4, 'floor': 3, 'tile': 3, 'crack': 4, 'stair': 3,
        'stairs': 3, 'railing': 3, 'lift': 5, 'elevator': 5, 'roof': 4, 'glass': 3,
        'broken glass': 5, 'broken chair': 4, 'broken door': 4
    }
}

# Critical Hazard Triggers (Urgent)
CRITICAL_HAZARD_TRIGGERS = [
    'fire', 'spark', 'electric shock', 'short circuit', 'smoke', 'gas leak',
    'blast', 'explosion', 'live wire', 'exposed wire', 'emergency', 'danger',
    'hazard', 'ceiling falling', 'elevator stuck', 'lift stuck', 'flood',
    'flooding', 'burning smell', 'electrocution', 'collapsed', 'broken glass',
    'water near wire'
]

# High Impact Triggers (High)
HIGH_IMPACT_TRIGGERS = [
    'exam', 'exam hall', 'proctored', 'presentation', 'blackout', 'no water',
    'major leak', 'water leakage', 'all lights off', 'broken lock', 'server down',
    'power outage', 'sewage overflow', 'drinking water contaminated',
    'cannot conduct class', 'whole floor', 'darkness', 'water shortage',
    'lab practical', 'viva', 'urgent'
]

# Moderate Triggers (Medium)
MEDIUM_TRIGGERS = [
    'not working', 'slow', 'blurry', 'flickering', 'dripping', 'broken chair',
    'smell', 'dustbin full', 'audio issue', 'door handle', 'projector issue',
    'noisy fan', 'loose', 'intermittent', 'clogged', 'leaking', 'stuck'
]

# High-impact campus location keywords that elevate priority weighting
HIGH_PRIORITY_LOCATIONS = [
    'exam hall', 'examination', 'server room', 'data center', 'central library',
    'chemistry lab', 'electrical lab', 'substation', 'hostel mess', 'auditorium'
]

def analyze_issue(title, description, location_block='', location_room=''):
    """
    Intelligent categorization, priority scoring engine, and location weighting.
    Runs 100% locally with zero latency and high explainability.
    """
    text = f"{title or ''} {description or ''}".lower()
    loc_text = f"{location_block or ''} {location_room or ''}".lower()

    # 1. Categorization Scoring
    category_scores = {}
    matched_keywords = {}

    for category, keywords_dict in CATEGORIES.items():
        score = 0
        matches = []
        for kw, weight in keywords_dict.items():
            pattern = r'\b' + re.escape(kw) + r'\b'
            count = len(re.findall(pattern, text))
            if count > 0:
                score += weight * count
                matches.append(kw)
        category_scores[category] = score
        if matches:
            matched_keywords[category] = matches

    # Determine highest matching category
    sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
    top_category, top_score = sorted_categories[0]

    if top_score > 0:
        suggested_category = top_category
        confidence = min(96, max(50, int(top_score * 12)))
        category_matches = matched_keywords.get(top_category, [])
    else:
        suggested_category = 'Classroom Infrastructure'
        confidence = 35
        category_matches = []

    # 2. Priority Scoring Engine
    suggested_priority = 'Low'
    priority_reason = 'Routine campus maintenance or minor cosmetic issue'
    matched_priority_kws = []

    # Check Critical Hazards
    for kw in CRITICAL_HAZARD_TRIGGERS:
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, text):
            matched_priority_kws.append(kw)

    if matched_priority_kws:
        suggested_priority = 'Urgent'
        priority_reason = f"Safety Hazard: critical trigger '{matched_priority_kws[0]}' detected"
    else:
        # Check High Impact Triggers
        for kw in HIGH_IMPACT_TRIGGERS:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, text):
                matched_priority_kws.append(kw)

        if matched_priority_kws:
            suggested_priority = 'High'
            priority_reason = f"High Disruption: impact trigger '{matched_priority_kws[0]}' detected"
        else:
            # Check Medium Triggers
            for kw in MEDIUM_TRIGGERS:
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, text):
                    matched_priority_kws.append(kw)

            if matched_priority_kws or top_score >= 4:
                suggested_priority = 'Medium'
                priority_reason = 'Moderate disruption affecting student workflow or facility comfort'

    # 3. Location Weighting Elevation
    location_boost = False
    for loc_kw in HIGH_PRIORITY_LOCATIONS:
        if loc_kw in loc_text or loc_kw in text:
            location_boost = True
            if suggested_priority == 'Low':
                suggested_priority = 'Medium'
                priority_reason += f" (Elevated due to critical location: '{loc_kw}')"
            elif suggested_priority == 'Medium':
                suggested_priority = 'High'
                priority_reason += f" (Elevated to High: priority campus zone '{loc_kw}')"
            break

    # Safety baseline: Electrical issues default to at least Medium
    if suggested_category == 'Electrical' and suggested_priority == 'Low':
        suggested_priority = 'Medium'
        priority_reason = 'Electrical issue requires prompt inspection for fire/shock prevention'

    return {
        'suggested_category': suggested_category,
        'category_confidence': confidence,
        'matched_category_keywords': category_matches,
        'suggested_priority': suggested_priority,
        'priority_reason': priority_reason,
        'matched_priority_keywords': matched_priority_kws,
        'location_boost': location_boost,
        'category_scores': category_scores
    }

def get_active_db_path():
    try:
        from flask import current_app
        if current_app and 'DATABASE' in current_app.config:
            return current_app.config['DATABASE']
    except Exception:
        pass
    return Config.DATABASE

def detect_duplicate_issue(category, location_block, location_room, title="", description="", db_path=None):
    """
    Lightweight duplicate detection heuristic:
    Checks if an open ticket (not Resolved or Closed) with similar category and
    matching location (block and room) already exists.
    """
    block_clean = (location_block or '').strip().lower()
    room_clean = (location_room or '').strip().lower()

    if not block_clean:
        return {'is_duplicate': False, 'duplicate_ticket': None, 'similarity_score': 0.0, 'message': None}

    target_db = db_path or get_active_db_path()
    if not os.path.exists(target_db):
        return {'is_duplicate': False, 'duplicate_ticket': None, 'similarity_score': 0.0, 'message': None}

    try:
        conn = sqlite3.connect(target_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query all active/open issues
        cursor.execute('''
            SELECT id, ticket_id, title, description, category, priority, status,
                   location_block, location_room, created_at
            FROM issues
            WHERE status NOT IN ('Resolved', 'Closed')
            ORDER BY created_at DESC
        ''')
        open_issues = cursor.fetchall()
        conn.close()

        cat_normalized = (category or '').strip().lower()
        title_words = set(re.findall(r'\w{3,}', (title or '').lower()))

        for issue in open_issues:
            issue_block = (issue['location_block'] or '').strip().lower()
            issue_room = (issue['location_room'] or '').strip().lower()
            issue_cat = (issue['category'] or '').strip().lower()

            # Location match logic:
            block_match = (block_clean in issue_block) or (issue_block in block_clean)
            room_match = False
            if room_clean and issue_room:
                room_match = (room_clean in issue_room) or (issue_room in room_clean)
            elif not room_clean and not issue_room:
                room_match = True
            elif not room_clean: # if user didn't specify room, but block matches
                room_match = True

            if block_match and room_match:
                # Category similarity or word overlap
                cat_match = (cat_normalized == issue_cat) or (cat_normalized in issue_cat) or (issue_cat in cat_normalized)
                issue_words = set(re.findall(r'\w{3,}', (issue['title'] or '').lower()))
                common_words = title_words.intersection(issue_words)

                if cat_match or len(common_words) >= 2:
                    score = 0.9 if cat_match and len(common_words) >= 2 else (0.8 if cat_match else 0.7)
                    ticket_info = {
                        'id': issue['id'],
                        'ticket_id': issue['ticket_id'],
                        'title': issue['title'],
                        'category': issue['category'],
                        'priority': issue['priority'],
                        'status': issue['status'],
                        'location_block': issue['location_block'],
                        'location_room': issue['location_room'],
                        'created_at': str(issue['created_at'])
                    }
                    room_display = f", {issue['location_room']}" if issue['location_room'] else ""
                    msg = (
                        f"Active similar issue found: '{issue['title']}' at "
                        f"{issue['location_block']}{room_display} (Ticket ID: {issue['ticket_id']} - {issue['status']})."
                    )
                    return {
                        'is_duplicate': True,
                        'similarity_score': score,
                        'duplicate_ticket': ticket_info,
                        'message': msg
                    }

    except Exception as e:
        print(f"Error checking duplicates: {e}")

    return {
        'is_duplicate': False,
        'duplicate_ticket': None,
        'similarity_score': 0.0,
        'message': None
    }
