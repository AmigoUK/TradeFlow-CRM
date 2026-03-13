"""Tests for follow-up CRUD, complete toggle, and matrix view."""

from datetime import date, timedelta

from extensions import db
from models.followup import FollowUp
from tests.conftest import login_as, make_client, make_followup


# ── List ────────────────────────────────────────────────────────


class TestFollowUpList:
    def test_list_renders(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get("/followups/")
        assert resp.status_code == 200

    def test_priority_filter(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="FU Filter Corp")
        make_followup(c, regular_user, priority="high", notes="High priority item")
        make_followup(c, regular_user, priority="low", notes="Low priority item")
        resp = client.get("/followups/?priority=high")
        assert resp.status_code == 200

    def test_overdue_filter(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Overdue Corp")
        make_followup(
            c, regular_user,
            due_date=date.today() - timedelta(days=5),
            completed=False,
            notes="Overdue task",
        )
        resp = client.get("/followups/?overdue=1")
        assert resp.status_code == 200

    def test_completed_filter(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Done Corp")
        make_followup(c, regular_user, completed=True, notes="Done task")
        resp = client.get("/followups/?completed=1")
        assert resp.status_code == 200


# ── Create ──────────────────────────────────────────────────────


class TestFollowUpCreate:
    def test_create_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="New FU Corp")
        resp = client.post(
            "/followups/new",
            data={
                "client_id": c.id,
                "due_date": date.today().isoformat(),
                "priority": "high",
                "notes": "Test follow-up",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        fu = FollowUp.query.filter_by(client_id=c.id, priority="high").first()
        assert fu is not None
        assert fu.user_id == regular_user.id

    def test_missing_client_rejected(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.post(
            "/followups/new",
            data={"client_id": "", "due_date": date.today().isoformat(), "priority": "medium"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_ownership_verified(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_client(other_user, company_name="Other FU Corp")
        resp = client.post(
            "/followups/new",
            data={"client_id": c.id, "due_date": date.today().isoformat(), "priority": "medium"},
        )
        assert resp.status_code == 403


# ── Edit ────────────────────────────────────────────────────────


class TestFollowUpEdit:
    def test_edit_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Edit FU Corp")
        fu = make_followup(c, regular_user, priority="low")
        resp = client.post(
            f"/followups/{fu.id}/edit",
            data={
                "client_id": c.id,
                "due_date": date.today().isoformat(),
                "priority": "high",
                "notes": "Updated",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(fu)
        assert fu.priority == "high"


# ── Complete toggle ─────────────────────────────────────────────


class TestFollowUpComplete:
    def test_toggle_completes(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Toggle Corp")
        fu = make_followup(c, regular_user, completed=False)
        resp = client.post(f"/followups/{fu.id}/complete", follow_redirects=True)
        assert resp.status_code == 200
        db.session.refresh(fu)
        assert fu.completed is True

    def test_toggle_back(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Toggle2 Corp")
        fu = make_followup(c, regular_user, completed=True)
        resp = client.post(f"/followups/{fu.id}/complete", follow_redirects=True)
        assert resp.status_code == 200
        db.session.refresh(fu)
        assert fu.completed is False

    def test_ajax_complete_returns_json(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Ajax Corp")
        fu = make_followup(c, regular_user, completed=False)
        resp = client.post(
            f"/followups/{fu.id}/complete",
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "completed"
        assert data["completed"] is True


# ── Delete ──────────────────────────────────────────────────────


class TestFollowUpDelete:
    def test_delete_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Del FU Corp")
        fu = make_followup(c, regular_user)
        fuid = fu.id
        resp = client.post(f"/followups/{fuid}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(FollowUp, fuid) is None


# ── Matrix ──────────────────────────────────────────────────────


class TestFollowUpMatrix:
    def test_matrix_renders(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get("/followups/matrix")
        assert resp.status_code == 200

    def test_matrix_categorises(self, client, regular_user):
        login_as(client, regular_user)
        c = make_client(regular_user, company_name="Matrix Corp")
        make_followup(c, regular_user, due_date=date.today(), priority="high", completed=False)
        make_followup(c, regular_user, due_date=date.today() + timedelta(days=30), priority="low", completed=False)
        resp = client.get("/followups/matrix")
        assert resp.status_code == 200
