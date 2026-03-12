# NextStep CRM

A lightweight CRM (Customer Relationship Management) web application built with Flask and Bootstrap 5. Manage clients, log interaction history, schedule follow-ups, and track overdue tasks from a single dashboard.

## Features

- **Client Management** — Create, edit, and organise clients with status tracking (lead, prospect, active, inactive)
- **Interaction History** — Log phone calls, emails, and meetings against each client
- **Follow-up Scheduling** — Set due dates and priorities, mark tasks complete, highlight overdue items
- **Dashboard** — At-a-glance stats, today's tasks, overdue follow-ups, and recent interactions
- **Search & Filters** — Filter clients by status, contacts by type/date, follow-ups by priority/completion

## Tech Stack

- Python 3.9+, Flask 3.1, Flask-SQLAlchemy 3.0
- SQLite database (no migrations needed)
- Jinja2 templates + Bootstrap 5 (CDN)
- No authentication required — single-user portfolio project

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

The app will be available at `http://localhost:5000`.

### Sample Data

To populate the database with sample data:

```bash
python3 seed.py
```

## Project Structure

```
NextStep-CRM/
├── .gitignore
├── README.md
├── requirements.txt
├── config.py              # Configuration
├── extensions.py          # SQLAlchemy singleton
├── app.py                 # Application factory + entry point
├── seed.py                # Sample data seeder
├── models/
│   ├── __init__.py
│   ├── client.py          # Client model
│   ├── contact.py         # Contact (interaction) model
│   └── followup.py        # FollowUp model
├── blueprints/
│   ├── dashboard/         # Dashboard stats and overview
│   ├── clients/           # Client CRUD + search
│   ├── contacts/          # Contact CRUD + filters
│   └── followups/         # FollowUp CRUD + overdue tracking
├── templates/
│   ├── base.html          # Bootstrap 5 layout
│   ├── partials/          # Navbar, flash messages, modals
│   ├── dashboard/
│   ├── clients/
│   ├── contacts/
│   └── followups/
└── static/
    ├── css/custom.css
    └── js/main.js
```

## Licence

MIT
