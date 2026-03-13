"""Shared fixtures and helpers for the NextStep-CRM test suite."""

import os
import tempfile

import pytest

from extensions import db as _db
from models.user import User
from models.client import Client
from models.contact import Contact
from models.followup import FollowUp


# ── Test configuration ──────────────────────────────────────────


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"
    SERVER_NAME = "localhost"
    UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), "nextstep-test-uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


# ── Core fixtures ───────────────────────────────────────────────


@pytest.fixture()
def app():
    """Create a fresh application with a persistent app context for each test."""
    from app import create_app

    application = create_app(TestConfig)

    ctx = application.app_context()
    ctx.push()

    yield application

    _db.session.remove()
    _db.drop_all()
    ctx.pop()


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


# ── User fixtures ───────────────────────────────────────────────


@pytest.fixture()
def admin_user(app):
    """Return the seeded admin user (created by create_app)."""
    return User.query.filter_by(username="admin").first()


@pytest.fixture()
def manager_user(app):
    """Create and return a manager user."""
    user = User(username="manager1", display_name="Manager One", role="manager")
    user.set_password("manager123")
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture()
def regular_user(app):
    """Create and return a regular user."""
    user = User(username="user1", display_name="User One", role="user")
    user.set_password("user123")
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture()
def other_user(app):
    """Create a second regular user for ownership tests."""
    user = User(username="user2", display_name="User Two", role="user")
    user.set_password("user456")
    _db.session.add(user)
    _db.session.commit()
    return user


# ── Login helpers ───────────────────────────────────────────────


def login(client, username, password):
    """POST to /login and return the response."""
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def login_as(client, user):
    """Login as a specific user fixture (uses known password conventions)."""
    passwords = {
        "admin": "admin123",
        "manager1": "manager123",
        "user1": "user123",
        "user2": "user456",
    }
    pw = passwords.get(user.username, "password")
    return login(client, user.username, pw)


# ── Factory functions ───────────────────────────────────────────


def make_client(user, **overrides):
    """Create and return a Client owned by user."""
    defaults = {
        "company_name": "Test Corp",
        "industry": "Tech",
        "status": "active",
        "user_id": user.id,
    }
    defaults.update(overrides)
    c = Client(**defaults)
    _db.session.add(c)
    _db.session.commit()
    return c


def make_contact(client_obj, user, **overrides):
    """Create and return a Contact linked to client_obj and owned by user."""
    from datetime import date

    defaults = {
        "client_id": client_obj.id,
        "date": date.today(),
        "contact_type": "phone",
        "notes": "Test contact",
        "user_id": user.id,
    }
    defaults.update(overrides)
    c = Contact(**defaults)
    _db.session.add(c)
    _db.session.commit()
    return c


def make_followup(client_obj, user, **overrides):
    """Create and return a FollowUp linked to client_obj and owned by user."""
    from datetime import date

    defaults = {
        "client_id": client_obj.id,
        "due_date": date.today(),
        "priority": "medium",
        "notes": "Test follow-up",
        "user_id": user.id,
    }
    defaults.update(overrides)
    fu = FollowUp(**defaults)
    _db.session.add(fu)
    _db.session.commit()
    return fu
