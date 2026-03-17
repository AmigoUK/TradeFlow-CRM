"""Tests for the CSV import/export feature (data_io blueprint)."""

import csv
import io
from datetime import date

import pytest

from extensions import db
from models.company import Company
from models.interaction import Interaction
from models.custom_field import CustomFieldDefinition, CustomFieldValue
from models.followup import FollowUp
from tests.conftest import login_as, make_company, make_interaction, make_followup


# ── Helpers ────────────────────────────────────────────────────


def _make_csv(headers, rows):
    """Build a BytesIO CSV file from headers and rows."""
    buf = io.BytesIO()
    buf.write(",".join(headers).encode("utf-8") + b"\n")
    for row in rows:
        buf.write(",".join(str(v) for v in row).encode("utf-8") + b"\n")
    buf.seek(0)
    return buf


def _parse_csv_response(response):
    """Parse CSV content from a response into a list of dicts."""
    text = response.data.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


# ── Export Companies ──────────────────────────────────────────


class TestExportCompanies:
    def test_admin_can_export(self, client, admin_user):
        login_as(client, admin_user)
        make_company(admin_user, company_name="Export Corp")
        resp = client.get("/settings/data/export/companies")
        assert resp.status_code == 200
        assert "text/csv" in resp.content_type
        assert "attachment" in resp.headers.get("Content-Disposition", "")

    def test_non_admin_gets_403(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get("/settings/data/export/companies")
        assert resp.status_code == 403

    def test_correct_headers(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/settings/data/export/companies")
        rows = _parse_csv_response(resp)
        text = resp.data.decode("utf-8-sig")
        header_line = text.split("\n")[0].strip()
        assert "company_name" in header_line
        assert "status" in header_line
        assert "owner" in header_line

    def test_correct_data(self, client, admin_user):
        login_as(client, admin_user)
        make_company(admin_user, company_name="Data Corp", status="active", industry="Tech")
        resp = client.get("/settings/data/export/companies")
        rows = _parse_csv_response(resp)
        names = [r["company_name"] for r in rows]
        assert "Data Corp" in names

    def test_includes_custom_fields(self, client, admin_user):
        login_as(client, admin_user)
        cf = CustomFieldDefinition(label="Website", field_type="url", is_active=True)
        db.session.add(cf)
        db.session.flush()
        c = make_company(admin_user, company_name="CF Corp")
        cfv = CustomFieldValue(definition_id=cf.id, company_id=c.id, value="https://example.com")
        db.session.add(cfv)
        db.session.commit()

        resp = client.get("/settings/data/export/companies")
        rows = _parse_csv_response(resp)
        cf_row = [r for r in rows if r["company_name"] == "CF Corp"][0]
        assert cf_row["Website"] == "https://example.com"


# ── Export Interactions ───────────────────────────────────────


class TestExportInteractions:
    def test_correct_headers(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/settings/data/export/interactions")
        assert resp.status_code == 200
        text = resp.data.decode("utf-8-sig")
        header_line = text.split("\n")[0].strip()
        assert "company_name" in header_line
        assert "interaction_type" in header_line

    def test_data_includes_company_name(self, client, admin_user):
        login_as(client, admin_user)
        c = make_company(admin_user, company_name="Interaction Corp")
        make_interaction(c, admin_user, notes="Test note")
        resp = client.get("/settings/data/export/interactions")
        rows = _parse_csv_response(resp)
        names = [r["company_name"] for r in rows]
        assert "Interaction Corp" in names

    def test_non_admin_gets_403(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get("/settings/data/export/interactions")
        assert resp.status_code == 403


# ── Export Follow-ups ──────────────────────────────────────────


class TestExportFollowups:
    def test_correct_headers(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/settings/data/export/followups")
        assert resp.status_code == 200
        text = resp.data.decode("utf-8-sig")
        header_line = text.split("\n")[0].strip()
        assert "company_name" in header_line
        assert "priority" in header_line

    def test_correct_data(self, client, admin_user):
        login_as(client, admin_user)
        c = make_company(admin_user, company_name="FU Corp")
        make_followup(c, admin_user, priority="high", notes="Urgent task")
        resp = client.get("/settings/data/export/followups")
        rows = _parse_csv_response(resp)
        fu_rows = [r for r in rows if r["company_name"] == "FU Corp"]
        assert len(fu_rows) >= 1
        assert fu_rows[0]["priority"] == "high"

    def test_non_admin_gets_403(self, client, regular_user):
        login_as(client, regular_user)
        resp = client.get("/settings/data/export/followups")
        assert resp.status_code == 403


# ── Download Template ──────────────────────────────────────────


class TestDownloadTemplate:
    def test_companies_template(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/settings/data/template/companies")
        assert resp.status_code == 200
        rows = _parse_csv_response(resp)
        assert len(rows) == 2  # 2 example rows
        assert rows[0]["company_name"] == "Acme Ltd"

    def test_interactions_template(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/settings/data/template/interactions")
        assert resp.status_code == 200
        rows = _parse_csv_response(resp)
        assert len(rows) == 2

    def test_followups_template(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/settings/data/template/followups")
        assert resp.status_code == 200
        rows = _parse_csv_response(resp)
        assert len(rows) == 2

    def test_invalid_entity_returns_404(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/settings/data/template/bogus")
        assert resp.status_code in (302, 404)


# ── Import Companies ─────────────────────────────────────────


class TestImportCompanies:
    def test_valid_csv(self, client, admin_user):
        login_as(client, admin_user)
        csv_file = _make_csv(
            ["company_name", "industry", "status"],
            [["Import Corp", "Tech", "active"]],
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "companies", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert b"1" in resp.data  # "1 record imported"
        assert Company.query.filter_by(company_name="Import Corp").first() is not None

    def test_missing_company_name_error(self, client, admin_user):
        login_as(client, admin_user)
        csv_file = _make_csv(
            ["company_name", "industry"],
            [["", "Tech"]],
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "companies", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert b"company_name is required" in resp.data

    def test_invalid_status_error(self, client, admin_user):
        login_as(client, admin_user)
        csv_file = _make_csv(
            ["company_name", "status"],
            [["Bad Status Corp", "nonexistent"]],
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "companies", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert b"Invalid status" in resp.data
        assert Company.query.filter_by(company_name="Bad Status Corp").first() is None

    def test_owner_column_resolution(self, client, admin_user):
        login_as(client, admin_user)
        csv_file = _make_csv(
            ["company_name", "owner"],
            [["Owned Corp", "admin"]],
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "companies", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        c = Company.query.filter_by(company_name="Owned Corp").first()
        assert c is not None
        assert c.user_id == admin_user.id

    def test_custom_fields_import(self, client, admin_user):
        login_as(client, admin_user)
        cf = CustomFieldDefinition(label="Website", field_type="url", is_active=True)
        db.session.add(cf)
        db.session.commit()

        csv_file = _make_csv(
            ["company_name", "Website"],
            [["CF Import Corp", "https://example.com"]],
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "companies", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        c = Company.query.filter_by(company_name="CF Import Corp").first()
        assert c is not None
        cfv = CustomFieldValue.query.filter_by(company_id=c.id, definition_id=cf.id).first()
        assert cfv is not None
        assert cfv.value == "https://example.com"

    def test_partial_errors(self, client, admin_user):
        login_as(client, admin_user)
        csv_file = _make_csv(
            ["company_name", "status"],
            [
                ["Good Corp", "active"],
                ["", "active"],  # Missing company_name
                ["Also Good Corp", "lead"],
            ],
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "companies", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert Company.query.filter_by(company_name="Good Corp").first() is not None
        assert Company.query.filter_by(company_name="Also Good Corp").first() is not None
        assert b"1" in resp.data  # 1 row skipped

    def test_empty_file(self, client, admin_user):
        login_as(client, admin_user)
        csv_file = _make_csv(["company_name"], [])
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "companies", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert b"empty" in resp.data.lower()

    def test_non_admin_gets_403(self, client, regular_user):
        login_as(client, regular_user)
        csv_file = _make_csv(["company_name"], [["Sneaky Corp"]])
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "companies", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 403


# ── Import Interactions ───────────────────────────────────────


class TestImportInteractions:
    def test_valid_csv(self, client, admin_user):
        login_as(client, admin_user)
        c = make_company(admin_user, company_name="Interaction Import Corp")
        csv_file = _make_csv(
            ["company_name", "date", "interaction_type", "notes"],
            [["Interaction Import Corp", date.today().isoformat(), "email", "Sent proposal"]],
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "interactions", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        ix = Interaction.query.filter_by(company_id=c.id).first()
        assert ix is not None
        assert ix.interaction_type == "email"

    def test_unknown_company_error(self, client, admin_user):
        login_as(client, admin_user)
        csv_file = _make_csv(
            ["company_name", "interaction_type"],
            [["Nonexistent Corp", "phone"]],
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "interactions", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert b"No company found" in resp.data

    def test_ambiguous_company_error(self, client, admin_user):
        login_as(client, admin_user)
        make_company(admin_user, company_name="Dupe Corp")
        make_company(admin_user, company_name="Dupe Corp")
        csv_file = _make_csv(
            ["company_name", "interaction_type"],
            [["Dupe Corp", "phone"]],
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "interactions", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert b"Multiple companies" in resp.data

    def test_defaults_applied(self, client, admin_user):
        login_as(client, admin_user)
        c = make_company(admin_user, company_name="Default Corp")
        csv_file = _make_csv(
            ["company_name"],
            [["Default Corp"]],
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "interactions", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        ix = Interaction.query.filter_by(company_id=c.id).first()
        assert ix is not None
        assert ix.interaction_type == "phone"  # Default
        assert ix.date == date.today()  # Default
        assert ix.user_id == admin_user.id  # Default to current admin


# ── Import Follow-ups ─────────────────────────────────────────


class TestImportFollowups:
    def test_valid_csv(self, client, admin_user):
        login_as(client, admin_user)
        c = make_company(admin_user, company_name="FU Import Corp")
        csv_file = _make_csv(
            ["company_name", "due_date", "priority", "notes"],
            [["FU Import Corp", date.today().isoformat(), "high", "Urgent task"]],
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "followups", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        fu = FollowUp.query.filter_by(company_id=c.id).first()
        assert fu is not None
        assert fu.priority == "high"

    def test_invalid_priority_error(self, client, admin_user):
        login_as(client, admin_user)
        c = make_company(admin_user, company_name="Priority Corp")
        csv_file = _make_csv(
            ["company_name", "priority"],
            [["Priority Corp", "urgent"]],  # Invalid priority
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "followups", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert b"Invalid priority" in resp.data

    def test_completed_boolean_variants(self, client, admin_user):
        login_as(client, admin_user)
        c = make_company(admin_user, company_name="Bool Corp")
        csv_file = _make_csv(
            ["company_name", "completed"],
            [
                ["Bool Corp", "true"],
                ["Bool Corp", "yes"],
                ["Bool Corp", "1"],
            ],
        )
        resp = client.post(
            "/settings/data/import",
            data={"entity_type": "followups", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        followups = FollowUp.query.filter_by(company_id=c.id).all()
        assert len(followups) == 3
        assert all(fu.completed for fu in followups)


# ── Import Error Report ───────────────────────────────────────


class TestImportErrorReport:
    def test_download_error_csv(self, client, admin_user):
        login_as(client, admin_user)
        # Trigger an import with errors first
        csv_file = _make_csv(
            ["company_name", "status"],
            [["", "active"]],  # Missing company_name
        )
        client.post(
            "/settings/data/import",
            data={"entity_type": "companies", "csv_file": (csv_file, "test.csv")},
            content_type="multipart/form-data",
        )
        # Now download the error report
        resp = client.get("/settings/data/import/errors")
        assert resp.status_code == 200
        assert "text/csv" in resp.content_type
        text = resp.data.decode("utf-8")
        assert "error" in text.lower()
        assert "company_name is required" in text

    def test_redirect_when_no_errors(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/settings/data/import/errors", follow_redirects=False)
        assert resp.status_code == 302
