import os
import uuid
from datetime import date, datetime

from flask import abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from blueprints.auth.decorators import can_access_record, role_required
from blueprints.contacts import contacts_bp
from extensions import db
from models import Client, Contact, InteractionType, Attachment, AppSettings
from models.user import User


def _is_ajax():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _ownership_filter(query, model):
    if current_user.has_role_at_least("manager"):
        return query
    return query.filter(model.user_id == current_user.id)


@contacts_bp.route("/")
@login_required
def list_contacts():
    contact_type = request.args.get("type", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    query = Contact.query.join(Client).options(joinedload(Contact.owner))

    # Ownership filter
    query = _ownership_filter(query, Contact)

    if contact_type:
        query = query.filter(Contact.contact_type == contact_type)
    if date_from:
        try:
            query = query.filter(Contact.date >= datetime.strptime(date_from, "%Y-%m-%d").date())
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Contact.date <= datetime.strptime(date_to, "%Y-%m-%d").date())
        except ValueError:
            pass

    settings = AppSettings.get()
    page = request.args.get("page", 1, type=int)
    if settings.pagination_enabled:
        pagination = query.order_by(Contact.date.desc()).paginate(
            page=page, per_page=settings.pagination_size, error_out=False
        )
        contacts = pagination.items
    else:
        pagination = None
        contacts = query.order_by(Contact.date.desc()).all()

    # Pass all_users for reassignment (Manager+)
    all_users = None
    if current_user.has_role_at_least("manager"):
        all_users = User.query.filter_by(is_active_user=True).order_by(User.display_name).all()

    return render_template(
        "contacts/list.html",
        contacts=contacts,
        contact_types=[t.label for t in InteractionType.query.filter_by(is_active=True).order_by(InteractionType.sort_order).all()],
        selected_type=contact_type,
        date_from=date_from,
        date_to=date_to,
        pagination=pagination,
        all_users=all_users,
    )


@contacts_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_contact():
    if request.method == "POST":
        client_id = request.form.get("client_id")
        contact_date = request.form.get("date", "").strip()
        contact_type = request.form.get("contact_type", "phone")

        if not client_id:
            if _is_ajax():
                clients = Client.query.order_by(Client.company_name).all()
                html = render_template(
                    "contacts/_form_fields.html",
                    contact=None,
                    clients=clients,
                    contact_types=[t.label for t in InteractionType.query.filter_by(is_active=True).order_by(InteractionType.sort_order).all()],
                    selected_client_id=None,
                    today=date.today().isoformat(),
                    prefill_notes="",
                    panel_mode=True,
                )
                return jsonify({"ok": False, "html": html})
            flash("Please select a client.", "danger")
            return redirect(url_for("contacts.create_contact"))

        # Verify client ownership
        client = db.get_or_404(Client, int(client_id))
        if not can_access_record(client):
            abort(403)

        try:
            parsed_date = datetime.strptime(contact_date, "%Y-%m-%d").date() if contact_date else date.today()
        except ValueError:
            parsed_date = date.today()

        time_str = request.form.get("time", "").strip()
        parsed_time = None
        if time_str:
            try:
                parsed_time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                pass

        contact = Contact(
            client_id=int(client_id),
            date=parsed_date,
            time=parsed_time,
            contact_type=contact_type,
            notes=request.form.get("notes", "").strip(),
            outcome=request.form.get("outcome", "").strip(),
            user_id=current_user.id,
        )
        db.session.add(contact)
        db.session.flush()

        # Handle optional file attachment
        file = request.files.get("file")
        if file and file.filename:
            description = request.form.get("file_description", "").strip() or None
            _save_contact_file(file, int(client_id), contact.id, description)

        db.session.commit()

        # Google Calendar sync hook
        if "sync_to_google" in request.form:
            try:
                from blueprints.google.google_service import is_google_connected
                if is_google_connected():
                    from blueprints.google.calendar_service import sync_contact_to_calendar
                    sync_contact_to_calendar(contact, current_user.id)
            except Exception:
                pass

        if _is_ajax():
            return jsonify({
                "ok": True,
                "message": "Interaction logged successfully.",
                "redirect": url_for("clients.detail_client", id=contact.client_id),
            })

        flash("Interaction logged successfully.", "success")
        return redirect(url_for("clients.detail_client", id=contact.client_id))

    client_id = request.args.get("client_id")
    prefill_notes = request.args.get("notes", "")
    prefill_date = request.args.get("date", date.today().isoformat())
    clients = Client.query.order_by(Client.company_name).all()

    if _is_ajax():
        return render_template(
            "contacts/_form_fields.html",
            contact=None,
            clients=clients,
            contact_types=[t.label for t in InteractionType.query.filter_by(is_active=True).order_by(InteractionType.sort_order).all()],
            selected_client_id=int(client_id) if client_id else None,
            today=prefill_date,
            prefill_notes=prefill_notes,
            panel_mode=True,
        )

    return render_template(
        "contacts/form.html",
        contact=None,
        clients=clients,
        contact_types=[t.label for t in InteractionType.query.filter_by(is_active=True).order_by(InteractionType.sort_order).all()],
        selected_client_id=int(client_id) if client_id else None,
        today=prefill_date,
        prefill_notes=prefill_notes,
    )


