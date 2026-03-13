"""Tests for contact/interaction CRUD."""

from datetime import date

from extensions import db
from models.contact import Contact
from tests.conftest import login_as, make_client, make_contact


# ── List ────────────────────────────────────────────────────────


class TestContactList:
    def test_list_renders(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get("/contacts/")
        assert resp.status_code == 200

    def test_type_filter(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Filter Corp")
        make_contact(c, regular_user, contact_type="phone", notes="Phone call")
        make_contact(c, regular_user, contact_type="email", notes="Email sent")
        resp = client.get("/contacts/?type=phone")
        assert resp.status_code == 200

    def test_date_filter(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get(
            f"/contacts/?date_from={date.today().isoformat()}&date_to={date.today().isoformat()}"
        )
        assert resp.status_code == 200


# ── Create ──────────────────────────────────────────────────────


class TestContactCreate:
    def test_create_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Contact Corp")
        resp = client.post(
            "/contacts/new",
            data={
                "client_id": c.id,
                "date": date.today().isoformat(),
                "contact_type": "phone",
                "notes": "Spoke with client",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        ct = Contact.query.filter_by(client_id=c.id, notes="Spoke with client").first()
        assert ct is not None
        assert ct.user_id == regular_user.id

    def test_missing_client_rejected(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.post(
            "/contacts/new",
            data={"client_id": "", "date": date.today().isoformat(), "contact_type": "phone"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_ownership_verified(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_client(other_user, company_name="Other Contact Corp")
        resp = client.post(
            "/contacts/new",
            data={"client_id": c.id, "date": date.today().isoformat(), "contact_type": "phone"},
        )
        assert resp.status_code == 403


# ── Edit ────────────────────────────────────────────────────────


class TestContactEdit:
    def test_edit_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Edit Contact Corp")
        ct = make_contact(c, regular_user, notes="Original notes")
        resp = client.post(
            f"/contacts/{ct.id}/edit",
            data={
                "client_id": c.id,
                "date": date.today().isoformat(),
                "contact_type": "email",
                "notes": "Updated notes",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(ct)
        assert ct.notes == "Updated notes"
        assert ct.contact_type == "email"

    def test_access_denied_for_other_user(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_client(other_user, company_name="Foreign Contact Corp")
        ct = make_contact(c, other_user)
        resp = client.post(
            f"/contacts/{ct.id}/edit",
            data={"client_id": c.id, "date": date.today().isoformat(), "contact_type": "phone"},
        )
        assert resp.status_code == 403


# ── Delete ──────────────────────────────────────────────────────


class TestContactDelete:
    def test_delete_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Del Contact Corp")
        ct = make_contact(c, regular_user)
        ctid = ct.id
        resp = client.post(f"/contacts/{ctid}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(Contact, ctid) is None

    def test_access_denied_for_other_user(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_client(other_user, company_name="Foreign Del Corp")
        ct = make_contact(c, other_user)
        resp = client.post(f"/contacts/{ct.id}/delete")
        assert resp.status_code == 403
