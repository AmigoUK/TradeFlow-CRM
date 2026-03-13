from datetime import datetime

from extensions import db


class GoogleOAuthConfig(db.Model):
    """Singleton model for admin-configured Google OAuth settings."""
    __tablename__ = "google_oauth_config"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(300), nullable=True)
    client_secret_encrypted = db.Column(db.Text, nullable=True)
    scopes = db.Column(db.Text, nullable=False, default="https://www.googleapis.com/auth/userinfo.email")
    is_enabled = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get():
        """Return the singleton config row, auto-creating if missing."""
        config = db.session.get(GoogleOAuthConfig, 1)
        if not config:
            config = GoogleOAuthConfig(id=1)
            db.session.add(config)
            db.session.commit()
        return config

    @property
    def is_configured(self):
        """True if both client_id and client_secret are set."""
        return bool(self.client_id and self.client_secret_encrypted)

    def __repr__(self):
        return f"<GoogleOAuthConfig enabled={self.is_enabled}>"
