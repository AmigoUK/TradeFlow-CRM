from datetime import datetime
from typing import Optional

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db

ROLES = ["user", "manager", "admin"]

_ROLE_RANK = {role: i for i, role in enumerate(ROLES)}


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    display_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Ownership relationships
    clients = db.relationship("Client", backref="owner", lazy=True)
    contacts = db.relationship("Contact", backref="owner", lazy=True)
    followups = db.relationship("FollowUp", backref="owner", lazy=True)

    @property
    def is_active(self):
        """Flask-Login uses this to refuse login for deactivated users."""
        return self.is_active_user

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def has_role_at_least(self, minimum_role: str) -> bool:
        """Return True if this user's role is >= the given minimum."""
        return _ROLE_RANK.get(self.role, 0) >= _ROLE_RANK.get(minimum_role, 0)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
