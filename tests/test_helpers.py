"""Tests for Jinja2 filter/helper functions defined in app.py."""

from datetime import date, timedelta
from unittest.mock import patch

from markupsafe import Markup

from app import days_overdue, mailto_link, relative_date, tel_link


# ── tel_link ────────────────────────────────────────────────────


class TestTelLink:
    def test_renders_link(self):
        result = tel_link("+44 123 456")
        assert isinstance(result, Markup)
        assert 'href="tel:+44 123 456"' in result
        assert "+44 123 456" in result

    def test_none_returns_dash(self):
        assert tel_link(None) == "\u2014"

    def test_empty_returns_dash(self):
        assert tel_link("") == "\u2014"


# ── mailto_link ─────────────────────────────────────────────────


class TestMailtoLink:
    def test_renders_link(self):
        result = mailto_link("test@example.com")
        assert isinstance(result, Markup)
        assert 'href="mailto:test@example.com"' in result

    def test_none_returns_dash(self):
        assert mailto_link(None) == "\u2014"

    def test_empty_returns_dash(self):
        assert mailto_link("") == "\u2014"


# ── relative_date ───────────────────────────────────────────────


class TestRelativeDate:
    def test_today(self):
        assert relative_date(date.today()) == "Today"

    def test_yesterday(self):
        assert relative_date(date.today() - timedelta(days=1)) == "Yesterday"

    def test_tomorrow(self):
        assert relative_date(date.today() + timedelta(days=1)) == "Tomorrow"

    def test_days_ago(self):
        d = date.today() - timedelta(days=3)
        assert relative_date(d) == "3 days ago"

    def test_in_days(self):
        d = date.today() + timedelta(days=5)
        assert relative_date(d) == "In 5 days"

    def test_far_future(self):
        d = date.today() + timedelta(days=60)
        assert relative_date(d) == d.strftime("%d %b %Y")

    def test_none_returns_dash(self):
        assert relative_date(None) == "\u2014"

    def test_string_passthrough(self):
        assert relative_date("custom") == "custom"


# ── days_overdue ────────────────────────────────────────────────


class TestDaysOverdue:
    def test_past_is_positive(self):
        d = date.today() - timedelta(days=5)
        assert days_overdue(d) == 5

    def test_future_is_negative(self):
        d = date.today() + timedelta(days=3)
        assert days_overdue(d) == -3

    def test_today_is_zero(self):
        assert days_overdue(date.today()) == 0

    def test_none_returns_zero(self):
        assert days_overdue(None) == 0
