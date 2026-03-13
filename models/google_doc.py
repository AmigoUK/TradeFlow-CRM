from datetime import datetime

from extensions import db


class GoogleDoc(db.Model):
    """Links a Google Document to a CRM record."""
    __tablename__ = "google_docs"

    id = db.Column(db.Integer, primary_key=True)
    google_doc_id = db.Column(db.String(300), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    google_url = db.Column(db.String(500), nullable=True)
    doc_type = db.Column(db.String(20), nullable=False, default="document")
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("contacts.id"), nullable=True)
    followup_id = db.Column(db.Integer, db.ForeignKey("followups.id"), nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", backref="google_docs")
    client = db.relationship("Client", backref="google_docs")
    contact = db.relationship("Contact", backref="google_docs")
    followup = db.relationship("FollowUp", backref="google_docs")

    def __repr__(self):
        return f"<GoogleDoc {self.title}>"
