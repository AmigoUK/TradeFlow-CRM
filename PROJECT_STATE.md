# NextStep CRM — Project State

**Date:** 13 March 2026
**Branch:** `feature/user-management-auth`
**Latest commit:** `acb0f95` — Add data import/export, attachment taxonomy, and full test suite (v0.25.0-beta)
**Open PR:** [#1](https://github.com/AmigoUK/NextStep-CRM/pull/1) — Google Workspace integration + user management + data I/O

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask 3.1, Python 3.9+ syntax |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (via `db.create_all()`, no migrations) |
| Frontend | Bootstrap 5 (CDN), FullCalendar.js |
| Auth | Flask-Login, bcrypt, session-based |
| CSRF | Flask-WTF CSRFProtect (global) |
| Google APIs | google-auth, google-auth-oauthlib, google-api-python-client |
| Token encryption | cryptography (Fernet, PBKDF2-derived key from SECRET_KEY) |

---

## Architecture

```
app.py                          # Application factory, context processors, schema migrations
config.py                       # Configuration (SECRET_KEY, UPLOAD_FOLDER, etc.)
extensions.py                   # db = SQLAlchemy(), csrf = CSRFProtect(), login_manager
seed.py                         # Sample data — 4 users, 15 clients, 104 contacts, 95 follow-ups

blueprints/
    auth/                       # Login, logout, rate limiting
        routes.py, decorators.py (role_required, can_access_record)
    dashboard/                  # Dashboard, calendar, agenda, API endpoints (/api/events, /api/quarterly)
    clients/                    # CRUD, detail view, quick actions, reassignment
    contacts/                   # Interactions CRUD with Google Calendar sync hooks
    followups/                  # Follow-ups CRUD with Calendar sync + Meet link hooks
    attachments/                # File upload/download/edit/delete (local + Google Drive)
    settings/                   # Admin: quick functions, interaction types, themes, Google config
    users/                      # User management (manager+): create, edit, toggle, delegate
    data_io/                    # CSV import/export for clients, contacts, follow-ups (admin-only)
    google/                     # Google Workspace integration
        routes.py               # OAuth2: connect, callback, disconnect, status, admin config
        google_service.py       # Token encryption, credential building, auto-refresh
        calendar_routes.py      # Sync follow-ups/contacts to Google Calendar
        calendar_service.py     # Calendar API logic
        meet_routes.py          # Google Meet link generation via Calendar API conferenceData
        docs_routes.py          # Google Docs create/link/unlink + template management
        docs_service.py         # Docs API logic
        drive_routes.py         # Google Drive upload/browse/link/share
        drive_service.py        # Drive API logic

models/
    client.py                   # Client (company_name, industry, phone, email, status, user_id)
    contact.py                  # Contact/Interaction (client_id, date, time, contact_type, meet_link)
    followup.py                 # FollowUp (client_id, due_date, priority, completed, meet_link)
    attachment.py               # Attachment (filename, storage_type: local|drive, category, tags)
    attachment_category.py      # AttachmentCategory (label, icon, colour)
    attachment_tag.py           # AttachmentTag (label, colour)
    user.py                     # User (username, password_hash, role: user|manager|admin)
    app_settings.py             # AppSettings singleton (theme, preferences)
    custom_field.py             # CustomFieldDefinition + CustomFieldValue
    interaction_type.py         # InteractionType (label, icon, colour)
    quick_function.py           # QuickFunction (one-click interaction shortcuts)
    google_oauth_config.py      # GoogleOAuthConfig singleton (client_id, secret, scopes, enabled)
    google_credential.py        # GoogleCredential per-user (encrypted tokens, expiry, scopes)
    google_calendar_sync.py     # GoogleCalendarSync (links CRM records to Calendar events)
    google_doc.py               # GoogleDoc (links Google Docs to clients/contacts/follow-ups)
    doc_template.py             # DocTemplate (admin-configured document templates)
    google_drive_file.py        # GoogleDriveFile (links Drive files to CRM records)

templates/
    base.html                   # Layout with navbar, flash messages, modals
    auth/login.html
    dashboard/ (index, calendar, agenda)
    clients/ (list, detail, create, edit)
    contacts/ (list, create, edit)
    followups/ (list, create, edit, matrix)
    settings/ (index, data_import)
    users/ (list, create, edit)
    partials/ (_navbar, _upload_form, _attachment_list, _drive_browser_modal, etc.)

static/
    css/custom.css
    js/main.js

tests/                          # 253 tests across 17 test files
```

---

## Features Implemented

### Core CRM
- **Client management** — CRUD, status lifecycle (lead → prospect → active → inactive), industry, contact person
- **Interactions** — Phone, email, meeting logging with date/time, notes, outcome
- **Follow-ups** — Priority (high/medium/low), due date/time, completion toggle, overdue detection (`is_overdue` hybrid property)
- **Activity timeline** — Merged chronological view on client detail page
- **Dashboard** — Stats cards, overdue alerts, recent activity
- **Calendar** — FullCalendar.js with follow-ups and contacts as events
- **Agenda** — List view of upcoming follow-ups
- **Eisenhower matrix** — Priority/urgency grid for follow-ups

### User Management & RBAC
- **3-role system** — user (own records), manager (all records), admin (settings + users)
- **Ownership filtering** — Users see only their own clients/contacts/follow-ups
- **Record access control** — `can_access_record()` decorator enforces ownership
- **Reassignment** — Managers can reassign clients (with cascade option) to other users
- **Bulk reassignment** — Reassign multiple clients at once
- **User CRUD** — Create, edit, toggle active/inactive, reset password, delegate records

### Authentication
- Session-based login with Flask-Login
- bcrypt password hashing
- Remember me functionality
- IP-based rate limiting (5 attempts / 30 seconds)

### Attachments
- File upload to local storage (per-client directories)
- Google Drive upload path (when connected)
- Categories and tags for organisation
- Preview modal for images and PDFs
- Download and inline view

### Data Import/Export (Admin)
- CSV export for clients, contacts, follow-ups
- CSV import with validation, error reporting, downloadable error CSV
- Template download for each entity type

### Customisation (Admin)
- Custom client fields (text, URL types with icons)
- Configurable interaction types (label, icon, colour)
- Quick functions (one-click interaction shortcuts)
- Theme and UI preferences

### Google Workspace Integration
- **Phase 0 — OAuth2 Foundation**: Admin configures Client ID/Secret in Settings, per-user OAuth2 connect/disconnect, Fernet-encrypted tokens at rest, `@google_required` decorator, graceful degradation
- **Phase 1 — Google Calendar**: Bidirectional sync (outbound push, inbound pull), FullCalendar event source (#4285F4 blue), sync hooks on follow-up/contact CRUD
- **Phase 2 — Google Meet**: Link generation via Calendar API `conferenceData`, "Join Meeting" buttons in timeline and agenda
- **Phase 3 — Google Docs**: Create blank or from template, link/unlink to clients, admin template management in Settings
- **Phase 4 — Google Drive**: Upload to Drive, browse/link existing files, `storage_type` on attachments, Drive browser modal, cloud icon indicators

---

## Database (Sample Data)

| Entity | Count | Notes |
|--------|-------|-------|
| Users | 4 | admin, manager1 (Sarah), user1 (James), user2 (Emily) |
| Clients | 15 | 6 active, 3 prospect, 4 lead, 2 inactive |
| Contacts | 104 | Full year Apr 2025 – Mar 2026, all 15 clients |
| Follow-ups | 95 | 68 completed, 27 pending (incl. future pipeline to Dec 2026) |
| Custom field values | 11 | Addresses, LinkedIn, Twitter/X |
| Attachment categories | 4 | Default categories |
| Attachment tags | 3 | Default tags |

Default credentials: `admin` / `admin123`, `manager1` / `manager123`, `user1` / `user123`, `user2` / `user123`

---

## Test Suite

**253 tests** across 17 files (3,040 lines):

| File | Tests | Covers |
|------|-------|--------|
| `test_auth.py` | 10 | Login, logout, rate limiting |
| `test_rbac.py` | 14 | Role gates, ownership, reassignment |
| `test_clients.py` | 11 | CRUD, status, delete cascade, quick action |
| `test_contacts.py` | 7 | CRUD, ownership, access control |
| `test_followups.py` | 10 | CRUD, complete toggle, AJAX, matrix |
| `test_dashboard.py` | 9 | Dashboard, calendar API, quarterly API |
| `test_users.py` | 9 | User CRUD, role escalation, toggle, delegate |
| `test_settings.py` | 9 | Settings access, quick functions, interaction types, theme |
| `test_attachments.py` | 8 | Upload, download, edit, delete, access control |
| `test_data_io.py` | 21 | Export, import, templates, error reports |
| `test_models.py` | 19 | User, Client, FollowUp, Attachment, AppSettings models |
| `test_helpers.py` | 12 | Template filters (tel_link, mailto_link, relative_date) |
| `test_google_oauth.py` | 19 | Admin config, OAuth flow, token encryption, graceful degradation |
| `test_google_calendar.py` | 12 | Sync model, routes, form checkbox, sync hooks |
| `test_google_meet.py` | 10 | meet_link columns, routes, UI elements |
| `test_google_docs.py` | 13 | Models, routes, admin templates, UI |
| `test_google_drive.py` | 11 | Model, storage_type, routes, UI, existing upload |

---

## Git History (recent)

```
acb0f95 Add data import/export, attachment taxonomy, and full test suite (v0.25.0-beta)
c0d528d Add Google Workspace integration — Calendar, Meet, Docs, and Drive (v0.24.0-beta)
86e77d3 Add 3-role user management with authentication and authorisation (v0.23.0-beta)
a677b32 Add screenshots for README (26 images)
4c7de02 Rebuild README with screenshots, navigation, and acknowledgements (v0.16.0-beta)
ad189c1 Fix garbled phone number in seed data
3f5f921 Add file attachments on clients, contacts, and follow-ups (v0.15.0-beta)
f47cae5 Add custom client fields with Settings CRUD (v0.14.0-beta)
e457b11 Add configurable interaction types with Settings CRUD (v0.13.0-beta)
b0a8b05 Add clickable tel: and mailto: links (v0.12.0-beta)
```

---

## Uncommitted Changes

| File | Change |
|------|--------|
| `seed.py` | Expanded sample data to cover full year (Apr 2025 – Mar 2026) |
| `templates/settings/index.html` | Added Google Cloud Console setup instructions with links |

---

## Running the App

```bash
# Install dependencies
pip install -r requirements.txt

# Seed the database
python seed.py

# Run the development server
python app.py
# → http://127.0.0.1:5001

# Run tests
pytest tests/ -v
```

---

## Key Design Decisions

- **No migrations** — SQLite with `db.create_all()` + ALTER TABLE blocks in `app.py` for schema evolution
- **No WTForms** — Raw HTML forms with manual validation
- **No npm/node** — Bootstrap 5 via CDN only
- **British English** — colour, organisation, behaviour, etc.
- **Graceful degradation** — All Google UI gated behind `{% if google_connected %}`; CRM works identically without Google
- **Token security** — Fernet encryption at rest, OAuth state CSRF, `drive.file` minimal scope
- **Ownership model** — Every record has `user_id`; users see own, managers see all, admins configure
