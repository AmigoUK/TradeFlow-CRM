from datetime import datetime

from extensions import db

SOCIAL_PLATFORMS = [
    {"value": "linkedin", "label": "LinkedIn", "icon": "bi-linkedin"},
    {"value": "twitter", "label": "Twitter / X", "icon": "bi-twitter-x"},
    {"value": "facebook", "label": "Facebook", "icon": "bi-facebook"},
    {"value": "instagram", "label": "Instagram", "icon": "bi-instagram"},
    {"value": "other", "label": "Other", "icon": "bi-link-45deg"},
]

PLATFORM_ICONS = {p["value"]: p["icon"] for p in SOCIAL_PLATFORMS}


class SocialAccount(db.Model):
    __tablename__ = "social_accounts"

    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(
        db.Integer, db.ForeignKey("contacts.id"), nullable=False
    )
    platform = db.Column(db.String(20), nullable=False, default="other")
    handle = db.Column(db.String(200), default="")
    url = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("contact_id", "platform", name="uq_contact_platform"),
    )

    @property
    def icon(self):
        return PLATFORM_ICONS.get(self.platform, "bi-link-45deg")

    def __repr__(self):
        return f"<SocialAccount {self.platform}: {self.handle}>"
