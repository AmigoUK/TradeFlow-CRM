"""Tests for Google Meet integration (Phase 2)."""

from datetime import date

from models import FollowUp, Contact
from extensions import db
from tests.conftest import login_as, make_client, make_followup, make_contact


class TestMeetLinkColumn:
    """meet_link column exists on FollowUp and Contact."""

    def test_followup_meet_link_default_none(self, app, admin_user):
        c = make_client(admin_user)
        fu = make_followup(c, admin_user)
        assert fu.meet_link is None

    def test_followup_meet_link_can_be_set(self, app, admin_user):
        c = make_client(admin_user)
        fu = make_followup(c, admin_user)
        fu.meet_link = "https://meet.google.com/abc-defg-hij"
        db.session.commit()
        fu2 = db.session.get(FollowUp, fu.id)
        assert fu2.meet_link == "https://meet.google.com/abc-defg-hij"

    def test_contact_meet_link_default_none(self, app, admin_user):
        c = make_client(admin_user)
        contact = make_contact(c, admin_user)
        assert contact.meet_link is None

    def test_contact_meet_link_can_be_set(self, app, admin_user):
        c = make_client(admin_user)
        contact = make_contact(c, admin_user)
        contact.meet_link = "https://meet.google.com/xyz-uvwx-rst"
        db.session.commit()
        c2 = db.session.get(Contact, contact.id)
        assert c2.meet_link == "https://meet.google.com/xyz-uvwx-rst"


class TestMeetRoutes:
    """Meet routes require authentication and Google connection."""

    def test_create_meet_for_followup_requires_login(self, client):
        resp = client.post("/google/meet/create-for-followup/1")
        assert resp.status_code in (302, 401)

    def test_create_meet_for_contact_requires_login(self, client):
        resp = client.post("/google/meet/create-for-contact/1")
        assert resp.status_code in (302, 401)

    def test_create_meet_when_not_connected(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        fu = make_followup(c, admin_user)
        resp = client.post(f"/google/meet/create-for-followup/{fu.id}", follow_redirects=True)
        assert resp.status_code == 200


class TestMeetUI:
    """Meet link UI elements appear correctly."""

    def test_followup_form_no_meet_checkbox_when_disconnected(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/followups/new")
        assert b"Create Google Meet link" not in resp.data

    def test_agenda_loads_with_meet_link(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        fu = make_followup(c, admin_user)
        fu.meet_link = "https://meet.google.com/abc-defg-hij"
        db.session.commit()
        resp = client.get("/agenda")
        assert resp.status_code == 200
        assert b"meet.google.com" in resp.data

    def test_agenda_no_meet_button_without_link(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        make_followup(c, admin_user)
        resp = client.get("/agenda")
        assert resp.status_code == 200
        assert b"Join" not in resp.data or b"Join Meeting" not in resp.data