@contacts_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_contact(id):
    contact = db.get_or_404(Contact, id)
    if not can_access_record(contact):
        abort(403)

    if request.method == "POST":
        client_id = request.form.get("client_id")
        contact_date = request.form.get("date", "").strip()

        if not client_id:
            flash("Please select a client.", "danger")
            clients = Client.query.order_by(Client.company_name).all()
            return render_template(
                "contacts/form.html",
                contact=contact,
                clients=clients,
                contact_types=[t.label for t in InteractionType.query.filter_by(is_active=True).order_by(InteractionType.sort_order).all()],
                selected_client_id=contact.client_id,
                today=date.today().isoformat(),
            )

        try:
            contact.date = datetime.strptime(contact_date, "%Y-%m-%d").date() if contact_date else date.today()
        except ValueError:
            contact.date = date.today()

        time_str = request.form.get("time", "").strip()
        if time_str:
            try:
                contact.time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                contact.time = None
        else:
            contact.time = None

        contact.client_id = int(client_id)
        contact.contact_type = request.form.get("contact_type", "phone")
        contact.notes = request.form.get("notes", "").strip()
        contact.outcome = request.form.get("outcome", "").strip()

        # Handle optional file attachment
        file = request.files.get("file")
        if file and file.filename:
            description = request.form.get("file_description", "").strip() or None
            _save_contact_file(file, int(client_id), contact.id, description)

        db.session.commit()

        # Google Calendar sync hook — update synced event
        try:
            from models.google_calendar_sync import GoogleCalendarSync
            sync = GoogleCalendarSync.query.filter_by(
                contact_id=contact.id, user_id=current_user.id
            ).first()
            if sync:
                from blueprints.google.calendar_service import sync_contact_to_calendar
                sync_contact_to_calendar(contact, current_user.id)
        except Exception:
            pass

        flash("Interaction updated successfully.", "success")
        return redirect(url_for("clients.detail_client", id=contact.client_id))

    clients = Client.query.order_by(Client.company_name).all()
    return render_template(
        "contacts/form.html",
        contact=contact,
        clients=clients,
        contact_types=[t.label for t in InteractionType.query.filter_by(is_active=True).order_by(InteractionType.sort_order).all()],
        selected_client_id=contact.client_id,
        today=date.today().isoformat(),
    )


def _save_contact_file(file, client_id, contact_id, description=None):
    """Save an uploaded file and create an Attachment record for a contact."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    client_dir = os.path.join(upload_folder, str(client_id))
    os.makedirs(client_dir, exist_ok=True)

    original_name = secure_filename(file.filename) or "unnamed_file"
    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    file_path = os.path.join(client_dir, stored_name)
    file.save(file_path)

    attachment = Attachment(
        filename=original_name,
        stored_filename=stored_name,
        description=description,
        file_size=os.path.getsize(file_path),
        mime_type=file.content_type or "",
        client_id=client_id,
        contact_id=contact_id,
    )
    db.session.add(attachment)


@contacts_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_contact(id):
    contact = db.get_or_404(Contact, id)
    if not can_access_record(contact):
        abort(403)
    client_id = contact.client_id

    # Google Calendar sync hook — delete synced event
    try:
        from models.google_calendar_sync import GoogleCalendarSync
        sync = GoogleCalendarSync.query.filter_by(
            contact_id=contact.id, user_id=current_user.id
        ).first()
        if sync:
            from blueprints.google.calendar_service import delete_calendar_event
            delete_calendar_event(sync, current_user.id)
    except Exception:
        pass

    db.session.delete(contact)
    db.session.commit()
    flash("Interaction deleted successfully.", "success")
    return redirect(url_for("clients.detail_client", id=client_id))


@contacts_bp.route("/<int:id>/reassign", methods=["POST"])
@role_required("manager")
def reassign_contact(id):
    contact = db.get_or_404(Contact, id)
    data = request.get_json(silent=True) or {}
    target_user_id = data.get("target_user_id")
    if not target_user_id:
        return jsonify({"ok": False, "error": "Target user is required."}), 400
    target_user = db.get_or_404(User, int(target_user_id))
    contact.user_id = target_user.id
    db.session.commit()
    return jsonify({"ok": True, "message": f"Interaction reassigned to {target_user.display_name}."})


@contacts_bp.route("/bulk-reassign", methods=["POST"])
@role_required("manager")
def bulk_reassign_contacts():
    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])
    target_user_id = data.get("target_user_id")
    if not ids or not target_user_id:
        return jsonify({"ok": False, "error": "IDs and target user are required."}), 400
    target_user = db.get_or_404(User, int(target_user_id))
    Contact.query.filter(Contact.id.in_(ids)).update({"user_id": target_user.id})
    db.session.commit()
    return jsonify({"ok": True, "message": f"{len(ids)} interaction(s) reassigned to {target_user.display_name}."})
