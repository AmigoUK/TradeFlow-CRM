from datetime import datetime, date

from extensions import db

PRIORITIES = ["high", "medium", "low"]


class FollowUp(db.Model):
    __tablename__ = "followups"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.Integer, db.ForeignKey("clients.id"), nullable=False
    )
    due_date = db.Column(db.Date, nullable=False, default=date.today)
    due_time = db.Column(db.Time, nullable=True, default=None)
    priority = db.Column(db.String(10), nullable=False, default="medium")
    completed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, default="")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    meet_link = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attachments = db.relationship(
        "Attachment", backref="followup", cascade="all, delete-orphan", lazy=True
    )

    @property
    def is_overdue(self):
        return not self.completed and self.due_date < date.today()

    def __repr__(self):
        return f"<FollowUp due {self.due_date} priority={self.priority}>"
