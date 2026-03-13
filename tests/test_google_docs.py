"""Tests for Google Docs integration (Phase 3)."""

from models.google_doc import GoogleDoc
from models.doc_template import DocTemplate
from extensions import db
from tests.conftest import login_as, make_client


class TestGoogleDocModel:
    """GoogleDoc model basics."""

    def test_create_google_doc(self, app, admin_user):
        c = make_client(admin_user)
        doc = GoogleDoc(
            google_doc_id="doc-123-abc",
            title="Meeting Notes",
            google_url="https://docs.google.com/document/d/doc-123-abc/edit",
            doc_type="document",
            client_id=c.id,
            created_by_user_id=admin_user.id,
        )
        db.session.add(doc)
        db.session.commit()
        assert doc.id is not None
        assert doc.client.id == c.id

    def test_client_google_docs_backref(self, app, admin_user):
        c = make_client(admin_user)
        doc = GoogleDoc(
            google_doc_id="doc-456",
            title="Proposal",
            google_url="https://docs.google.com/document/d/doc-456/edit",
            client_id=c.id,
            created_by_user_id=admin_user.id,
        )
        db.session.add(doc)
        db.session.commit()
        assert len(c.google_docs) == 1
        assert c.google_docs[0].title == "Proposal"


class TestDocTemplateModel:
    """DocTemplate model basics."""

    def test_create_template(self, app):
        t = DocTemplate(
            name="Meeting Notes",
            description="Standard meeting notes template",
            google_template_doc_id="template-doc-id-123",
            template_type="meeting_notes",
        )
        db.session.add(t)
        db.session.commit()
        assert t.id is not None
        assert t.is_active is True


class TestDocsRoutes:
    """Docs routes require authentication and Google connection."""

    def test_create_doc_requires_login(self, client):
        resp = client.post("/google/docs/create")
        assert resp.status_code in (302, 401)

    def test_create_doc_when_not_connected(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        resp = client.post("/google/docs/create", data={
            "doc_title": "Test Doc",
            "client_id": c.id,
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_link_doc_when_not_connected(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        resp = client.post("/google/docs/link", data={
            "google_doc_id": "abc123",
            "doc_title": "Linked Doc",
            "client_id": c.id,
        }, follow_redirects=True)
        assert resp.status_code == 200

    def test_unlink_doc(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        doc = GoogleDoc(
            google_doc_id="unlink-test",
            title="To Unlink",
            google_url="https://docs.google.com/document/d/unlink-test/edit",
            client_id=c.id,
            created_by_user_id=admin_user.id,
        )
        db.session.add(doc)
        db.session.commit()
        doc_id = doc.id

        resp = client.post(f"/google/docs/{doc_id}/unlink", follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(GoogleDoc, doc_id) is None

    def test_templates_json_endpoint(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/google/docs/templates")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)


class TestDocTemplateAdmin:
    """Admin template management."""

    def test_admin_can_create_template(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.post("/google/docs/templates/new", data={
            "template_name": "Test Template",
            "template_description": "A test",
            "template_doc_id": "test-doc-id-abc",
            "template_type": "meeting_notes",
        }, follow_redirects=True)
        assert resp.status_code == 200
        t = DocTemplate.query.filter_by(name="Test Template").first()
        assert t is not None

    def test_non_admin_blocked_from_creating_template(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.post("/google/docs/templates/new", data={
            "template_name": "Hacker Template",
            "template_doc_id": "hack",
        })
        assert resp.status_code == 403

    def test_admin_can_delete_template(self, client, admin_user):
        login_as(client, admin_user)
        t = DocTemplate(
            name="To Delete",
            google_template_doc_id="delete-me",
        )
        db.session.add(t)
        db.session.commit()
        resp = client.post(f"/google/docs/templates/{t.id}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(DocTemplate, t.id) is None


class TestDocsUI:
    """Docs UI elements in client detail and settings."""

    def test_client_detail_no_docs_card_when_disconnected(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        resp = client.get(f"/clients/{c.id}")
        assert resp.status_code == 200
        assert b"Google Docs" not in resp.data

    def test_settings_shows_doc_templates_when_enabled(self, client, admin_user):
        login_as(client, admin_user)
        from models.google_oauth_config import GoogleOAuthConfig
        from blueprints.google.google_service import encrypt_client_secret
        config = GoogleOAuthConfig.get()
        config.client_id = "test-id"
        config.client_secret_encrypted = encrypt_client_secret("test-secret")
        config.is_enabled = True
        db.session.commit()

        resp = client.get("/settings/")
        assert resp.status_code == 200
        assert b"Document Templates" in resp.data
