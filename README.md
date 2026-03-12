# 📋 NextStep CRM

**A lightweight, single-user CRM for managing clients, interactions, and follow-ups — built with Flask and Bootstrap 5.**

![Version](https://img.shields.io/badge/version-v0.16.0--beta-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-green)
![Flask](https://img.shields.io/badge/flask-3.1-lightgrey)
![Licence](https://img.shields.io/badge/licence-MIT-orange)

NextStep CRM is a portfolio project that demonstrates a full-featured mini CRM built without any JavaScript frameworks or build tools. It covers client management, interaction logging, follow-up scheduling, an Eisenhower Matrix, a Kanban board, file attachments, and more — all in a responsive, dark-mode-capable interface.

---

## Table of Contents

- [Screenshots](#screenshots)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Acknowledgements](#acknowledgements)
- [Version History](#version-history)
- [Licence](#licence)

---

## Screenshots

### Dashboard & Views

<a href="screenshots/Dashboard.png"><img src="screenshots/Dashboard.png" width="280"></a>
<a href="screenshots/Dashboard-Dark-Mode.png"><img src="screenshots/Dashboard-Dark-Mode.png" width="280"></a>
<a href="screenshots/calendar-month.png"><img src="screenshots/calendar-month.png" width="280"></a>
<a href="screenshots/calendar-week.png"><img src="screenshots/calendar-week.png" width="280"></a>
<a href="screenshots/agenda.png"><img src="screenshots/agenda.png" width="280"></a>
<a href="screenshots/quartely-overview.png"><img src="screenshots/quartely-overview.png" width="280"></a>

### Client Management

<a href="screenshots/client-dashboard.png"><img src="screenshots/client-dashboard.png" width="280"></a>
<a href="screenshots/client-dashboard2-add-quick-action.png"><img src="screenshots/client-dashboard2-add-quick-action.png" width="280"></a>
<a href="screenshots/add-client.png"><img src="screenshots/add-client.png" width="280"></a>
<a href="screenshots/interactions.png"><img src="screenshots/interactions.png" width="280"></a>
<a href="screenshots/log-interaction.png"><img src="screenshots/log-interaction.png" width="280"></a>

### Follow-ups & Productivity

<a href="screenshots/follow-ups-list-view.png"><img src="screenshots/follow-ups-list-view.png" width="280"></a>
<a href="screenshots/Follow-ups-Eisenhower-Matrix-View.png"><img src="screenshots/Follow-ups-Eisenhower-Matrix-View.png" width="280"></a>
<a href="screenshots/add-followup.png"><img src="screenshots/add-followup.png" width="280"></a>
<a href="screenshots/quick-functions.png"><img src="screenshots/quick-functions.png" width="280"></a>

### Attachments & Settings

<a href="screenshots/attachment-upload.png"><img src="screenshots/attachment-upload.png" width="280"></a>
<a href="screenshots/document-preview.png"><img src="screenshots/document-preview.png" width="280"></a>
<a href="screenshots/settings.png"><img src="screenshots/settings.png" width="280"></a>

### Mobile Responsive

<a href="screenshots/Dashboard-Dark-Mode-mobile.png"><img src="screenshots/Dashboard-Dark-Mode-mobile.png" width="140"></a>
<a href="screenshots/agenda-mobile.png"><img src="screenshots/agenda-mobile.png" width="140"></a>
<a href="screenshots/calendar-list-mobile.png"><img src="screenshots/calendar-list-mobile.png" width="140"></a>
<a href="screenshots/quartely-overview-mobile.png"><img src="screenshots/quartely-overview-mobile.png" width="140"></a>
<a href="screenshots/client-dv-mobile1.png"><img src="screenshots/client-dv-mobile1.png" width="140"></a>
<a href="screenshots/client-dv-mobile2.png"><img src="screenshots/client-dv-mobile2.png" width="140"></a>
<a href="screenshots/client-dashboard2-add-quick-action-mobile.png"><img src="screenshots/client-dashboard2-add-quick-action-mobile.png" width="140"></a>
<a href="screenshots/log-interaction-mobile.png"><img src="screenshots/log-interaction-mobile.png" width="140"></a>

---

## Features

### Core
- **Client Management** — Full CRUD with status tracking (lead, prospect, active, inactive), search, and filtering
- **Interaction Logging** — Log phone calls, emails, meetings, and custom interaction types against each client
- **Follow-up Scheduling** — Set due dates, times, and priorities; mark tasks complete; highlight overdue items automatically
- **Cascade Delete** — Removing a client cleanly deletes all associated contacts, follow-ups, and attachments
- **Custom Fields** — Define additional client fields from Settings to capture data specific to your workflow
- **File Attachments** — Upload and manage documents on clients, contacts, and follow-ups with categories, tags, and in-browser preview

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
- **Interaction Types** — Add, edit, and delete interaction types from Settings
- **Custom Client Fields** — Define extra fields (text, number, date, dropdown) that appear on the client form
- **Attachment Categories & Tags** — Organise uploaded files with configurable categories and tags
- **UI Preferences** — Sticky navbar, configurable pagination (10/25/50/100 per page), back-to-top button
- **Colour Scheme** — Light, Dark, and System (follows OS preference) themes with instant switching and persistence

### UX
- **Toast Notifications** — Non-blocking success/error feedback throughout
- **Mobile Responsive** — Stacked card layout for tables on small screens, full-width offcanvas panels
- **AJAX Everywhere** — Status updates, quick functions, toggles, and theme switching without page reloads
- **Clickable Links** — Phone numbers and email addresses rendered as `tel:` and `mailto:` links
- **Pagination** — Configurable page sizes across all list views

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.9+, Flask 3.1, Flask-SQLAlchemy 3.1, SQLAlchemy 2.0 |
| Database | SQLite (auto-created, no migrations) |
| Frontend | Jinja2, Bootstrap 5.3.3 (CDN), Bootstrap Icons 1.11.3 |
| Calendar | FullCalendar.js (CDN) |
| Drag & Drop | SortableJS (CDN) |
| Auth | None — single-user portfolio project |
| Build Tools | None — no npm/node, all CDN |

---

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

To populate the database with 15 clients, 30+ contacts, and 40+ follow-ups:

```bash
python3 seed.py
```

---

## Project Structure

```
NextStep-CRM/
├── app.py                      # Application factory + entry point
├── config.py                   # Configuration (SECRET_KEY, DATABASE_URL)
├── extensions.py               # SQLAlchemy singleton
├── seed.py                     # Sample data seeder
├── requirements.txt
├── models/
│   ├── __init__.py             # Model exports
│   ├── client.py               # Client model + CLIENT_STATUSES
│   ├── contact.py              # Contact model + CONTACT_TYPES
│   ├── followup.py             # FollowUp model + PRIORITIES
│   ├── quick_function.py       # QuickFunction model + defaults
│   ├── interaction_type.py     # InteractionType model
│   ├── custom_field.py         # CustomField model
│   ├── attachment.py           # Attachment model
│   ├── attachment_category.py  # AttachmentCategory model
│   ├── attachment_tag.py       # AttachmentTag model
│   └── app_settings.py         # AppSettings singleton (theme, UI prefs)
├── blueprints/
│   ├── dashboard/              # Dashboard, calendar, agenda, quarterly
│   ├── clients/                # Client CRUD, kanban, quick actions
│   ├── contacts/               # Contact CRUD + filters
│   ├── followups/              # FollowUp CRUD, matrix, completion flow
│   ├── attachments/            # File upload, download, preview, delete
│   └── settings/               # Settings page, interaction types, custom fields, UI prefs
├── templates/
│   ├── base.html               # Bootstrap 5 layout with dark mode support
│   ├── partials/               # Navbar, flash messages, modals, pagination
│   ├── dashboard/              # Dashboard, calendar, agenda, quarterly views
│   ├── clients/                # Client list, detail, form templates
│   ├── contacts/               # Contact list, form templates
│   ├── followups/              # Follow-up list, form, matrix templates
│   └── settings/               # Settings page template
└── static/
    ├── css/custom.css          # Custom styles + dark mode overrides
    └── js/
        ├── main.js             # Delete modal, quick functions, toasts, pagination
        ├── panel.js            # Slide-over form panel
        ├── kanban.js           # Drag-and-drop board
        └── settings.js         # Theme switcher + settings handlers
```

---

## Acknowledgements

> Thank you to **Miłosz Ławrynowicz** for my first copy of *The 7 Habits of Highly Effective People* by Stephen Covey. The Eisenhower Matrix feature in this project exists because of you!

---

## Version History

| Version | Description |
|---------|-------------|
| v0.16.0-beta | Attachment categories, tags, document preview, pagination, and UI preferences |
| v0.15.0-beta | File attachments on clients, contacts, and follow-ups |
| v0.14.0-beta | Custom client fields with Settings CRUD |
| v0.13.0-beta | Configurable interaction types with Settings CRUD |
| v0.12.0-beta | Clickable `tel:` and `mailto:` links |
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

---

## Licence

MIT
