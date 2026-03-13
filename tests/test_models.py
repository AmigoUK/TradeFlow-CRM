"""Tests for model logic — data layer correctness without HTTP."""

from datetime import date, timedelta

from extensions import db
from models.user import User, ROLES
from models.client import Client
from models.contact import Contact
from models.followup import FollowUp
from models.attachment import Attachment
from models.app_settings import AppSettings


# ── User model ──────────────────────────────────────────────────


class TestUserModel:
    def test_set_and_check_password(self, app):
        u = User(username="pw_test", display_name="PW Test", role="user")
        u.set_password("secret")
        assert u.check_password("secret")
        assert not u.check_password("wrong")

    def test_has_role_at_least_user(self, app):
        u = User(username="r1", display_name="R1", role="user")
        assert u.has_role_at_least("user")
        assert not u.has_role_at_least("manager")
        assert not u.has_role_at_least("admin")

    def test_has_role_at_least_manager(self, app):
        u = User(username="r2", display_name="R2", role="manager")
        assert u.has_role_at_least("user")
        assert u.has_role_at_least("manager")
        assert not u.has_role_at_least("admin")

    def test_has_role_at_least_admin(self, app):
        u = User(username="r3", display_name="R3", role="admin")
        assert u.has_role_at_least("user")
        assert u.has_role_at_least("manager")
        assert u.has_role_at_least("admin")

    def test_is_active_mirrors_is_active_user(self, app):
        u = User(username="a1", display_name="A1", role="user", is_active_user=True)
        assert u.is_active is True
        u.is_active_user = False
        assert u.is_active is False

    def test_roles_list(self):
        assert ROLES == ["user", "manager", "admin"]


# ── Client model ────────────────────────────────────────────────


class TestClientModel:
    def test_default_status_is_lead(self, app):
        admin = User.query.filter_by(username="admin").first()
        c = Client(company_name="Defaults Ltd", user_id=admin.id)
        db.session.add(c)
        db.session.commit()
        assert c.status == "lead"

    def test_cascade_delete_contacts_and_followups(self, app):
        admin = User.query.filter_by(username="admin").first()
        c = Client(company_name="Cascade Corp", user_id=admin.id)
        db.session.add(c)
        db.session.flush()

        ct = Contact(client_id=c.id, contact_type="phone", user_id=admin.id)
        fu = FollowUp(client_id=c.id, priority="high", user_id=admin.id)
        db.session.add_all([ct, fu])
        db.session.commit()

        assert Contact.query.count() >= 1
        assert FollowUp.query.count() >= 1

        db.session.delete(c)
        db.session.commit()

        assert Contact.query.filter_by(client_id=c.id).count() == 0
        assert FollowUp.query.filter_by(client_id=c.id).count() == 0

    def test_cascade_delete_attachments(self, app):
        admin = User.query.filter_by(username="admin").first()
        c = Client(company_name="Attach Corp", user_id=admin.id)
        db.session.add(c)
        db.session.flush()

        att = Attachment(
            filename="test.pdf",
            stored_filename="abc_test.pdf",
            client_id=c.id,
            file_size=1024,
        )
        db.session.add(att)
        db.session.commit()
        att_id = att.id

        db.session.delete(c)
        db.session.commit()
        assert db.session.get(Attachment, att_id) is None


# ── FollowUp model ──────────────────────────────────────────────


