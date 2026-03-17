"""Google Drive routes — upload, browse, link, unlink, share."""

from flask import flash, jsonify, redirect, request, url_for
from flask_login import current_user, login_required

from blueprints.auth.decorators import can_access_record
from blueprints.google import google_bp
from blueprints.google.drive_service import (
    list_drive_files,
    set_file_sharing,
    upload_file_to_drive,
)
from blueprints.google.google_service import google_required
from extensions import db
from models import Attachment, Company
from models.google_drive_file import GoogleDriveFile


@google_bp.route("/drive/upload", methods=["POST"])
@login_required
@google_required
def drive_upload():
    """Upload a file to Google Drive and optionally create a CRM attachment."""
    file = request.files.get("file")
    company_id = request.form.get("company_id")
    interaction_id = request.form.get("interaction_id")
    followup_id = request.form.get("followup_id")

    if not file or not file.filename:
        flash("No file selected.", "danger")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    if not company_id:
        flash("Company is required.", "danger")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    company_id = int(company_id)
    parent = db.get_or_404(Company, company_id)
    if not can_access_record(parent):
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    mime_type = file.content_type or "application/octet-stream"
    file_id, web_url = upload_file_to_drive(file, file.filename, mime_type, current_user.id)

    if not file_id:
        flash("Failed to upload to Google Drive.", "danger")
        return redirect(request.referrer or url_for("companies.detail_company", id=company_id))

    # Create Attachment record with storage_type="drive"
    attachment = Attachment(
        filename=file.filename,
        stored_filename=f"drive:{file_id}",
        description=request.form.get("description", "").strip() or None,
        file_size=0,
        mime_type=mime_type,
        company_id=company_id,
        interaction_id=int(interaction_id) if interaction_id else None,
        followup_id=int(followup_id) if followup_id else None,
        storage_type="drive",
    )
    db.session.add(attachment)
    db.session.flush()

    # Create Drive file record
    drive_file = GoogleDriveFile(
        google_file_id=file_id,
        filename=file.filename,
        mime_type=mime_type,
        google_url=web_url,
        company_id=company_id,
        interaction_id=int(interaction_id) if interaction_id else None,
        followup_id=int(followup_id) if followup_id else None,
        attachment_id=attachment.id,
        uploaded_by_user_id=current_user.id,
    )
    db.session.add(drive_file)
    db.session.commit()

    flash(f"File '{file.filename}' uploaded to Google Drive.", "success")
    return redirect(request.referrer or url_for("companies.detail_company", id=company_id))


@google_bp.route("/drive/browse")
@login_required
@google_required
def drive_browse():
    """JSON: list Drive files for picker modal."""
    page_token = request.args.get("page_token")
    files, next_token = list_drive_files(current_user.id, page_token=page_token)

    return jsonify({
        "files": [{
            "id": f.get("id"),
            "name": f.get("name"),
            "mimeType": f.get("mimeType"),
            "size": f.get("size"),
            "webViewLink": f.get("webViewLink"),
            "thumbnailLink": f.get("thumbnailLink"),
            "createdTime": f.get("createdTime"),
        } for f in files],
        "nextPageToken": next_token,
    })


@google_bp.route("/drive/link", methods=["POST"])
@login_required
@google_required
def drive_link():
    """Link an existing Google Drive file to a CRM record."""
    google_file_id = request.form.get("google_file_id", "").strip()
    filename = request.form.get("filename", "").strip() or "Linked File"
    google_url = request.form.get("google_url", "").strip()
    mime_type = request.form.get("mime_type", "")
    company_id = request.form.get("company_id")
    interaction_id = request.form.get("interaction_id")
    followup_id = request.form.get("followup_id")

    if not google_file_id or not company_id:
        flash("File ID and company are required.", "danger")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    company_id = int(company_id)

    drive_file = GoogleDriveFile(
        google_file_id=google_file_id,
        filename=filename,
        mime_type=mime_type,
        google_url=google_url,
        company_id=company_id,
        interaction_id=int(interaction_id) if interaction_id else None,
        followup_id=int(followup_id) if followup_id else None,
        uploaded_by_user_id=current_user.id,
    )
    db.session.add(drive_file)
    db.session.commit()

    flash(f"File '{filename}' linked from Google Drive.", "success")
    return redirect(url_for("companies.detail_company", id=company_id))


@google_bp.route("/drive/<int:id>/unlink", methods=["POST"])
@login_required
def drive_unlink(id):
    """Remove a Drive file link from CRM (does not delete from Google)."""
    drive_file = db.get_or_404(GoogleDriveFile, id)
    company_id = drive_file.company_id
    filename = drive_file.filename
    db.session.delete(drive_file)
    db.session.commit()

    flash(f"File '{filename}' unlinked.", "success")
    if company_id:
        return redirect(url_for("companies.detail_company", id=company_id))
    return redirect(request.referrer or url_for("dashboard.dashboard"))


@google_bp.route("/drive/<int:id>/share", methods=["POST"])
@login_required
@google_required
def drive_share(id):
    """Set sharing permissions on a Drive file."""
    drive_file = db.get_or_404(GoogleDriveFile, id)

    if set_file_sharing(drive_file.google_file_id, user_id=current_user.id):
        flash(f"Sharing enabled for '{drive_file.filename}'.", "success")
    else:
        flash("Failed to set sharing permissions.", "danger")

    if drive_file.company_id:
        return redirect(url_for("companies.detail_company", id=drive_file.company_id))
    return redirect(request.referrer or url_for("dashboard.dashboard"))
