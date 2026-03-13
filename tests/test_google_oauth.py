"""Tests for Google OAuth2 integration (Phase 0)."""

from unittest.mock import patch, MagicMock

from models.google_oauth_config import GoogleOAuthConfig
from models.google_credential import GoogleCredential
from extensions import db
from tests.conftest import login_as


class TestGoogleOAuthConfig:
    """Admin can save/update OAuth config; non-admin blocked."""

    def test_admin_can_save_google_config(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post("/google/config", data={
            "google_client_id": "test-client-id.apps.googleusercontent.com",
            "google_client_secret": "test-secret-123",
            "google_enabled": "on",
            "scope_calendar": "on",
        }, follow_redirects=True)
        assert resp.status_code == 200

        config = GoogleOAuthConfig.get()
        assert config.client_id == "test-client-id.apps.googleusercontent.com"
        assert config.is_enabled is True
        assert config.client_secret_encrypted is not None
        assert "calendar" in config.scopes

    def test_admin_can_update_config_without_changing_secret(self, client, admin_user):
        login_as(client, admin_user)
        # First save with real secret
        client.post("/google/config", data={
            "google_client_id": "id-1",
            "google_client_secret": "real-secret",
        })
        config = GoogleOAuthConfig.get()
        original_encrypted = config.client_secret_encrypted

        # Update with placeholder secret — should keep original
        client.post("/google/config", data={
            "google_client_id": "id-2",
            "google_client_secret": "••••••••",
        })
        config = GoogleOAuthConfig.get()
        assert config.client_id == "id-2"
        assert config.client_secret_encrypted == original_encrypted

    def test_non_admin_blocked_from_google_settings(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.post("/google/config", data={
            "google_client_id": "hacker",
            "google_client_secret": "hacker",
        })
        assert resp.status_code == 403

    def test_manager_blocked_from_google_settings(self, client, manager_user):
        login_as(client, manager_user)
        resp = client.post("/google/config", data={
            "google_client_id": "hacker",
            "google_client_secret": "hacker",
        })
        assert resp.status_code == 403


class TestGoogleOAuthConnect:
    """OAuth connect redirects with correct params and state."""

    def test_connect_when_not_enabled(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/google/connect", follow_redirects=True)
        assert resp.status_code == 200
        # Should redirect with a flash warning

    def test_connect_when_enabled(self, client, admin_user):
        login_as(client, admin_user)
        # Configure Google
        config = GoogleOAuthConfig.get()
        config.client_id = "test-id"
        from blueprints.google.google_service import encrypt_client_secret
        config.client_secret_encrypted = encrypt_client_secret("test-secret")
        config.is_enabled = True
        db.session.commit()

        with patch("google_auth_oauthlib.flow.Flow") as MockFlow:
            mock_flow = MagicMock()
            MockFlow.from_client_config.return_value = mock_flow
            mock_flow.authorization_url.return_value = ("https://accounts.google.com/auth", None)

            resp = client.get("/google/connect")
            assert resp.status_code == 302
            assert "accounts.google.com" in resp.location

    def test_status_endpoint(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/google/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "enabled" in data
        assert "connected" in data
        assert "email" in data


class TestGoogleOAuthDisconnect:
    """Disconnect revokes tokens and deletes credential."""

    def test_disconnect_removes_credential(self, client, admin_user):
        login_as(client, admin_user)
        # Create a credential
        from blueprints.google.google_service import encrypt_token
        cred = GoogleCredential(
            user_id=admin_user.id,
            access_token_encrypted=encrypt_token("fake-access-token"),
            refresh_token_encrypted=encrypt_token("fake-refresh-token"),
            google_email="admin@gmail.com",
            is_valid=True,
        )
        db.session.add(cred)
        db.session.commit()

        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            resp = client.post("/google/disconnect", follow_redirects=True)
            assert resp.status_code == 200

        cred = GoogleCredential.query.filter_by(user_id=admin_user.id).first()
        assert cred is None

    def test_disconnect_when_not_connected(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post("/google/disconnect", follow_redirects=True)
        assert resp.status_code == 200


class TestTokenEncryption:
    """Token encryption round-trips correctly."""

    def test_encrypt_decrypt_roundtrip(self, app):
        from blueprints.google.google_service import encrypt_token, decrypt_token
        original = "ya29.a0AfH6SM-test-token-value"
        encrypted = encrypt_token(original)
        assert encrypted != original
        decrypted = decrypt_token(encrypted)
        assert decrypted == original

    def test_decrypt_none_returns_none(self, app):
        from blueprints.google.google_service import decrypt_token
        assert decrypt_token(None) is None
        assert decrypt_token("") is None


class TestGoogleServiceHelpers:
    """Helper functions work correctly."""

    def test_is_google_enabled_default_false(self, app):
        from blueprints.google.google_service import is_google_enabled
        assert is_google_enabled() is False

    def test_google_config_singleton(self, app):
        config1 = GoogleOAuthConfig.get()
        config2 = GoogleOAuthConfig.get()
        assert config1.id == config2.id

    def test_settings_page_shows_google_card(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/settings/")
        assert resp.status_code == 200
        assert b"Google Integration" in resp.data

    def test_navbar_shows_connect_when_enabled(self, client, admin_user):
        login_as(client, admin_user)
        config = GoogleOAuthConfig.get()
        config.client_id = "test-id"
        from blueprints.google.google_service import encrypt_client_secret
        config.client_secret_encrypted = encrypt_client_secret("test-secret")
        config.is_enabled = True
        db.session.commit()

        resp = client.get("/dashboard")
        assert b"Connect Google Account" in resp.data


class TestExistingFeaturesUnaffected:
    """All existing CRM features work when Google is not configured."""

    def test_dashboard_loads(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/dashboard")
        assert resp.status_code == 200

    def test_calendar_loads(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/calendar")
        assert resp.status_code == 200

    def test_agenda_loads(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/agenda")
        assert resp.status_code == 200

    def test_api_events_loads(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/api/events")
        assert resp.status_code == 200
