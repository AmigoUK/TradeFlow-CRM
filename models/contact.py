from datetime import datetime, date

from extensions import db


class Contact(db.Model):
    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.Integer, db.ForeignKey("clients.id"), nullable=False
    )
    date = db.Column(db.Date, nullable=False, default=date.today)
    time = db.Column(db.Time, nullable=True, default=None)
    contact_type = db.Column(db.String(20), nullable=False, default="phone")
    notes = db.Column(db.Text, default="")
    outcome = db.Column(db.String(200), default="")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attachments = db.relationship(
        "Attachment", backref="contact", cascade="all, delete-orphan", lazy=True
    )

    def __repr__(self):
        return f"<Contact {self.contact_type} on {self.date}>"
