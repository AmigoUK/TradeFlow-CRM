from datetime import datetime

from extensions import db

CLIENT_STATUSES = ["lead", "prospect", "active", "inactive"]


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(100), default="")
    phone = db.Column(db.String(50), default="")
    email = db.Column(db.String(200), default="")
    contact_person = db.Column(db.String(200), default="")
    status = db.Column(db.String(20), nullable=False, default="lead")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    contacts = db.relationship(
        "Contact", backref="client", cascade="all, delete-orphan", lazy=True
    )
    followups = db.relationship(
        "FollowUp", backref="client", cascade="all, delete-orphan", lazy=True
    )

    def __repr__(self):
        return f"<Client {self.company_name}>"
