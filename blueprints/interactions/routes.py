import os
import uuid
from datetime import date, datetime

from flask import abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from blueprints.auth.decorators import can_access_record, role_required
from blueprints.interactions import interactions_bp
from extensions import db
from models import Company, Interaction, InteractionType, Attachment, AppSettings, Contact
from models.user import User


def _is_ajax():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _ownership_filter(query, model):
    if current_user.has_role_at_least("manager"):
        return query
    return query.filter(model.user_id == current_user.id)


@interactions_bp.route("/")
@login_required
def list_interactions():
    interaction_type = request.args.get("type", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    query = Interaction.query.join(Company).options(joinedload(Interaction.owner))

    # Ownership filter
    query = _ownership_filter(query, Interaction)

    if interaction_type:
        query = query.filter(Interaction.interaction_type == interaction_type)
    if date_from:
        try:
            query = query.filter(Interaction.date >= datetime.strptime(date_from, "%Y-%m-%d").date())
        except ValueError:
            pass
    if date_to:
        try:
            query = query.filter(Interaction.date <= datetime.strptime(date_to, "%Y-%m-%d").date())
        except ValueError:
            pass

    settings = AppSettings.get()
    page = request.args.get("page", 1, type=int)
    if settings.pagination_enabled:
        pagination = query.order_by(Interaction.date.desc()).paginate(
            page=page, per_page=settings.pagination_size, error_out=False
        )
        interactions = pagination.items
    else:
        pagination = None
        interactions = query.order_by(Interaction.date.desc()).all()

    # Pass all_users for reassignment (Manager+)
    all_users = None
    if current_user.has_role_at_least("manager"):
        all_users = User.query.filter_by(is_active_user=True).order_by(User.display_name).all()

    return render_template(
        "interactions/list.html",
        interactions=interactions,
        interaction_types=[t.label for t in InteractionType.query.filter_by(is_active=True).order_by(InteractionType.sort_order).all()],
        selected_type=interaction_type,
        date_from=date_from,
        date_to=date_to,
        pagination=pagination,
        all_users=all_users,
    )


@interactions_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_interaction():
    if request.method == "POST":
        company_id = request.form.get("company_id")
        interaction_date = request.form.get("date", "").strip()
        interaction_type = request.form.get("interaction_type", "phone")

        if not company_id:
            if _is_ajax():
                companies = Company.query.order_by(Company.company_name).all()
                html = render_template(
                    "interactions/_form_fields.html",
                    interaction=None,
                    companies=companies,
                    interaction_types=[t.label for t in InteractionType.query.filter_by(is_active=True).order_by(InteractionType.sort_order).all()],
                    selected_company_id=None,
                    today=date.today().isoformat(),
                    prefill_notes="",
                    panel_mode=True,
                )
                return jsonify({"ok": False, "html": html})
            flash("Please select a company.", "danger")
            return redirect(url_for("interactions.create_interaction"))

        # Verify company ownership
        company = db.get_or_404(Company, int(company_id))
        if not can_access_record(company):
            abort(403)

        try:
            parsed_date = datetime.strptime(interaction_date, "%Y-%m-%d").date() if interaction_date else date.today()
        except ValueError:
            parsed_date = date.today()

        time_str = request.form.get("time", "").strip()
        parsed_time = None
        if time_str:
            try:
                parsed_time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                pass

        contact_id = request.form.get("contact_id")

        interaction = Interaction(
            company_id=int(company_id),
            contact_id=int(contact_id) if contact_id else None,
            date=parsed_date,
            time=parsed_time,
            interaction_type=interaction_type,
            notes=request.form.get("notes", "").strip(),
            outcome=request.form.get("outcome", "").strip(),
            user_id=current_user.id,
        )
        db.session.add(interaction)
        db.session.flush()

        # Handle optional file attachment
        file = request.files.get("file")
        if file and file.filename:
            description = request.form.get("file_description", "").strip() or None
            _save_interaction_file(file, int(company_id), interaction.id, description)

        db.session.commit()

        # Google Calendar sync hook
        if "sync_to_google" in request.form:
            try:
                from blueprints.google.google_service import is_google_connected
                if is_google_connected():
                    from blueprints.google.calendar_service import sync_interaction_to_calendar
                    sync_interaction_to_calendar(interaction, current_user.id)
            except Exception:
                pass

        if _is_ajax():
            return jsonify({
                "ok": True,
                "message": "Interaction logged successfully.",
                "redirect": url_for("companies.detail_company", id=interaction.company_id),
            })

        flash("Interaction logged successfully.", "success")
        return redirect(url_for("companies.detail_company", id=interaction.company_id))

    company_id = request.args.get("company_id")
    prefill_notes = request.args.get("notes", "")
    prefill_date = request.args.get("date", date.today().isoformat())
    companies = Company.query.order_by(Company.company_name).all()

    # Get contacts for selected company
    company_contacts = []
    if company_id:
        company_contacts = Contact.query.filter_by(company_id=int(company_id)).order_by(
            Contact.is_primary.desc(), Contact.first_name
        ).all()

    if _is_ajax():
        return render_template(
            "interactions/_form_fields.html",
            interaction=None,
            companies=companies,
            interaction_types=[t.label for t in InteractionType.query.filter_by(is_active=True).order_by(InteractionType.sort_order).all()],
            selected_company_id=int(company_id) if company_id else None,
            today=prefill_date,
            prefill_notes=prefill_notes,
            company_contacts=company_contacts,
            panel_mode=True,
        )

    return render_template(
        "interactions/form.html",
        interaction=None,
        companies=companies,
        interaction_types=[t.label for t in InteractionType.query.filter_by(is_active=True).order_by(InteractionType.sort_order).all()],
        selected_company_id=int(company_id) if company_id else None,
        today=prefill_date,
        prefill_notes=prefill_notes,
        company_contacts=company_contacts,
    )


@interactions_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_interaction(id):
    interaction = db.get_or_404(Interaction, id)
    if not can_access_record(interaction):
        abort(403)

    if request.method == "POST":
        company_id = request.form.get("company_id")
        interaction_date = request.form.get("date", "").strip()

        if not company_id:
            flash("Please select a company.", "danger")
            companies = Company.query.order_by(Company.company_name).all()
            return render_template(
                "interactions/form.html",
                interaction=interaction,
                companies=companies,
                interaction_types=[t.label for t in InteractionType.query.filter_by(is_active=True).order_by(InteractionType.sort_order).all()],
                selected_company_id=interaction.company_id,
                today=date.today().isoformat(),
            )

        try:
            interaction.date = datetime.strptime(interaction_date, "%Y-%m-%d").date() if interaction_date else date.today()
        except ValueError:
            interaction.date = date.today()

        time_str = request.form.get("time", "").strip()
        if time_str:
            try:
                interaction.time = datetime.strptime(time_str, "%H:%M").time()
            except ValueError:
                interaction.time = None
        else:
            interaction.time = None

        contact_id = request.form.get("contact_id")
        interaction.company_id = int(company_id)
        interaction.contact_id = int(contact_id) if contact_id else None
        interaction.interaction_type = request.form.get("interaction_type", "phone")
        interaction.notes = request.form.get("notes", "").strip()
        interaction.outcome = request.form.get("outcome", "").strip()

        # Handle optional file attachment
        file = request.files.get("file")
        if file and file.filename:
            description = request.form.get("file_description", "").strip() or None
            _save_interaction_file(file, int(company_id), interaction.id, description)

        db.session.commit()

        # Google Calendar sync hook — update synced event
        try:
            from models.google_calendar_sync import GoogleCalendarSync
            sync = GoogleCalendarSync.query.filter_by(
                interaction_id=interaction.id, user_id=current_user.id
            ).first()
            if sync:
                from blueprints.google.calendar_service import sync_interaction_to_calendar
                sync_interaction_to_calendar(interaction, current_user.id)
        except Exception:
            pass

        flash("Interaction updated successfully.", "success")
        return redirect(url_for("companies.detail_company", id=interaction.company_id))

    companies = Company.query.order_by(Company.company_name).all()
    company_contacts = Contact.query.filter_by(company_id=interaction.company_id).order_by(
        Contact.is_primary.desc(), Contact.first_name
    ).all()
    return render_template(
        "interactions/form.html",
        interaction=interaction,
        companies=companies,
        interaction_types=[t.label for t in InteractionType.query.filter_by(is_active=True).order_by(InteractionType.sort_order).all()],
        selected_company_id=interaction.company_id,
        today=date.today().isoformat(),
        company_contacts=company_contacts,
    )


def _save_interaction_file(file, company_id, interaction_id, description=None):
    """Save an uploaded file and create an Attachment record for an interaction."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    company_dir = os.path.join(upload_folder, str(company_id))
    os.makedirs(company_dir, exist_ok=True)

    original_name = secure_filename(file.filename) or "unnamed_file"
    stored_name = f"{uuid.uuid4().hex}_{original_name}"
    file_path = os.path.join(company_dir, stored_name)
    file.save(file_path)

    attachment = Attachment(
        filename=original_name,
        stored_filename=stored_name,
        description=description,
        file_size=os.path.getsize(file_path),
        mime_type=file.content_type or "",
        company_id=company_id,
        interaction_id=interaction_id,
    )
    db.session.add(attachment)


@interactions_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_interaction(id):
    interaction = db.get_or_404(Interaction, id)
    if not can_access_record(interaction):
        abort(403)
    company_id = interaction.company_id

    # Google Calendar sync hook — delete synced event
    try:
        from models.google_calendar_sync import GoogleCalendarSync
        sync = GoogleCalendarSync.query.filter_by(
            interaction_id=interaction.id, user_id=current_user.id
        ).first()
        if sync:
            from blueprints.google.calendar_service import delete_calendar_event
            delete_calendar_event(sync, current_user.id)
    except Exception:
        pass

    db.session.delete(interaction)
    db.session.commit()
    flash("Interaction deleted successfully.", "success")
    return redirect(url_for("companies.detail_company", id=company_id))


@interactions_bp.route("/<int:id>/reassign", methods=["POST"])
@role_required("manager")
def reassign_interaction(id):
    interaction = db.get_or_404(Interaction, id)
    data = request.get_json(silent=True) or {}
    target_user_id = data.get("target_user_id")
    if not target_user_id:
        return jsonify({"ok": False, "error": "Target user is required."}), 400
    target_user = db.get_or_404(User, int(target_user_id))
    interaction.user_id = target_user.id
    db.session.commit()
    return jsonify({"ok": True, "message": f"Interaction reassigned to {target_user.display_name}."})


@interactions_bp.route("/bulk-reassign", methods=["POST"])
@role_required("manager")
def bulk_reassign_interactions():
    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])
    target_user_id = data.get("target_user_id")
    if not ids or not target_user_id:
        return jsonify({"ok": False, "error": "IDs and target user are required."}), 400
    target_user = db.get_or_404(User, int(target_user_id))
    Interaction.query.filter(Interaction.id.in_(ids)).update({"user_id": target_user.id})
    db.session.commit()
    return jsonify({"ok": True, "message": f"{len(ids)} interaction(s) reassigned to {target_user.display_name}."})
