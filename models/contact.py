from datetime import datetime

from extensions import db


class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), default="")
    email = db.Column(db.String(200), default="")
    phone = db.Column(db.String(50), default="")
    job_title = db.Column(db.String(200), default="")
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=True
    )
    previous_company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=True
    )
    is_primary = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, default="")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    previous_company = db.relationship(
        "Company",
        foreign_keys=[previous_company_id],
        backref="former_contacts",
    )
    social_accounts = db.relationship(
        "SocialAccount", backref="contact", cascade="all, delete-orphan", lazy=True
    )
    interactions = db.relationship(
        "Interaction", backref="contact_person", lazy=True
    )
    followups = db.relationship(
        "FollowUp", backref="contact_person", lazy=True
    )

    @property
    def full_name(self):
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p)

    def __repr__(self):
        return f"<Contact {self.full_name}>"
