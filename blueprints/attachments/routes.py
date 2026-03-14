import os
import uuid

from flask import abort, current_app, flash, jsonify, redirect, request, send_from_directory, url_for
from flask_login import login_required
from werkzeug.utils import secure_filename

from blueprints.auth.decorators import can_access_record
from blueprints.attachments import attachments_bp
from extensions import db
from models import Attachment, AttachmentTag, Client


def _is_ajax():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _check_attachment_access(attachment):
    """Verify the current user can access the parent record of this attachment."""
    parent = db.session.get(Client, attachment.client_id)
    if parent and not can_access_record(parent):
        abort(403)


def _save_file(file, client_id):
    """Save uploaded file to disk and return (stored_filename, file_size, mime_type)."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    client_dir = os.path.join(upload_folder, str(client_id))
    os.makedirs(client_dir, exist_ok=True)

    original_name = secure_filename(file.filename)
    if not original_name:
        original_name = "unnamed_file"
    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    file_path = os.path.join(client_dir, stored_name)
    file.save(file_path)

    file_size = os.path.getsize(file_path)
    mime_type = file.content_type or ""

    return stored_name, file_size, mime_type, original_name


@attachments_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    client_id = request.form.get("client_id")

    if not file or not file.filename:
        flash("No file selected.", "danger")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    if not client_id:
        flash("Client is required.", "danger")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    client_id = int(client_id)

    # Verify parent record access
    parent = db.get_or_404(Client, client_id)
    if not can_access_record(parent):
        abort(403)

    contact_id = request.form.get("contact_id")
    followup_id = request.form.get("followup_id")
    storage_type = request.form.get("storage_type", "local")

    # Google Drive upload path
    if storage_type == "drive":
        try:
            from blueprints.google.google_service import is_google_connected
            from flask_login import current_user as cu
            if is_google_connected():
                from blueprints.google.drive_service import upload_file_to_drive
                mime_type = file.content_type or "application/octet-stream"
                file_id, web_url = upload_file_to_drive(file, file.filename, mime_type, cu.id)
                if file_id:
                    from models.google_drive_file import GoogleDriveFile
                    original_name = secure_filename(file.filename) or "unnamed_file"
                    attachment = Attachment(
                        filename=original_name,
                        stored_filename=f"drive:{file_id}",
                        description=request.form.get("description", "").strip() or None,
                        file_size=0,
                        mime_type=mime_type,
                        client_id=client_id,
                        contact_id=int(contact_id) if contact_id else None,
                        followup_id=int(followup_id) if followup_id else None,
                        category_id=int(request.form.get("category_id")) if request.form.get("category_id") else None,
                        storage_type="drive",
                    )
                    db.session.add(attachment)
                    db.session.flush()
                    drive_file = GoogleDriveFile(
                        google_file_id=file_id,
                        filename=original_name,
                        mime_type=mime_type,
                        google_url=web_url,
                        client_id=client_id,
                        attachment_id=attachment.id,
                        uploaded_by_user_id=cu.id,
                    )
                    db.session.add(drive_file)
                    db.session.commit()
                    if _is_ajax():
                        return jsonify({"ok": True, "message": f"File '{original_name}' uploaded to Google Drive."})
                    flash(f"File '{original_name}' uploaded to Google Drive.", "success")
                    return redirect(request.referrer or url_for("clients.detail_client", id=client_id))
        except Exception as e:
            current_app.logger.warning("Google Drive upload failed: %s", e)
        flash("Failed to upload to Google Drive. Saving locally instead.", "warning")

    stored_name, file_size, mime_type, original_name = _save_file(file, client_id)

    description = request.form.get("description", "").strip() or None
    category_id = request.form.get("category_id")
    tag_ids = request.form.getlist("tag_ids")

    attachment = Attachment(
        filename=original_name,
        stored_filename=stored_name,
        description=description,
        file_size=file_size,
        mime_type=mime_type,
        client_id=client_id,
        contact_id=int(contact_id) if contact_id else None,
        followup_id=int(followup_id) if followup_id else None,
        category_id=int(category_id) if category_id else None,
    )
    if tag_ids:
        tags = AttachmentTag.query.filter(AttachmentTag.id.in_([int(t) for t in tag_ids])).all()
        attachment.tags = tags
    db.session.add(attachment)
    db.session.commit()

    if _is_ajax():
        return jsonify({
            "ok": True,
            "message": f"File '{original_name}' uploaded successfully.",
        })

    flash(f"File '{original_name}' uploaded successfully.", "success")
    return redirect(request.referrer or url_for("clients.detail_client", id=client_id))


@attachments_bp.route("/<int:id>/download")
@login_required
def download(id):
    attachment = db.get_or_404(Attachment, id)
    _check_attachment_access(attachment)
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    client_dir = os.path.join(upload_folder, str(attachment.client_id))
    return send_from_directory(
        client_dir,
        attachment.stored_filename,
        download_name=attachment.filename,
        as_attachment=True,
    )


@attachments_bp.route("/<int:id>/view")
@login_required
def view(id):
    attachment = db.get_or_404(Attachment, id)
    _check_attachment_access(attachment)
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    client_dir = os.path.join(upload_folder, str(attachment.client_id))
    return send_from_directory(
        client_dir,
        attachment.stored_filename,
        download_name=attachment.filename,
        as_attachment=False,
    )


@attachments_bp.route("/<int:id>/edit", methods=["POST"])
@login_required
def edit(id):
    attachment = db.get_or_404(Attachment, id)
    _check_attachment_access(attachment)

    description = request.form.get("description", "").strip() or None
    category_id = request.form.get("category_id")
    tag_ids = request.form.getlist("tag_ids")

    attachment.description = description
    attachment.category_id = int(category_id) if category_id else None

    tags = AttachmentTag.query.filter(AttachmentTag.id.in_([int(t) for t in tag_ids])).all() if tag_ids else []
    attachment.tags = tags

    db.session.commit()

    if _is_ajax():
        return jsonify({"ok": True, "message": f"Attachment '{attachment.display_name}' updated."})

    flash(f"Attachment '{attachment.display_name}' updated.", "success")
    return redirect(request.referrer or url_for("clients.detail_client", id=attachment.client_id))


@attachments_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    attachment = db.get_or_404(Attachment, id)
    _check_attachment_access(attachment)
    client_id = attachment.client_id
    filename = attachment.filename

    # Delete file from disk
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, str(client_id), attachment.stored_filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(attachment)
    db.session.commit()

    if _is_ajax():
        return jsonify({"ok": True, "message": f"File '{filename}' deleted."})

    flash(f"File '{filename}' deleted.", "success")
    return redirect(request.referrer or url_for("clients.detail_client", id=client_id))
