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
- Flask-Login for session-based authentication
- Flask-WTF for CSRF protection (not form generation — raw HTML forms with manual validation)
- Cryptography library for encrypting OAuth tokens at rest
- No npm/node — Bootstrap 5 via CDN only
- SQLite database via `db.create_all()` — no migrations

## Authentication & Authorisation
- Flask-Login session-based auth with 3-role RBAC: **user**, **manager**, **admin**
- Ownership model: each record has a `user_id` — users see only their own data, managers/admins see all
- `@login_required` on all non-auth routes
- Role checks via `@role_required('admin')` or `@role_required('manager', 'admin')`
- First registered user auto-promoted to admin

## Architecture
- **Blueprints** (10): auth, dashboard, clients, contacts, followups, attachments, settings, users, data_io, google — each in `blueprints/<name>/`
- **Models** (18): User, Client, Contact, FollowUp, Attachment, AttachmentCategory, AttachmentTag, CustomFieldDefinition, CustomFieldValue, QuickFunction, InteractionType, AppSettings, GoogleOAuthConfig, GoogleCredential, GoogleCalendarSync, GoogleDoc, DocTemplate, GoogleDriveFile — each in `models/`
- **Templates**: `templates/<blueprint>/` + `templates/partials/`
- **Static CSS**: `static/css/custom.css`
- **Static JS**: `static/js/main.js`, `kanban.js`, `panel.js`, `reassign.js`, `settings.js`

## Google Workspace Integration
- OAuth2 flow with encrypted token storage (Fernet symmetric encryption)
- Calendar sync, Meet link generation, Docs from templates, Drive file linking
- Config stored in `GoogleOAuthConfig` model, per-user credentials in `GoogleCredential`

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

## Testing
- pytest + pytest-flask, fixtures in `conftest.py`
- 17 test modules in `tests/` covering all blueprints and models
- Run: `python -m pytest --tb=short -q`

## Don'ts
- Do NOT re-enable the Flask stat reloader (`use_reloader=True`) — it crashes background servers
- Do NOT add WTForms for form generation — use raw HTML forms with manual validation
- Do NOT add npm/node dependencies — Bootstrap via CDN only
- Do NOT use `X | None` syntax — use `Optional[X]` (Python 3.9 compat)
- Do NOT create migration files — use `db.create_all()` exclusively
