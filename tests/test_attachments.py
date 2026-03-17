"""Tests for file attachment upload, download, edit, delete, and access control."""

import io

from extensions import db
from models.attachment import Attachment
from tests.conftest import login_as, make_company


# ── Upload ──────────────────────────────────────────────────────


class TestAttachmentUpload:
    def test_upload_success(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Upload Corp")
        data = {
            "file": (io.BytesIO(b"test file content"), "test.txt"),
            "company_id": str(c.id),
            "description": "Test upload",
        }
        resp = client.post(
            "/attachments/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        att = Attachment.query.filter_by(company_id=c.id).first()
        assert att is not None
        assert att.filename == "test.txt"

    def test_no_file_rejected(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="NoFile Corp")
        resp = client.post(
            "/attachments/upload",
            data={"company_id": str(c.id)},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_verifies_company_access(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_company(other_user, company_name="Forbidden Corp")
        data = {
            "file": (io.BytesIO(b"hack"), "evil.txt"),
            "company_id": str(c.id),
        }
        resp = client.post(
            "/attachments/upload",
            data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 403


# ── Download ────────────────────────────────────────────────────


class TestAttachmentDownload:
    def test_download_returns_file(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Download Corp")
        data = {
            "file": (io.BytesIO(b"download me"), "download.txt"),
            "company_id": str(c.id),
        }
        client.post(
            "/attachments/upload",
            data=data,
            content_type="multipart/form-data",
        )
        att = Attachment.query.filter_by(company_id=c.id).first()
        resp = client.get(f"/attachments/{att.id}/download")
        assert resp.status_code == 200
        assert b"download me" in resp.data


# ── Edit ────────────────────────────────────────────────────────


class TestAttachmentEdit:
    def test_edit_updates_description(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Edit Att Corp")
        data = {
            "file": (io.BytesIO(b"editable"), "editable.txt"),
            "company_id": str(c.id),
        }
        client.post(
            "/attachments/upload",
            data=data,
            content_type="multipart/form-data",
        )
        att = Attachment.query.filter_by(company_id=c.id).first()
        resp = client.post(
            f"/attachments/{att.id}/edit",
            data={"description": "New description"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        db.session.refresh(att)
        assert att.description == "New description"


# ── Delete ──────────────────────────────────────────────────────


class TestAttachmentDelete:
    def test_delete_removes_from_db(self, client, regular_user):
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Del Att Corp")
        data = {
            "file": (io.BytesIO(b"delete me"), "deleteme.txt"),
            "company_id": str(c.id),
        }
        client.post(
            "/attachments/upload",
            data=data,
            content_type="multipart/form-data",
        )
        att = Attachment.query.filter_by(company_id=c.id).first()
        attid = att.id
        resp = client.post(f"/attachments/{attid}/delete", follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(Attachment, attid) is None


# ── Access control ──────────────────────────────────────────────


class TestAttachmentAccessControl:
    def test_user_cannot_download_other_attachment(self, client, regular_user, other_user):
        # Upload as other_user
        login_as(client, other_user)
        c = make_company(other_user, company_name="Secret Corp")
        data = {
            "file": (io.BytesIO(b"secret"), "secret.txt"),
            "company_id": str(c.id),
        }
        client.post(
            "/attachments/upload",
            data=data,
            content_type="multipart/form-data",
        )
        att = Attachment.query.filter_by(company_id=c.id).first()

        # Logout other_user, then login as regular_user and try to download
        client.post("/logout")
        login_as(client, regular_user)
        resp = client.get(f"/attachments/{att.id}/download")
        assert resp.status_code == 403

    def test_manager_can_download_any_attachment(self, client, regular_user, manager_user):
        # Upload as regular_user
        login_as(client, regular_user)
        c = make_company(regular_user, company_name="Mgr Access Corp")
        data = {
            "file": (io.BytesIO(b"visible to manager"), "visible.txt"),
            "company_id": str(c.id),
        }
        client.post(
            "/attachments/upload",
            data=data,
            content_type="multipart/form-data",
        )
        att = Attachment.query.filter_by(company_id=c.id).first()

        # Logout regular_user, login as manager and download
        client.post("/logout")
        login_as(client, manager_user)
        resp = client.get(f"/attachments/{att.id}/download")
        assert resp.status_code == 200
        assert b"visible to manager" in resp.data
