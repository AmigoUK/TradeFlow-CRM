"""Tests for Google Calendar integration (Phase 1)."""

from unittest.mock import patch, MagicMock
from datetime import date

from models.google_calendar_sync import GoogleCalendarSync
from extensions import db
from tests.conftest import login_as, make_client, make_followup, make_contact


class TestCalendarSyncModel:
    """GoogleCalendarSync model basics."""

    def test_create_sync_record(self, app, admin_user):
        client_obj = make_client(admin_user)
        fu = make_followup(client_obj, admin_user)
        sync = GoogleCalendarSync(
            user_id=admin_user.id,
            followup_id=fu.id,
            google_event_id="test-event-123",
            google_calendar_id="primary",
            sync_direction="outbound",
        )
        db.session.add(sync)
        db.session.commit()
        assert sync.id is not None
        assert sync.followup.id == fu.id

    def test_followup_has_calendar_sync_backref(self, app, admin_user):
        client_obj = make_client(admin_user)
        fu = make_followup(client_obj, admin_user)
        assert fu.calendar_sync is None

        sync = GoogleCalendarSync(
            user_id=admin_user.id,
            followup_id=fu.id,
            google_event_id="event-456",
            google_calendar_id="primary",
        )
        db.session.add(sync)
        db.session.commit()
        assert fu.calendar_sync is not None
        assert fu.calendar_sync.google_event_id == "event-456"


class TestCalendarRoutes:
    """Calendar sync routes require google connection."""

    def test_sync_followup_requires_login(self, client):
        resp = client.post("/google/calendar/sync-followup/1")
        assert resp.status_code in (302, 401)

    def test_google_calendar_events_when_not_connected(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/google/calendar/events", follow_redirects=True)
        assert resp.status_code == 200

    def test_pull_events_when_not_connected(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post("/google/calendar/pull", follow_redirects=True)
        assert resp.status_code == 200


class TestCalendarFormCheckbox:
    """Follow-up form shows sync checkbox when connected."""

    def test_followup_form_no_checkbox_when_disconnected(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/followups/new")
        assert resp.status_code == 200
        assert b"Sync to Google Calendar" not in resp.data

    def test_contact_form_no_checkbox_when_disconnected(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/contacts/new")
        assert resp.status_code == 200
        assert b"Sync to Google Calendar" not in resp.data


class TestCalendarSyncHooks:
    """CRUD operations on follow-ups/contacts still work with sync hooks."""

    def test_create_followup_works(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        resp = client.post("/followups/new", data={
            "client_id": c.id,
            "due_date": date.today().isoformat(),
            "priority": "medium",
            "notes": "Test with sync hooks",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_create_contact_works(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        resp = client.post("/contacts/new", data={
            "client_id": c.id,
            "date": date.today().isoformat(),
            "contact_type": "phone",
            "notes": "Test with sync hooks",
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_delete_followup_works(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        fu = make_followup(c, admin_user)
        resp = client.post(f"/followups/{fu.id}/delete", follow_redirects=True)
        assert resp.status_code == 200

    def test_delete_contact_works(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        contact = make_contact(c, admin_user)
        resp = client.post(f"/contacts/{contact.id}/delete", follow_redirects=True)
        assert resp.status_code == 200

    def test_calendar_view_still_loads(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/calendar")
        assert resp.status_code == 200
        assert b"Google Calendar" not in resp.data  # Not shown when disconnected
