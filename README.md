# NextStep CRM

A lightweight, single-user CRM web application built with Flask and Bootstrap 5. Manage clients, log interactions, schedule follow-ups, and stay on top of your pipeline — all from one place.

**Current version:** v0.11.0-beta

## Features

### Core
- **Client Management** — Full CRUD with status tracking (lead, prospect, active, inactive), search, and filtering
- **Interaction History** — Log phone calls, emails, and meetings against each client with timestamps and outcomes
- **Follow-up Scheduling** — Set due dates, times, and priorities; mark tasks complete; highlight overdue items automatically
- **Cascade Delete** — Removing a client cleanly deletes all associated contacts and follow-ups

### Views & Dashboards
- **Dashboard** — At-a-glance stats, today's tasks, overdue follow-ups, and recent interactions
- **Calendar** — Interactive monthly/weekly calendar powered by FullCalendar.js with colour-coded events
- **Agenda** — Daily planner view with grouped tasks and overdue highlights
- **Quarterly Overview** — Q1–Q4 strategic calendar with activity density and per-client breakdowns
- **Eisenhower Matrix** — Four-quadrant priority matrix for follow-ups (Do First / Schedule / Delegate / Eliminate)
- **Kanban Board** — Drag-and-drop pipeline board with columns per client status
- **Client Profile** — 360-degree two-column layout with sidebar stats and activity timeline

### Productivity
- **Quick Functions** — One-click client interaction logging (catalogue sent, price list sent, follow-up call, etc.) — fully configurable from Settings
- **Quick Add Panel** — Slide-over form panels with AJAX submit for creating clients, contacts, and follow-ups from any page
- **Completion-to-Outcome Flow** — Completing a follow-up prompts an optional interaction log with pre-filled context

### Settings & Customisation
- **Configurable Quick Functions** — Add, edit, activate/deactivate, and delete quick functions from the Settings page
- **Colour Scheme** — Light, Dark, and System (follows OS preference) themes with instant switching and persistence

### UX
- **Toast Notifications** — Non-blocking success/error feedback throughout
- **Mobile Responsive** — Stacked card layout for tables on small screens, full-width offcanvas panels
- **AJAX Everywhere** — Status updates, quick functions, toggles, and theme switching without page reloads

## Screenshots

| Dashboard | Client Profile | Calendar |
|-----------|---------------|----------|
| ![Dashboard](screenshots/Dashboard.png) | ![Client](screenshots/client-dashboard.png) | ![Calendar](screenshots/calendar-month.png) |

| Agenda | Interactions | Kanban Board |
|--------|-------------|--------------|
| ![Agenda](screenshots/agenda.png) | ![Interactions](screenshots/interactions.png) | ![Log Interaction](screenshots/log-interaction.png) |

## Tech Stack

- **Backend:** Python 3.9+, Flask 3.1, Flask-SQLAlchemy 3.1, SQLAlchemy 2.0
- **Database:** SQLite (auto-created via `db.create_all()`, no migrations)
- **Frontend:** Jinja2 templates, Bootstrap 5.3.3 (CDN), Bootstrap Icons 1.11.3
- **Calendar:** FullCalendar.js (CDN)
- **No authentication** — single-user portfolio project
- **No npm/node** — all frontend dependencies via CDN

## Installation

```bash
# Clone the repository
git clone https://github.com/AmigoUK/NextStep-CRM.git
cd NextStep-CRM

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 app.py
```

The app will be available at `http://localhost:5001`.

### Sample Data

To populate the database with 10 clients, 15 contacts, and 12 follow-ups:

```bash
python3 seed.py
```

## Project Structure

```
NextStep-CRM/
├── app.py                 # Application factory + entry point
├── config.py              # Configuration (SECRET_KEY, DATABASE_URL)
├── extensions.py          # SQLAlchemy singleton
├── seed.py                # Sample data seeder
├── requirements.txt
├── models/
│   ├── __init__.py        # Model exports
│   ├── client.py          # Client model + CLIENT_STATUSES
│   ├── contact.py         # Contact model + CONTACT_TYPES
│   ├── followup.py        # FollowUp model + PRIORITIES
│   ├── quick_function.py  # QuickFunction model + DEFAULT_QUICK_FUNCTIONS
│   └── app_settings.py    # AppSettings singleton (theme preferences)
├── blueprints/
│   ├── dashboard/         # Dashboard, calendar, agenda, quarterly
│   ├── clients/           # Client CRUD, kanban, quick actions
│   ├── contacts/          # Contact CRUD + filters
│   ├── followups/         # FollowUp CRUD, matrix, completion flow
│   └── settings/          # Settings page, quick function CRUD, theme
├── templates/
│   ├── base.html          # Bootstrap 5 layout with dark mode support
│   ├── partials/          # Navbar, flash messages, modals
│   ├── dashboard/         # Dashboard, calendar, agenda, quarterly views
│   ├── clients/           # Client list, detail, form templates
│   ├── contacts/          # Contact list, form templates
│   ├── followups/         # Follow-up list, form, matrix templates
│   └── settings/          # Settings page template
└── static/
    ├── css/custom.css     # Custom styles + dark mode overrides
    └── js/
        ├── main.js        # Delete modal, quick functions, toasts
        ├── panel.js       # Slide-over form panel
        ├── kanban.js      # Drag-and-drop board
        └── settings.js    # Theme switcher + toggle handlers
```

## Version History

| Version | Description |
|---------|-------------|
| v0.11.0-beta | Colour scheme with dark mode (Light / Dark / System) |
| v0.10.0-beta | Settings page + DB-backed configurable quick functions |
| v0.9.0-beta | Eisenhower Matrix for follow-up prioritisation |
| v0.8.0-beta | Quarterly Overview with Q1–Q4 strategic calendar |
| v0.7.0-beta | Quick Functions for one-click interaction logging |
| v0.6.0-beta | Slide-over form panels with AJAX submit |
| v0.5.0-beta | Completion-to-outcome flow with modal |
| v0.4.0-beta | Kanban pipeline board with drag-and-drop |
| v0.3.0-beta | 360-degree client profile with two-column layout |
| v0.2.0-beta | Calendar time context for timed events |
| v0.1.0-beta | Rebrand to NextStep CRM with version system |

## Licence

MIT
