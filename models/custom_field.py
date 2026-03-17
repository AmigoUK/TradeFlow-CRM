from datetime import datetime

from extensions import db

DEFAULT_CUSTOM_FIELDS = [
    {"label": "Address", "field_type": "textarea", "icon": "bi-geo-alt"},
    {"label": "LinkedIn", "field_type": "url", "icon": "bi-linkedin"},
    {"label": "Twitter / X", "field_type": "url", "icon": "bi-twitter-x"},
]


class CustomFieldDefinition(db.Model):
    __tablename__ = "custom_field_definitions"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    field_type = db.Column(db.String(20), nullable=False, default="text")
    icon = db.Column(db.String(50), default="bi-input-cursor-text")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    values = db.relationship(
        "CustomFieldValue", backref="definition", cascade="all, delete-orphan", lazy=True
    )

    def __repr__(self):
        return f"<CustomFieldDefinition {self.label}>"


class CustomFieldValue(db.Model):
    __tablename__ = "custom_field_values"

    id = db.Column(db.Integer, primary_key=True)
    definition_id = db.Column(
        db.Integer, db.ForeignKey("custom_field_definitions.id"), nullable=False
    )
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=False
    )
    value = db.Column(db.Text, default="")

    __table_args__ = (
        db.UniqueConstraint("definition_id", "company_id", name="uq_field_company"),
    )

    def __repr__(self):
        return f"<CustomFieldValue def={self.definition_id} company={self.company_id}>"
