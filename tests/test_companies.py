"""Tests for company CRUD, status updates, quick actions, and delete."""

from extensions import db
from models.company import Company
from models.interaction import Interaction
from models.followup import FollowUp
from tests.conftest import login_as, make_company, make_interaction, make_followup


# ── List ────────────────────────────────────────────────────────


class TestCompanyList:
    def test_requires_login(self, client):
        resp = client.get("/companies/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_shows_companies(self, client, regular_user):
        login_as(client, regular_user)
        make_company(regular_user, company_name="Visible Corp")
        resp = client.get("/companies/")
        assert resp.status_code == 200
        assert b"Visible Corp" in resp.data

    def test_search_filter(self, client, regular_user):
        login_as(client, regular_user)
        make_company(regular_user, company_name="Alpha Ltd")
        make_company(regular_user, company_name="Beta Inc")
        resp = client.get("/companies/?q=Alpha")
        assert b"Alpha Ltd" in resp.data
        assert b"Beta Inc" not in resp.data

    def test_status_filter(self, client, regular_user):
        login_as(client, regular_user)
        make_company(regular_user, company_name="Active Co", status="active")
        make_company(regular_user, company_name="Lead Co", status="lead")
        resp = client.get("/companies/?status=active")
        assert b"Active Co" in resp.data
        assert b"Lead Co" not in resp.data


# ── Create ──────────────────────────────────────────────────────


class TestCompanyCreate:
    def test_form_renders(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get("/companies/new")
        assert resp.status_code == 200

    def test_create_success(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.post(
            "/companies/new",
            data={"company_name": "New Corp", "status": "lead"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"New Corp" in resp.data
        c = Company.query.filter_by(company_name="New Corp").first()
        assert c is not None
        assert c.user_id == regular_user.id

    def test_missing_company_name_rejected(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.post(
            "/companies/new",
            data={"company_name": "", "status": "lead"},
        )
        assert b"required" in resp.data.lower()


# ── Detail ──────────────────────────────────────────────────────


class TestCompanyDetail:
    def test_shows_company_info(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Detail Corp", industry="Finance")
        resp = client.get(f"/companies/{c.id}")
        assert resp.status_code == 200
        assert b"Detail Corp" in resp.data


# ── Edit ────────────────────────────────────────────────────────


class TestCompanyEdit:
    def test_edit_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Old Name")
        resp = client.post(
            f"/companies/{c.id}/edit",
            data={"company_name": "New Name", "status": "active"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"New Name" in resp.data

    def test_edit_preserves_other_fields(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Keep Fields", industry="Tech", phone="123")
        client.post(
            f"/companies/{c.id}/edit",
            data={"company_name": "Keep Fields Updated", "status": "active", "industry": "Tech", "phone": "123"},
        )
        c_updated = db.session.get(Company, c.id)
        assert c_updated.industry == "Tech"
        assert c_updated.phone == "123"


# ── Status PATCH ────────────────────────────────────────────────


class TestCompanyStatus:
    def test_status_update(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Status Corp")
        resp = client.patch(f"/companies/{c.id}/status", json={"status": "active"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["status"] == "active"

    def test_invalid_status_rejected(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Bad Status Corp")
        resp = client.patch(f"/companies/{c.id}/status", json={"status": "invalid_status"})
        assert resp.status_code == 400


# ── Delete ──────────────────────────────────────────────────────


class TestCompanyDelete:
    def test_delete_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Delete Me Corp")
        cid = c.id
        resp = client.post(f"/companies/{cid}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert b"deleted" in resp.data.lower()
        assert db.session.get(Company, cid) is None

    def test_delete_cascades(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Cascade Del Corp")
        make_interaction(c, regular_user)
        make_followup(c, regular_user)
        cid = c.id
        client.post(f"/companies/{cid}/delete")
        assert Interaction.query.filter_by(company_id=cid).count() == 0
        assert FollowUp.query.filter_by(company_id=cid).count() == 0


# ── Quick action ────────────────────────────────────────────────


class TestQuickAction:
    def test_quick_action_creates_interaction(self, client, regular_user):
        login_as(client, regular_user)
        from models import QuickFunction
        c = make_company(regular_user, company_name="Quick Corp")
        qf = QuickFunction.query.first()
        resp = client.post(
            f"/companies/{c.id}/quick-action",
            data={"action_id": qf.id},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        interactions = Interaction.query.filter_by(company_id=c.id).all()
        assert len(interactions) >= 1
