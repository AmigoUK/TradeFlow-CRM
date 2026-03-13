from datetime import datetime

from extensions import db

DEFAULT_ATTACHMENT_TAGS = [
    {"label": "Important", "colour": "#dc3545"},
    {"label": "Archived", "colour": "#6c757d"},
    {"label": "Pending", "colour": "#ffc107"},
]

attachment_tag_map = db.Table(
    "attachment_tag_map",
    db.Column("attachment_id", db.Integer, db.ForeignKey("attachments.id"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("attachment_tags.id"), primary_key=True),
)


class AttachmentTag(db.Model):
    __tablename__ = "attachment_tags"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), nullable=False, unique=True)
    colour = db.Column(db.String(7), nullable=False, default="#6c757d")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AttachmentTag {self.label}>"
