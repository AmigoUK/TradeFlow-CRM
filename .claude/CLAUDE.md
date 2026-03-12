# NextStep CRM — Project Instructions

## Overview
Mini CRM web application — Flask 3.1 + SQLAlchemy 2.0 + Bootstrap 5 + SQLite.
Portfolio project for junior developer showcase.

## Language
- **British English throughout** — colour, organisation, honour, behaviour, centre, licence, favourite, categorise

## Stack Rules
- Python 3.9 syntax: use `Optional[X]` not `X | None`
- Flask application factory pattern in `app.py`
- `extensions.py` holds `db = SQLAlchemy()` singleton (avoids circular imports)
- No WTForms — raw HTML forms with manual validation
- No authentication
- No npm/node — Bootstrap 5 via CDN only
- SQLite database via `db.create_all()` — no migrations

## Architecture
- **Blueprints**: dashboard, clients, contacts, followups — each in `blueprints/<name>/`
- **Models**: in `models/` — Client, Contact, FollowUp
- **Templates**: `templates/<blueprint>/` + `templates/partials/`
- **Static**: `static/css/custom.css`, `static/js/main.js`

## Git Workflow
- Branch: `main` only
- Commit after each major feature
- Push immediately after each commit
- Repo: `AmigoUK/NextStep-CRM`

## Key Patterns
- Constants (statuses, types, priorities) live alongside their model
- Cascade delete: removing a client deletes its contacts and follow-ups
- `is_overdue` is a hybrid property on FollowUp
- Flash messages use Bootstrap alert categories: success, danger, warning, info
