from datetime import datetime, date

from extensions import db


class Interaction(db.Model):
    __tablename__ = "interactions"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer, db.ForeignKey("companies.id"), nullable=False
    )
    contact_id = db.Column(
        db.Integer, db.ForeignKey("contacts.id"), nullable=True
    )
    date = db.Column(db.Date, nullable=False, default=date.today)
    time = db.Column(db.Time, nullable=True, default=None)
    interaction_type = db.Column(db.String(20), nullable=False, default="phone")
    notes = db.Column(db.Text, default="")
    outcome = db.Column(db.String(200), default="")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    meet_link = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attachments = db.relationship(
        "Attachment", backref="interaction", cascade="all, delete-orphan", lazy=True
    )

    def __repr__(self):
        return f"<Interaction {self.interaction_type} on {self.date}>"
