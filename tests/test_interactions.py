"""Tests for interaction CRUD."""

from datetime import date

from extensions import db
from models.interaction import Interaction
from tests.conftest import login_as, make_company, make_interaction


# ── List ────────────────────────────────────────────────────────


class TestInteractionList:
    def test_list_renders(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get("/interactions/")
        assert resp.status_code == 200

    def test_type_filter(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Filter Corp")
        make_interaction(c, regular_user, interaction_type="phone", notes="Phone call")
        make_interaction(c, regular_user, interaction_type="email", notes="Email sent")
        resp = client.get("/interactions/?type=phone")
        assert resp.status_code == 200

    def test_date_filter(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get(
            f"/interactions/?date_from={date.today().isoformat()}&date_to={date.today().isoformat()}"
        )
        assert resp.status_code == 200


# ── Create ──────────────────────────────────────────────────────


class TestInteractionCreate:
    def test_create_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Interaction Corp")
        resp = client.post(
            "/interactions/new",
            data={
                "company_id": c.id,
                "date": date.today().isoformat(),
                "interaction_type": "phone",
                "notes": "Spoke with company",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        ix = Interaction.query.filter_by(company_id=c.id, notes="Spoke with company").first()
        assert ix is not None
        assert ix.user_id == regular_user.id

    def test_missing_company_rejected(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.post(
            "/interactions/new",
            data={"company_id": "", "date": date.today().isoformat(), "interaction_type": "phone"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_ownership_verified(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_company(other_user, company_name="Other Interaction Corp")
        resp = client.post(
            "/interactions/new",
            data={"company_id": c.id, "date": date.today().isoformat(), "interaction_type": "phone"},
        )
        assert resp.status_code == 403


# ── Edit ────────────────────────────────────────────────────────


class TestInteractionEdit:
    def test_edit_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Edit Interaction Corp")
        ix = make_interaction(c, regular_user, notes="Original notes")
        resp = client.post(
            f"/interactions/{ix.id}/edit",
            data={
                "company_id": c.id,
                "date": date.today().isoformat(),
                "interaction_type": "email",
                "notes": "Updated notes",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(ix)
        assert ix.notes == "Updated notes"
        assert ix.interaction_type == "email"

    def test_access_denied_for_other_user(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_company(other_user, company_name="Foreign Interaction Corp")
        ix = make_interaction(c, other_user)
        resp = client.post(
            f"/interactions/{ix.id}/edit",
            data={"company_id": c.id, "date": date.today().isoformat(), "interaction_type": "phone"},
        )
        assert resp.status_code == 403


# ── Delete ──────────────────────────────────────────────────────


class TestInteractionDelete:
    def test_delete_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Del Interaction Corp")
        ix = make_interaction(c, regular_user)
        ixid = ix.id
        resp = client.post(f"/interactions/{ixid}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(Interaction, ixid) is None

    def test_access_denied_for_other_user(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_company(other_user, company_name="Foreign Del Corp")
        ix = make_interaction(c, other_user)
        resp = client.post(f"/interactions/{ix.id}/delete")
        assert resp.status_code == 403
