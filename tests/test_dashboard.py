"""Tests for dashboard, calendar API, and quarterly API."""

from datetime import date, timedelta

from tests.conftest import login_as, make_client, make_contact, make_followup


# ── Dashboard ───────────────────────────────────────────────────


class TestDashboard:
    def test_root_redirects_to_dashboard(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_dashboard_renders(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/dashboard")
        assert resp.status_code == 200

    def test_dashboard_shows_stats(self, client, admin_user):
        login_as(client, admin_user)
        make_client(admin_user, company_name="Dashboard Corp", status="active")
        resp = client.get("/dashboard")
        assert resp.status_code == 200

    def test_dashboard_filters_by_ownership(self, client, regular_user, other_user):
        login_as(client, regular_user)
        make_client(regular_user, company_name="My Dash Corp", status="active")
        make_client(other_user, company_name="Other Dash Corp", status="active")
        resp = client.get("/dashboard")
        assert resp.status_code == 200


# ── Calendar API ────────────────────────────────────────────────


class TestCalendarAPI:
    def test_events_returns_json(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/api/events")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_events_respects_date_range(self, client, admin_user):
        login_as(client, admin_user)
        today = date.today()
        start = (today - timedelta(days=30)).isoformat()
        end = (today + timedelta(days=30)).isoformat()
        resp = client.get(f"/api/events?start={start}&end={end}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_events_ownership_filter(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c1 = make_client(regular_user, company_name="My Events Corp")
        c2 = make_client(other_user, company_name="Other Events Corp")
        make_followup(c1, regular_user, due_date=date.today())
        make_followup(c2, other_user, due_date=date.today())
        resp = client.get("/api/events")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)


# ── Quarterly API ───────────────────────────────────────────────


class TestQuarterlyAPI:
    def test_quarterly_returns_json(self, client, admin_user):
        login_as(client, admin_user)
        resp = client.get("/api/quarterly-data")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "year" in data
        assert "quarters" in data
        assert "1" in data["quarters"]

    def test_quarterly_structure(self, client, admin_user):
        login_as(client, admin_user)
        year = date.today().year
        resp = client.get(f"/api/quarterly-data?year={year}")
        data = resp.get_json()
        q1 = data["quarters"]["1"]
        assert "total_contacts" in q1
        assert "total_followups" in q1
        assert "type_breakdown" in q1
        assert "priority_breakdown" in q1
        assert "months" in q1
        assert len(q1["months"]) == 3

    def test_quarterly_ownership_filter(self, client, regular_user, other_user):
        login_as(client, regular_user)
        c = make_client(other_user, company_name="Hidden Corp")
        make_contact(c, other_user, date=date.today())
        resp = client.get("/api/quarterly-data")
        assert resp.status_code == 200
