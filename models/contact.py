from datetime import datetime, date

from extensions import db

CONTACT_TYPES = ["phone", "email", "meeting"]


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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Contact {self.contact_type} on {self.date}>"
