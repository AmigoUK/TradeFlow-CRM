"""Tests for Contact (person) CRUD."""

from extensions import db
from models.contact import Contact
from tests.conftest import login_as, make_company


# ── List ────────────────────────────────────────────────────────


class TestContactList:
    def test_list_renders(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get("/contacts/")
        assert resp.status_code == 200


# ── Create ──────────────────────────────────────────────────────


class TestContactCreate:
    def test_create_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Contact Person Corp")
        resp = client.post(
            "/contacts/new",
            data={
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane@example.com",
                "company_id": c.id,
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        ct = Contact.query.filter_by(first_name="Jane", last_name="Doe").first()
        assert ct is not None

    def test_missing_first_name_rejected(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.post(
            "/contacts/new",
            data={"first_name": "", "last_name": "Doe"},
            follow_redirects=True,
        )
        assert resp.status_code == 200


# ── Detail ──────────────────────────────────────────────────────


class TestContactDetail:
    def test_shows_contact_info(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Detail Contact Corp")
        ct = Contact(
            first_name="John",
            last_name="Smith",
            company_id=c.id,
            user_id=regular_user.id,
        )
        db.session.add(ct)
        db.session.commit()
        resp = client.get(f"/contacts/{ct.id}")
        assert resp.status_code == 200


# ── Edit ────────────────────────────────────────────────────────


class TestContactEdit:
    def test_edit_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Edit Contact Corp")
        ct = Contact(
            first_name="Original",
            last_name="Name",
            company_id=c.id,
            user_id=regular_user.id,
        )
        db.session.add(ct)
        db.session.commit()
        resp = client.post(
            f"/contacts/{ct.id}/edit",
            data={
                "first_name": "Updated",
                "last_name": "Name",
                "company_id": c.id,
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(ct)
        assert ct.first_name == "Updated"


# ── Delete ──────────────────────────────────────────────────────


class TestContactDelete:
    def test_delete_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Del Contact Corp")
        ct = Contact(
            first_name="Delete",
            last_name="Me",
            company_id=c.id,
            user_id=regular_user.id,
        )
        db.session.add(ct)
        db.session.commit()
        ctid = ct.id
        resp = client.post(f"/contacts/{ctid}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(Contact, ctid) is None
