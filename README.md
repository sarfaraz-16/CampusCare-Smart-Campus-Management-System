# 🏛️ CampusCare – Smart Campus Management System
> **Centralized Campus Grievance Ticketing & Automated Facilities Management Web Platform**  
> *Built for National-Level Hackathons with Python Flask, SQLite, Vanilla JS, and Chart.js.*

---

## 🌟 Executive Summary & Hackathon Pitch

In large university campuses, infrastructure and facility breakdowns (such as dangerous electrical sparks, Wi-Fi outages during proctored exams, overflowing washroom pipes, or broken classroom projectors) often go unnoticed, get lost in bureaucratic WhatsApp groups, or lack accountability.

**CampusCare** solves this with an intelligent, centralized campus management platform that:
1. **Automates Triage with Heuristic AI**: Uses a transparent, keyword-weighted rule engine to classify issues and instantly flag urgent life-safety hazards with location-aware weighting (zero paid APIs required).
2. **Proactively Prevents Duplicate Reports**: Evaluates active open issues by campus block and room, warning students before they lodge identical tickets.
3. **Streamlines Incident Reporting via QR Codes**: Supports static QR code parameters (`/report?block=CSE&room=Lab-2`) to auto-populate building and room locations in under 5 seconds.
4. **Eliminates Dead-Ends with 4-Stage Stepper**: Generates unique tracking IDs (`CC-2026-XXXX`) with a visual 4-milestone lifecycle progress bar:
   $$\text{Reported (12\%)} \longrightarrow \text{Review (38\%)} \longrightarrow \text{In Progress (68\%)} \longrightarrow \text{Resolved (100\%) }$$
5. **Empowers Administration with 1-Click Transitions**: Provides an operations control room with rapid 1-click status transitions, resolution notes logging, automated **SLA breach alerts**, and campus-wide broadcast notices.
6. **Delivers Deep Visibility & Audit Export**: Features an interactive **Chart.js** analytics dashboard and 1-click **CSV report export** for campus facility review.

---

## 🎨 Design System & UI/UX Highlights

- **Theme Identity**: **MIDNIGHT MINERAL × ARCTIC SIGNAL** — Premium Command Centre Dark Mode.
  - *Obsidian · Deep Mineral · Moss Lime · Aqua · Soft Ivory*
- **Design Tokens**:
  | Token | Hex / Value | Usage & Visual Role |
  | :--- | :--- | :--- |
  | **Canvas** | `#10191B` | Main page background (Deep Obsidian Mineral) |
  | **Surface** | `#192729` | KPI cards, data tables, sidebars, modal surfaces |
  | **Elevated** | `#263A39` | Hover states, active tabs, modal elevation |
  | **Border** | `#344847` | Subtle structural borders and card outlines |
  | **Primary Text** | `#F0F2E9` | Soft Ivory headings, high-readability values |
  | **Secondary Text** | `#A7B6B0` | Mineral Sage supporting text and metadata |
  | **Accent** | `#C3E88D` | Moss Lime primary actions / buttons (`#10191B` high contrast text) |
  | **AI Accent** | `#70D6C6` | Arctic Signal Aqua for AI classification and smart preview |
  | **Urgent** | `#F07868` | Critical hazard alerts and SLA breach badges |
  | **Warning** | `#E5B45C` | Pending / Reported warnings & duplicate alerts |
  | **Resolved** | `#70C9A0` | Completed tickets and verified resolutions |
- **Typography**: *Plus Jakarta Sans* for clean, modern interface reading paired with *JetBrains Mono* for ticket tracking numbers (`CC-2026-XXXX`) and audit timestamps.
- **Responsiveness**: Fully responsive desktop and mobile experience with collapsable sidebar navigation, touch-friendly cards, and toast notifications.
- **Judge-Ready**: Includes **1-Click Demo Login shortcuts** on both the Landing Page and Sign-In page so evaluators can inspect student and admin workflows without manual typing!

---

## 🚀 Key Functional Modules

