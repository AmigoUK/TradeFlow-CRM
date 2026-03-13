from datetime import datetime

from extensions import db


class DocTemplate(db.Model):
    """Template configuration for creating Google Docs from CRM."""
    __tablename__ = "doc_templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    google_template_doc_id = db.Column(db.String(300), nullable=False)
    template_type = db.Column(db.String(20), nullable=False, default="meeting_notes")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DocTemplate {self.name}>"