class TestFollowUpModel:
    def test_is_overdue_past_incomplete(self, app):
        admin = User.query.filter_by(username="admin").first()
        c = Client(company_name="FU Corp", user_id=admin.id)
        db.session.add(c)
        db.session.flush()

        fu = FollowUp(
            client_id=c.id,
            due_date=date.today() - timedelta(days=3),
            completed=False,
            user_id=admin.id,
        )
        db.session.add(fu)
        db.session.commit()
        assert fu.is_overdue is True

    def test_is_overdue_completed(self, app):
        admin = User.query.filter_by(username="admin").first()
        c = Client(company_name="FU2 Corp", user_id=admin.id)
        db.session.add(c)
        db.session.flush()

        fu = FollowUp(
            client_id=c.id,
            due_date=date.today() - timedelta(days=3),
            completed=True,
            user_id=admin.id,
        )
        db.session.add(fu)
        db.session.commit()
        assert fu.is_overdue is False

    def test_is_overdue_future(self, app):
        admin = User.query.filter_by(username="admin").first()
        c = Client(company_name="FU3 Corp", user_id=admin.id)
        db.session.add(c)
        db.session.flush()

        fu = FollowUp(
            client_id=c.id,
            due_date=date.today() + timedelta(days=5),
            completed=False,
            user_id=admin.id,
        )
        db.session.add(fu)
        db.session.commit()
        assert fu.is_overdue is False

    def test_is_overdue_today(self, app):
        admin = User.query.filter_by(username="admin").first()
        c = Client(company_name="FU4 Corp", user_id=admin.id)
        db.session.add(c)
        db.session.flush()

        fu = FollowUp(
            client_id=c.id,
            due_date=date.today(),
            completed=False,
            user_id=admin.id,
        )
        db.session.add(fu)
        db.session.commit()
        assert fu.is_overdue is False

    def test_default_priority(self, app):
        admin = User.query.filter_by(username="admin").first()
        c = Client(company_name="DefPri Corp", user_id=admin.id)
        db.session.add(c)
        db.session.flush()

        fu = FollowUp(client_id=c.id, user_id=admin.id)
        db.session.add(fu)
        db.session.commit()
        assert fu.priority == "medium"


# ── Attachment model ────────────────────────────────────────────


class TestAttachmentModel:
    def test_display_name_with_description(self, app):
        a = Attachment(
            filename="doc.pdf",
            stored_filename="x_doc.pdf",
            description="My Document",
            client_id=1,
        )
        assert a.display_name == "My Document"

    def test_display_name_without_description(self, app):
        a = Attachment(
            filename="doc.pdf",
            stored_filename="x_doc.pdf",
            client_id=1,
        )
        assert a.display_name == "doc.pdf"

    def test_file_size_display_bytes(self, app):
        a = Attachment(filename="f", stored_filename="f", client_id=1, file_size=512)
        assert a.file_size_display == "512 B"

    def test_file_size_display_kb(self, app):
        a = Attachment(filename="f", stored_filename="f", client_id=1, file_size=2048)
        assert a.file_size_display == "2.0 KB"

    def test_file_size_display_mb(self, app):
        a = Attachment(filename="f", stored_filename="f", client_id=1, file_size=2 * 1024 * 1024)
        assert a.file_size_display == "2.0 MB"

    def test_is_previewable_image(self, app):
        a = Attachment(filename="f", stored_filename="f", client_id=1, mime_type="image/png")
        assert a.is_previewable is True

    def test_is_previewable_pdf(self, app):
        a = Attachment(filename="f", stored_filename="f", client_id=1, mime_type="application/pdf")
        assert a.is_previewable is True

    def test_is_previewable_false(self, app):
        a = Attachment(filename="f", stored_filename="f", client_id=1, mime_type="application/zip")
        assert a.is_previewable is False

    def test_icon_image(self, app):
        a = Attachment(filename="f", stored_filename="f", client_id=1, mime_type="image/jpeg")
        assert a.icon == "bi-file-image"

    def test_icon_pdf(self, app):
        a = Attachment(filename="f", stored_filename="f", client_id=1, mime_type="application/pdf")
        assert a.icon == "bi-file-pdf"

    def test_icon_fallback(self, app):
        a = Attachment(filename="f", stored_filename="f", client_id=1, mime_type="application/zip")
        assert a.icon == "bi-file-earmark"


# ── AppSettings model ───────────────────────────────────────────


class TestAppSettingsModel:
    def test_singleton_auto_creates(self, app):
        settings = AppSettings.get()
        assert settings is not None
        assert settings.id == 1
        assert settings.theme == "light"

    def test_singleton_returns_same(self, app):
        s1 = AppSettings.get()
        s2 = AppSettings.get()
        assert s1.id == s2.id
