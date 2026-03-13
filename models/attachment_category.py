from datetime import datetime

from extensions import db

DEFAULT_ATTACHMENT_CATEGORIES = [
    {"label": "Contract", "icon": "bi-file-earmark-text", "colour": "#0d6efd"},
    {"label": "Invoice", "icon": "bi-receipt", "colour": "#198754"},
    {"label": "Proposal", "icon": "bi-file-earmark-richtext", "colour": "#6f42c1"},
    {"label": "Other", "icon": "bi-folder", "colour": "#6c757d"},
]


class AttachmentCategory(db.Model):
    __tablename__ = "attachment_categories"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), nullable=False, unique=True)
    icon = db.Column(db.String(50), nullable=False, default="bi-folder")
    colour = db.Column(db.String(7), nullable=False, default="#6c757d")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attachments = db.relationship("Attachment", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<AttachmentCategory {self.label}>"
