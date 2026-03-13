"""Tests for Google Drive integration (Phase 4)."""

from models.google_drive_file import GoogleDriveFile
from models import Attachment
from extensions import db
from tests.conftest import login_as, make_client


class TestGoogleDriveFileModel:
    """GoogleDriveFile model basics."""

    def test_create_drive_file(self, app, admin_user):
        c = make_client(admin_user)
        df = GoogleDriveFile(
            google_file_id="drive-file-123",
            filename="contract.pdf",
            mime_type="application/pdf",
            google_url="https://drive.google.com/file/d/drive-file-123/view",
            client_id=c.id,
            uploaded_by_user_id=admin_user.id,
        )
        db.session.add(df)
        db.session.commit()
        assert df.id is not None
        assert df.client.id == c.id

    def test_client_drive_files_backref(self, app, admin_user):
        c = make_client(admin_user)
        df = GoogleDriveFile(
            google_file_id="drive-file-456",
            filename="report.docx",
            client_id=c.id,
            uploaded_by_user_id=admin_user.id,
        )
        db.session.add(df)
        db.session.commit()
        assert len(c.drive_files) == 1

    def test_attachment_drive_file_backref(self, app, admin_user):
        c = make_client(admin_user)
        att = Attachment(
            filename="test.pdf",
            stored_filename="drive:abc123",
            client_id=c.id,
            storage_type="drive",
        )
        db.session.add(att)
        db.session.flush()

        df = GoogleDriveFile(
            google_file_id="abc123",
            filename="test.pdf",
            attachment_id=att.id,
            client_id=c.id,
            uploaded_by_user_id=admin_user.id,
        )
        db.session.add(df)
        db.session.commit()
        assert att.drive_file is not None
        assert att.drive_file.google_file_id == "abc123"


class TestAttachmentStorageType:
    """Attachment storage_type column."""

    def test_default_storage_type_is_local(self, app, admin_user):
        c = make_client(admin_user)
        att = Attachment(
            filename="local.txt",
            stored_filename="uuid_local.txt",
            client_id=c.id,
        )
        db.session.add(att)
        db.session.commit()
        assert att.storage_type == "local"

    def test_drive_storage_type(self, app, admin_user):
        c = make_client(admin_user)
        att = Attachment(
            filename="cloud.pdf",
            stored_filename="drive:xyz789",
            client_id=c.id,
            storage_type="drive",
        )
        db.session.add(att)
        db.session.commit()
        assert att.storage_type == "drive"


class TestDriveRoutes:
    """Drive routes require authentication and Google connection."""

    def test_drive_upload_requires_login(self, client):
        resp = client.post("/google/drive/upload")
        assert resp.status_code in (302, 401)

    def test_drive_browse_requires_login(self, client):
        resp = client.get("/google/drive/browse")
        assert resp.status_code in (302, 401)

    def test_drive_browse_when_not_connected(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/google/drive/browse", follow_redirects=True)
        assert resp.status_code == 200

    def test_drive_unlink(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        df = GoogleDriveFile(
            google_file_id="unlink-test",
            filename="to-unlink.pdf",
            client_id=c.id,
            uploaded_by_user_id=admin_user.id,
        )
        db.session.add(df)
        db.session.commit()
        df_id = df.id

        resp = client.post(f"/google/drive/{df_id}/unlink", follow_redirects=True)
        assert resp.status_code == 200
        assert db.session.get(GoogleDriveFile, df_id) is None


class TestDriveUI:
    """Drive UI elements appear correctly."""

    def test_upload_form_no_drive_option_when_disconnected(self, client, admin_user):
        login_as(client, admin_user)
        c = make_client(admin_user)
        resp = client.get(f"/clients/{c.id}")
        assert resp.status_code == 200
        assert b"Upload to Google Drive" not in resp.data
        assert b"Link from Google Drive" not in resp.data

    def test_existing_upload_still_works(self, client, admin_user):
        """Existing local upload unaffected by Drive integration."""
        login_as(client, admin_user)
        c = make_client(admin_user)
        import io
        data = {
            "file": (io.BytesIO(b"test content"), "test.txt"),
            "client_id": str(c.id),
        }
        resp = client.post("/attachments/upload", data=data,
                          content_type="multipart/form-data",
                          follow_redirects=True)
        assert resp.status_code == 200
