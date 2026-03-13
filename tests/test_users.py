"""Tests for user management routes (manager+ only)."""

from extensions import db
from models.user import User
from models.client import Client
from tests.conftest import login_as, make_client


# ── List ────────────────────────────────────────────────────────


class TestUserList:
    def test_renders_for_manager(self, client, manager_user):
        login_as(client, manager_user)
        resp = client.get("/users/")
        assert resp.status_code == 200

    def test_forbidden_for_user(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get("/users/")
        assert resp.status_code == 403


# ── Create ──────────────────────────────────────────────────────


class TestUserCreate:
    def test_create_success(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post(
            "/users/new",
            data={
                "username": "newuser",
                "display_name": "New User",
                "password": "newpass123",
                "role": "user",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        u = User.query.filter_by(username="newuser").first()
        assert u is not None
        assert u.display_name == "New User"

    def test_duplicate_username_rejected(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post(
            "/users/new",
            data={
                "username": "admin",
                "display_name": "Duplicate",
                "password": "pass123",
                "role": "user",
            },
        )
        assert b"already taken" in resp.data

    def test_manager_cannot_create_admin(self, client, manager_user):
        login_as(client, manager_user)
        resp = client.post(
            "/users/new",
            data={
                "username": "sneakyadmin",
                "display_name": "Sneaky",
                "password": "pass123",
                "role": "admin",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        u = User.query.filter_by(username="sneakyadmin").first()
        assert u is not None
        assert u.role == "user"  # Downgraded from admin


# ── Edit ────────────────────────────────────────────────────────


class TestUserEdit:
    def test_edit_success(self, client, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.post(
            f"/users/{regular_user.id}/edit",
            data={"display_name": "Updated Name", "role": "user"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.display_name == "Updated Name"

    def test_manager_cannot_escalate_role(self, client, manager_user, regular_user):
        login_as(client, manager_user)
        resp = client.post(
            f"/users/{regular_user.id}/edit",
            data={"display_name": "Escalated", "role": "admin"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.role == "user"  # Role unchanged


# ── Toggle ──────────────────────────────────────────────────────


class TestUserToggle:
    def test_deactivate_user(self, client, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.post(
            f"/users/{regular_user.id}/toggle",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(regular_user)
        assert regular_user.is_active_user is False

    def test_cannot_deactivate_self(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post(
            f"/users/{admin_user.id}/toggle",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"cannot deactivate" in resp.data.lower()


# ── Reset password ──────────────────────────────────────────────


class TestResetPassword:
    def test_reset_success(self, client, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.post(
            f"/users/{regular_user.id}/reset-password",
            data={"new_password": "brand_new_password"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"reset" in resp.data.lower()
        db.session.refresh(regular_user)
        assert regular_user.check_password("brand_new_password")

    def test_empty_password_rejected(self, client, admin_user, regular_user):
        login_as(client, admin_user)
        resp = client.post(
            f"/users/{regular_user.id}/reset-password",
            data={"new_password": ""},
            follow_redirects=True,
        )
        assert b"cannot be empty" in resp.data.lower()


# ── Delegate ────────────────────────────────────────────────────


class TestDelegate:
    def test_delegate_transfers_records(self, client, admin_user, regular_user):
        login_as(client, admin_user)
        make_client(regular_user, company_name="Delegate Corp")
        make_client(regular_user, company_name="Delegate Corp 2")

        resp = client.post(
            f"/users/{regular_user.id}/delegate",
            data={"target_user_id": admin_user.id},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        remaining = Client.query.filter_by(user_id=regular_user.id).count()
        assert remaining == 0
