from datetime import datetime

from extensions import db


class GoogleCredential(db.Model):
    """Per-user OAuth2 tokens for Google API access."""
    __tablename__ = "google_credentials"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    access_token_encrypted = db.Column(db.Text, nullable=True)
    refresh_token_encrypted = db.Column(db.Text, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    granted_scopes = db.Column(db.Text, nullable=True)
    google_email = db.Column(db.String(200), nullable=True)
    is_valid = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("google_credential", uselist=False))

    def __repr__(self):
        return f"<GoogleCredential user_id={self.user_id} email={self.google_email}>"
