from datetime import datetime

from extensions import db

COMPANY_STATUSES = ["lead", "prospect", "active", "inactive"]


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100), default="")
    phone = db.Column(db.String(50), default="")
    email = db.Column(db.String(200), default="")
    contact_person = db.Column(db.String(200), default="")
    status = db.Column(db.String(20), nullable=False, default="lead")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    interactions = db.relationship(
        "Interaction", backref="company", cascade="all, delete-orphan", lazy=True
    )
    followups = db.relationship(
        "FollowUp", backref="company", cascade="all, delete-orphan", lazy=True
    )
    custom_field_values = db.relationship(
        "CustomFieldValue", backref="company", cascade="all, delete-orphan", lazy=True
    )
    attachments = db.relationship(
        "Attachment", backref="company", cascade="all, delete-orphan", lazy=True
    )
    contacts = db.relationship(
        "Contact",
        backref="company",
        foreign_keys="Contact.company_id",
        lazy=True,
    )

    def __repr__(self):
        return f"<Company {self.company_name}>"
