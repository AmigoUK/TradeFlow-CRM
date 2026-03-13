"""Tests for authentication — login, logout, rate limiting."""

from extensions import db
from models.user import User
from tests.conftest import login, login_as


# ── Login ───────────────────────────────────────────────────────


class TestLogin:
    def test_login_page_renders(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert b"login" in resp.data.lower() or b"sign in" in resp.data.lower()

    def test_successful_login_redirects(self, client, admin_user):
        resp = client.post(
            "/login",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_successful_login_reaches_dashboard(self, client, admin_user):
        resp = login(client, "admin", "admin123")
        assert resp.status_code == 200

    def test_invalid_password(self, client, admin_user):
        resp = client.post(
            "/login",
            data={"username": "admin", "password": "wrong"},
        )
        assert b"Invalid" in resp.data

    def test_invalid_username(self, client, admin_user):
        resp = client.post(
            "/login",
            data={"username": "nobody", "password": "admin123"},
        )
        assert b"Invalid" in resp.data

    def test_deactivated_user(self, client):
        u = User(username="inactive1", display_name="Inactive", role="user", is_active_user=False)
        u.set_password("pass123")
        db.session.add(u)
        db.session.commit()

        resp = client.post(
            "/login",
            data={"username": "inactive1", "password": "pass123"},
        )
        assert b"Invalid" in resp.data

    def test_next_redirect(self, client, admin_user):
        resp = client.post(
            "/login?next=/clients/",
            data={"username": "admin", "password": "admin123"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/clients/" in resp.headers["Location"]

    def test_remember_me(self, client, admin_user):
        resp = client.post(
            "/login",
            data={"username": "admin", "password": "admin123", "remember": "on"},
            follow_redirects=False,
        )
        assert resp.status_code == 302


# ── Logout ──────────────────────────────────────────────────────


class TestLogout:
    def test_logout_clears_session(self, client, admin_user):
        login(client, "admin", "admin123")
        resp = client.post("/logout", follow_redirects=True)
        assert b"logged out" in resp.data.lower() or b"login" in resp.data.lower()

    def test_logout_get_method_not_allowed(self, client, admin_user):
        login(client, "admin", "admin123")
        resp = client.get("/logout")
        assert resp.status_code == 405


# ── Rate limiting ───────────────────────────────────────────────


class TestRateLimiting:
    def test_lockout_after_max_failures(self, client, admin_user):
        from blueprints.auth.routes import _failed_attempts

        _failed_attempts.clear()

        for _ in range(5):
            client.post("/login", data={"username": "admin", "password": "wrong"})

        resp = client.post(
            "/login",
            data={"username": "admin", "password": "wrong"},
        )
        assert resp.status_code == 429

        _failed_attempts.clear()

    def test_successful_login_resets_failures(self, client, admin_user):
        from blueprints.auth.routes import _failed_attempts

        _failed_attempts.clear()

        for _ in range(3):
            client.post("/login", data={"username": "admin", "password": "wrong"})

        login(client, "admin", "admin123")
        assert "127.0.0.1" not in _failed_attempts

        _failed_attempts.clear()