| Module | Description |
| :--- | :--- |
| **Hero & Landing Page** | Modern animated landing page with live system statistics, feature breakdowns, and campus broadcast alerts. |
| **Student Workspace** | KPI metric cards (Total, Reported, In Progress, Resolved), filtered grievances table, and recent campus notices. |
| **Smart Grievance Reporting** | Real-time classification assistant as you type title and description, drag-and-drop photo attachment, location mapping. |
| **QR Code Auto-fill** | Query parameter parsing (`/report?block=CSE&room=Lab-2`) pre-fills block and room fields automatically with a green glowing badge. |
| **Duplicate Detection Heuristic** | Real-time check against active open issues in the same block/room, alerting students before lodging duplicates. |
| **Keyword Triage Engine** | 100% local rule engine categorizing issues into `Electrical`, `Water & Plumbing`, `Internet/Wi-Fi`, `Sanitation/Housekeeping`, or `Classroom Infrastructure`. |
| **Public & Student Tracking** | Direct lookup by Ticket ID (`CC-2026-1001`) with an animated 4-stage stepper, resolution notes, and collaborative comment feed. |
| **Admin Operations Hub** | Centralized facility triage table with live search, multi-factor filtering, priority assignment, and 1-click status transitions. |
| **SLA Breach Monitoring** | Automated elapsed hour calculation with pulsating red badge (`⚠️ SLA Breached`) for overdue active issues. |
| **Resolution Notes Logging** | Dedicated resolution modal requiring technician remarks when marking an issue as `Resolved`. |
| **Campus Announcements** | Administrative tool to publish and broadcast maintenance schedules, power outage notices, or emergency advisories. |
| **Visual Analytics & CSV Export** | Dynamic Chart.js charts (Category Donut, Status Pipeline, Priority Matrix, Department Volume) and 1-click downloadable CSV audit export. |

---

## 🛠️ Technology Stack

