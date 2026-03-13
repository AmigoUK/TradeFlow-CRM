"""Tests for admin settings CRUD — quick functions, interaction types, etc."""

from extensions import db
from models import QuickFunction, InteractionType, AppSettings
from tests.conftest import login_as


# ── Settings page ───────────────────────────────────────────────


class TestSettingsPage:
    def test_admin_can_access(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/settings/")
        assert resp.status_code == 200

    def test_manager_cannot_access(self, client, manager_user):
        login_as(client, manager_user)
        resp = client.get("/settings/")
        assert resp.status_code == 403


# ── Quick Functions ─────────────────────────────────────────────


class TestQuickFunctions:
    def test_create(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post(
            "/settings/quick-functions/new",
            data={"label": "Test QF", "icon": "bi-star", "contact_type": "phone"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        qf = QuickFunction.query.filter_by(label="Test QF").first()
        assert qf is not None

    def test_edit(self, client, admin_user):
        login_as(client, admin_user)
        qf = QuickFunction.query.first()
        resp = client.post(
            f"/settings/quick-functions/{qf.id}/edit",
            data={"label": "Updated QF", "icon": "bi-star", "contact_type": "email"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(qf)
        assert qf.label == "Updated QF"

    def test_toggle(self, client, admin_user):
        login_as(client, admin_user)
        qf = QuickFunction.query.first()
        was_active = qf.is_active
        resp = client.post(f"/settings/quick-functions/{qf.id}/toggle", follow_redirects=True)
        assert resp.status_code == 200
        db.session.refresh(qf)
        assert qf.is_active != was_active

    def test_delete(self, client, admin_user):
        login_as(client, admin_user)
        qf = QuickFunction(label="Delete Me", icon="bi-trash", contact_type="phone")
        db.session.add(qf)
        db.session.commit()
        qfid = qf.id
        resp = client.post(f"/settings/quick-functions/{qfid}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(QuickFunction, qfid) is None


# ── Interaction Types ───────────────────────────────────────────


class TestInteractionTypes:
    def test_create(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post(
            "/settings/interaction-types/new",
            data={"label": "video", "icon": "bi-camera-video", "colour": "#ff5733"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        it = InteractionType.query.filter_by(label="video").first()
        assert it is not None

    def test_duplicate_rejected(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post(
            "/settings/interaction-types/new",
            data={"label": "phone", "icon": "bi-phone", "colour": "#0d6efd"},
            follow_redirects=True,
        )
        assert b"already exists" in resp.data


# ── UI Preferences ──────────────────────────────────────────────


class TestUIPreferences:
    def test_update_preferences(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post(
            "/settings/ui-preferences",
            json={"sticky_navbar": False, "pagination_size": 50},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        settings = AppSettings.get()
        assert settings.sticky_navbar is False
        assert settings.pagination_size == 50


# ── Theme ───────────────────────────────────────────────────────


class TestTheme:
    def test_update_theme(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post("/settings/theme", json={"theme": "dark"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["theme"] == "dark"

    def test_invalid_theme(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post("/settings/theme", json={"theme": "neon"})
        assert resp.status_code == 400
