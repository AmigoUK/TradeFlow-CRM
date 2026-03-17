from datetime import datetime

from extensions import db


class GoogleDriveFile(db.Model):
    """Links a Google Drive file to a CRM record."""
    __tablename__ = "google_drive_files"

    id = db.Column(db.Integer, primary_key=True)
    google_file_id = db.Column(db.String(300), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    mime_type = db.Column(db.String(100), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    google_url = db.Column(db.String(500), nullable=True)
    thumbnail_url = db.Column(db.String(500), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    interaction_id = db.Column(db.Integer, db.ForeignKey("interactions.id"), nullable=True)
    followup_id = db.Column(db.Integer, db.ForeignKey("followups.id"), nullable=True)
    attachment_id = db.Column(db.Integer, db.ForeignKey("attachments.id"), nullable=True)
    uploaded_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship("User", backref="drive_uploads")
    company = db.relationship("Company", backref="drive_files")
    interaction = db.relationship("Interaction", backref="drive_files")
    followup = db.relationship("FollowUp", backref="drive_files")
    attachment = db.relationship("Attachment", backref=db.backref("drive_file", uselist=False))

    def __repr__(self):
        return f"<GoogleDriveFile {self.filename}>"
