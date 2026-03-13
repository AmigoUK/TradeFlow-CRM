from datetime import datetime

from extensions import db


class GoogleCalendarSync(db.Model):
    """Links CRM records to Google Calendar events."""
    __tablename__ = "google_calendar_syncs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    followup_id = db.Column(db.Integer, db.ForeignKey("followups.id"), nullable=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("contacts.id"), nullable=True)
    google_event_id = db.Column(db.String(300), nullable=False)
    google_calendar_id = db.Column(db.String(300), nullable=False, default="primary")
    sync_direction = db.Column(db.String(10), nullable=False, default="outbound")
    last_synced_at = db.Column(db.DateTime, default=datetime.utcnow)
    google_etag = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="calendar_syncs")
    followup = db.relationship("FollowUp", backref=db.backref("calendar_sync", uselist=False))
    contact = db.relationship("Contact", backref=db.backref("calendar_sync", uselist=False))

    def __repr__(self):
        return f"<GoogleCalendarSync event={self.google_event_id}>"