- **Backend**: Python 3.9+ / [Flask 3.0.3](https://flask.palletsprojects.com/)
- **Database**: SQLite3 (relational schema with `PRAGMA foreign_keys = ON`, indexes, and dictionary row factories)
- **Security**: [Werkzeug](https://werkzeug.palletsprojects.com/) (PBKDF2 SHA-256 password hashing & secure file name handling)
- **Frontend**: HTML5, Vanilla CSS3 Glassmorphism, Modern ES6+ JavaScript
- **Data Visualizations**: [Chart.js 4.4+](https://www.chartjs.org/)
- **Icons & Typography**: Font Awesome 6.5+, Google Fonts (*Plus Jakarta Sans*, *JetBrains Mono*)

---

## 📁 Repository Structure

```text
exathon/
├── app.py                      # Core application router, route controllers, and lifecycle handlers
├── config.py                   # Environment settings, secret keys, upload directory paths
├── database.py                 # SQLite connection manager, schema initialization, and automated migrations
├── seed_data.py                # Database population script with realistic users, issues, comments, and notices
├── smart_analyzer.py           # Local keyword heuristic engine for category, priority, and duplicate detection
├── requirements.txt            # Python dependencies (Flask, Werkzeug)
├── README.md                   # Setup guide, run commands, and team documentation
├── test_app.py                 # Automated 15-step smoke test and regression verification suite
├── campuscare.db               # SQLite database file generated at runtime
│
├── static/
│   ├── css/
│   │   ├── style.css           # Global typography, color tokens, layout resets, utility classes
│   │   ├── dashboard.css       # Layout styles for metrics grids, tables, badges, stepper, sidebars
│   │   └── landing.css         # Hero section, feature cards, landing page branding
│   ├── js/
│   │   ├── main.js             # Global utilities: modals, flash dismissals, clipboard copy, dropzones
│   │   ├── charts.js           # Chart.js initialization for issue trends, status donuts, department bars
│   │   └── smart_classifier.js # Debounced live classifier, QR code autofill, duplicate warning card
│   └── uploads/                # Attached photographic evidence uploaded with complaints
│
└── templates/
    ├── base.html               # Master layout containing navigation bar, flash toasts, footer
    ├── index.html              # Public landing page presenting the project value proposition
    ├── login.html              # Authentication portal with 1-Click Judge Demo shortcuts
    ├── register.html           # Student registration screen with client-side validation
    ├── report_issue.html       # Dynamic issue submission form with live triage hints & duplicate warning
    ├── student_dashboard.html  # Student track-list of submitted grievances with status filters
    ├── track_issue.html        # Detailed 4-stage stepper, technician notes, and collaborative comment feed
    ├── admin_dashboard.html    # Operational control room with 1-click status transitions & SLA tracking
    ├── admin_announcements.html# Broadcast publisher for campus-wide maintenance notices
    └── analytics.html          # Interactive charts showing resolution rates and departmental volumes
```

---

## 🔑 Demo Credentials (For Judges & Evaluators)

The application comes pre-populated with realistic campus data. You can either use the **1-Click Demo Login** shortcuts on the login screen or enter the credentials below:

### 1. Campus Administrator
- **Email**: `admin@campuscare.edu`
- **Password**: `admin123`
- **Role**: Campus Facilities & Operations Admin
- **Capabilities**: View global triage board, advance issues with 1-click (`Reported` ➔ `Under Review` ➔ `In Progress` ➔ `Resolved`), record technician notes, monitor SLA breaches, publish campus announcements, export CSV reports.

### 2. Student Account
- **Email**: `student@campuscare.edu`
- **Password**: `student123`
- **Student ID**: `CS2024-042` (Aarav Mehta - Computer Science)
- **Capabilities**: Lodge new issues with photo evidence, receive real-time keyword category recommendations and duplicate warnings, copy tracking IDs, track progress timelines, post follow-up comments.

*(Additional pre-registered students: `priya@campuscare.edu` / `student123`, `rohan@campuscare.edu` / `student123`)*

---

## ⚡ Installation & Execution Guide

### Step 1: Open Terminal in Project Directory
```bash
# In your terminal or PowerShell:
cd "d:\HACKATHON\campuscare hackathon\exathon"
```

### Step 2: (Optional) Set up a Virtual Environment
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Initialize and Seed the Database
```bash
# Populates realistic demo users, issues, comments, and notices.
# Use the --reset flag anytime to reset to a pristine demo state:
python seed_data.py --reset
```

### Step 5: Start the Web Application
```bash
python app.py
```

### Step 6: Open in Your Browser
Visit: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Running Automated Verification Tests

A comprehensive 15-point automated test suite is included in `test_app.py`. It runs non-destructively on an isolated temporary database to ensure zero side-effects on demo data.

```bash
python test_app.py
```

**Test Suite Coverage:**
```text
=== Running Non-Destructive Automated Tests on Isolated Temp DB ===
[PASS] 1. Landing page loaded (200 OK)
[PASS] 2. Student Demo 1-Click Login successful
[PASS] 3. Student Dashboard loaded (200 OK)
[PASS] 4. Smart Analyzer Rule Engine: Electrical -> Urgent
[PASS] 5. Report Issue form submitted successfully
[PASS] 6. Duplicate Detection Flagged Ticket: CC-2026-2129
[PASS] 7. QR-code URL parameters pre-populated in form
[PASS] 8. Tracking view validated for Ticket ID CC-2026-2129
[PASS] 9. Follow-up comment lifecycle validated
[PASS] 10. Admin Demo 1-Click Login successful
[PASS] 11. 1-Click Status transition to 'In Progress' verified
[PASS] 12. Admin marked issue 'Resolved' with resolution notes and timestamp
[PASS] 13. Admin announcement broadcast published
[PASS] 14. Analytics Chart.js endpoint returned valid dynamic statistics
[PASS] 15. Admin downloadable CSV report exported successfully

>>> ALL 15 TESTS PASSED CLEANLY ON ISOLATED TEST DB! <<<
```

---

## 💡 Smart Triage & Duplicate Heuristics Explained

CampusCare avoids fragile, paid external APIs by utilizing a deterministic, high-throughput **Keyword-Weighted Natural Language Rule Engine** (`smart_analyzer.py`):

1. **Category Detection**:
   - Compares grievance text against domain dictionaries:
     - `Electrical`: `spark`, `socket`, `shock`, `fuse`, `power cut`, `live wire`, `mcb`, `burning smell`
     - `Water & Plumbing`: `water`, `pipe`, `leakage`, `tap`, `flush`, `drainage`, `sewage`, `clogged`
     - `Internet/Wi-Fi`: `wifi`, `internet`, `network`, `router`, `bandwidth`, `dns`, `ping`, `packet loss`
     - `Sanitation/Housekeeping`: `garbage`, `dustbin`, `trash`, `dirty`, `smell`, `pest`, `hygiene`
     - `Classroom Infrastructure`: `projector`, `speaker`, `bench`, `door`, `window`, `broken glass`, `lift`

2. **Priority Triage**:
   - **Urgent**: Critical life-safety hazards (`fire`, `spark`, `electric shock`, `short circuit`, `live wire`, `broken glass`, `flooding`).
   - **High**: Major academic or infrastructure disruptions (`exam hall`, `proctored exam`, `blackout`, `server down`, `water shortage`).
   - **Medium**: Moderate facility inconveniences (`slow wifi`, `blurry projector`, `noisy fan`, `dripping tap`).
   - **Low**: Minor aesthetic or cosmetic repairs.

3. **Campus Location Weighting**:
   - Critical zones (`Exam Hall`, `Server Room`, `Central Library`, `Substation`, `Chemistry Lab`) automatically elevate priority by +1 tier.

4. **Duplicate Detection Engine (`detect_duplicate_issue`)**:
   - Queries open grievances (`status NOT IN ('Resolved', 'Closed')`).
   - Compares `location_block`, `location_room`, and category/title tokens.
   - Triggers an instant amber banner warning if an active grievance is already being handled at that spot.

---

## 🎙️ 3-Minute Live Demo Pitch Sequence

| Time | Action | What Judges See |
| :--- | :--- | :--- |
| **0:00 - 0:30** | Open `http://127.0.0.1:5000/` | Dark glassmorphism landing page with live resolution rates. Click **Student Demo Login**. |
| **0:30 - 1:15** | Open `/report?block=Science%20Block%20B&room=Room%20204%20(Lab%204)` | Pre-filled block and room via QR parameter. Type: *"Electrical spark and burning smell near switchboard"*. Show **Urgent (Hazard)** auto-tagging and **Duplicate Warning Banner**. |
| **1:15 - 2:15** | Switch to **Admin Demo Login** (`/admin/dashboard`) | View operations control center. Point out **SLA Breached** alert. Advance status with 1-click **Dispatch Tech** $\rightarrow$ **Resolve** (with resolution remarks). |
| **2:15 - 3:00** | Open `/track/CC-2026-1001` and `/analytics` | 4-step progress stepper advancing to **Resolved** with resolution notes and comment feed. Show Chart.js visual analytics and download the **CSV Audit Report**. |

---

## 📑 Dedicated Tab & Module Guides

Each screen and operational tab has a dedicated reference document in the [`docs/`](docs/README.md) directory:

- [🚀 How to Run & Setup Guide](docs/01_HOW_TO_RUN_AND_SETUP.md) — Prerequisites, installation, test suite, and commands.
- [🌐 Tab 1: Public Landing Page & Auth](docs/02_TAB_LANDING_AND_AUTH.md) — Hero, QR simulation, and 1-click logins.
- [🎓 Tab 2: Student Dashboard](docs/03_TAB_STUDENT_DASHBOARD.md) — Sticky minimal table, SLA countdowns, and segmented filters.
- [🧠 Tab 3: Report Issue & AI Copilot](docs/04_TAB_REPORT_ISSUE_AI_COPILOT.md) — 2-column bento layout, confidence gauge, and suggested actions.
- [📍 Tab 4: Ticket Tracking & Timeline](docs/05_TAB_TRACKING_AND_TIMELINE.md) — Connected 4-stage vertical timeline and comment dialogue.
- [⚡ Tab 5: Admin Command Center (Bento)](docs/06_TAB_ADMIN_COMMAND_BENTO.md) — 12-column bento grid, spatial heatmap, and live activity stream.
- [📊 Tab 6: Campus Analytics & Audit Reporting](docs/07_TAB_ANALYTICS_AND_AUDIT.md) — Chart.js visual analytics and CSV audit download.
- [📢 Tab 7: Campus Broadcast Management](docs/08_TAB_ADMIN_BROADCASTS.md) — Push emergency advisories to student dashboards.
- [📚 Master Tab Directory](docs/README.md) — Complete documentation sitemap and index.

---

**Developed with ❤️ for Smart Campus Automation & National Hackathons.**

