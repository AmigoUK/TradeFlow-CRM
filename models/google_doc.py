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
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    interaction_id = db.Column(db.Integer, db.ForeignKey("interactions.id"), nullable=True)
    followup_id = db.Column(db.Integer, db.ForeignKey("followups.id"), nullable=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", backref="google_docs")
    company = db.relationship("Company", backref="google_docs")
    interaction = db.relationship("Interaction", backref="google_docs")
    followup = db.relationship("FollowUp", backref="google_docs")

    def __repr__(self):
        return f"<GoogleDoc {self.title}>"
