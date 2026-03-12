import os
import shutil
from datetime import date, datetime

from flask import abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from blueprints.auth.decorators import can_access_record, role_required
from blueprints.clients import clients_bp
from extensions import db
from models import Client, CLIENT_STATUSES, Contact, FollowUp, QuickFunction, InteractionType, CustomFieldDefinition, CustomFieldValue, Attachment, AttachmentCategory, AttachmentTag, AppSettings
from models.user import User


def _is_ajax():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _ownership_filter(query, model):
    if current_user.has_role_at_least("manager"):
        return query
    return query.filter(model.user_id == current_user.id)


@clients_bp.route("/")
@login_required
def list_clients():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    view = request.args.get("view", "table")

    # Subqueries for last contact and next follow-up per client
    last_contact_sq = (
        db.session.query(
            Contact.client_id,
            func.max(Contact.date).label("last_contact"),
        )
        .group_by(Contact.client_id)
        .subquery()
    )

    next_followup_sq = (
        db.session.query(
            FollowUp.client_id,
            func.min(FollowUp.due_date).label("next_followup"),
        )
        .filter(FollowUp.completed == False)  # noqa: E712
        .group_by(FollowUp.client_id)
        .subquery()
    )

    query = (
        db.session.query(
            Client,
            last_contact_sq.c.last_contact,
            next_followup_sq.c.next_followup,
        )
        .outerjoin(last_contact_sq, Client.id == last_contact_sq.c.client_id)
        .outerjoin(next_followup_sq, Client.id == next_followup_sq.c.client_id)
        .options(joinedload(Client.owner))
    )

    # Ownership filter
    if not current_user.has_role_at_least("manager"):
        query = query.filter(Client.user_id == current_user.id)

    if q:
        query = query.filter(Client.company_name.ilike(f"%{q}%"))
    if status and view != "board":
        query = query.filter(Client.status == status)

    settings = AppSettings.get()
    page = request.args.get("page", 1, type=int)
    ordered = query.order_by(Client.company_name)

    if settings.pagination_enabled and view != "board":
        pagination = ordered.paginate(page=page, per_page=settings.pagination_size, error_out=False)
        results = pagination.items
    else:
        pagination = None
        results = ordered.all()

    # Attach computed dates to client objects for template access
    clients = []
    for client, last_contact, next_followup in results:
        client.last_contact = last_contact
        client.next_followup = next_followup
        clients.append(client)

    active_qfs = QuickFunction.query.filter_by(is_active=True).order_by(
        QuickFunction.sort_order
    ).all()

    # Pass all_users for reassignment (Manager+)
    all_users = None
    if current_user.has_role_at_least("manager"):
        all_users = User.query.filter_by(is_active_user=True).order_by(User.display_name).all()

    return render_template(
        "clients/list.html",
        clients=clients,
        statuses=CLIENT_STATUSES,
        q=q,
        status=status,
        view=view,
        quick_functions=[qf.to_dict() for qf in active_qfs],
        pagination=pagination,
        all_users=all_users,
    )


@clients_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_client():
    active_custom_fields = CustomFieldDefinition.query.filter_by(is_active=True).order_by(
        CustomFieldDefinition.sort_order
    ).all()

    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        if not company_name:
            if _is_ajax():
                html = render_template(
                    "clients/_form_fields.html",
                    client=None,
                    statuses=CLIENT_STATUSES,
                    custom_fields=active_custom_fields,
                    custom_values={},
                    panel_mode=True,
                )
                return jsonify({"ok": False, "html": html})
            flash("Company name is required.", "danger")
            return render_template(
                "clients/form.html",
                client=None,
                statuses=CLIENT_STATUSES,
                custom_fields=active_custom_fields,
                custom_values={},
            )

        client = Client(
            company_name=company_name,
            industry=request.form.get("industry", "").strip(),
            phone=request.form.get("phone", "").strip(),
            email=request.form.get("email", "").strip(),
            contact_person=request.form.get("contact_person", "").strip(),
            status=request.form.get("status", "lead"),
            user_id=current_user.id,
        )
        db.session.add(client)
        db.session.flush()

        # Save custom field values
        for cf in active_custom_fields:
            val = request.form.get(f"custom_field_{cf.id}", "").strip()
            if val:
                db.session.add(CustomFieldValue(definition_id=cf.id, client_id=client.id, value=val))
        db.session.commit()

        if _is_ajax():
            return jsonify({
                "ok": True,
                "message": f"Client '{client.company_name}' created successfully.",
                "redirect": url_for("clients.detail_client", id=client.id),
            })

        flash(f"Client '{client.company_name}' created successfully.", "success")
        return redirect(url_for("clients.detail_client", id=client.id))

    if _is_ajax():
        return render_template(
            "clients/_form_fields.html",
            client=None,
            statuses=CLIENT_STATUSES,
            custom_fields=active_custom_fields,
            custom_values={},
            panel_mode=True,
        )

    return render_template(
        "clients/form.html",
        client=None,
        statuses=CLIENT_STATUSES,
        custom_fields=active_custom_fields,
        custom_values={},
    )


@clients_bp.route("/<int:id>")
@login_required
def detail_client(id):
    client = db.get_or_404(Client, id)
    if not can_access_record(client):
        abort(403)

    # Build unified timeline merging contacts + follow-ups
    types_map = {t.label: {"icon": t.icon, "colour": t.colour} for t in InteractionType.query.all()}
    timeline = []
    for c in client.contacts:
        type_info = types_map.get(c.contact_type, {})
        timeline.append({
            "type": "contact",
            "date": c.date,
            "time": c.time,
            "icon": type_info.get("icon", "bi-chat-dots"),
            "badge_class": f"badge-{c.contact_type}",
            "badge_colour": type_info.get("colour", "#6c757d"),
            "badge_text": c.contact_type.capitalize(),
            "notes": c.notes,
            "outcome": c.outcome,
            "edit_url": url_for("contacts.edit_contact", id=c.id),
            "obj": c,
            "attachment_count": len(c.attachments),
        })
    for fu in client.followups:
        timeline.append({
            "type": "followup",
            "date": fu.due_date,
            "time": fu.due_time,
            "icon": "bi-calendar-check",
            "badge_class": f"badge-{fu.priority}",
            "badge_text": fu.priority.capitalize(),
            "notes": fu.notes,
            "completed": fu.completed,
            "is_overdue": fu.is_overdue,
            "edit_url": url_for("followups.edit_followup", id=fu.id),
            "complete_url": url_for("followups.complete_followup", id=fu.id),
            "obj": fu,
            "attachment_count": len(fu.attachments),
        })
    timeline.sort(key=lambda x: x["date"], reverse=True)

    # Summary dates
    contact_dates = [c.date for c in client.contacts]
    last_contact = max(contact_dates) if contact_dates else None
    pending_dates = [fu.due_date for fu in client.followups if not fu.completed]
    next_followup = min(pending_dates) if pending_dates else None

    # Relationship summary stats
    total_contacts = len(client.contacts)
    total_followups = len(client.followups)
    completed_followups = sum(1 for fu in client.followups if fu.completed)
    pending_followups = total_followups - completed_followups
    completion_rate = round((completed_followups / total_followups) * 100) if total_followups else 0

    # Custom field values for display
    active_custom_fields = CustomFieldDefinition.query.filter_by(is_active=True).order_by(
        CustomFieldDefinition.sort_order
    ).all()
    custom_values = {
        v.definition_id: v.value
        for v in CustomFieldValue.query.filter_by(client_id=client.id).all()
    }

    # All attachments for this client (direct + via contacts/followups)
    client_attachments = Attachment.query.filter_by(client_id=client.id).options(
        joinedload(Attachment.category),
        joinedload(Attachment.tags),
    ).order_by(Attachment.created_at.desc()).all()

    # Active categories and tags for upload/edit modals
    attachment_categories = AttachmentCategory.query.filter_by(is_active=True).order_by(
        AttachmentCategory.sort_order
    ).all()
    attachment_tags = AttachmentTag.query.filter_by(is_active=True).order_by(
        AttachmentTag.sort_order
    ).all()

    # Pass all_users for reassignment (Manager+)
    all_users = None
    if current_user.has_role_at_least("manager"):
        all_users = User.query.filter_by(is_active_user=True).order_by(User.display_name).all()

    return render_template(
        "clients/detail.html",
        client=client,
        timeline=timeline,
        last_contact=last_contact,
        next_followup=next_followup,
        total_contacts=total_contacts,
        total_followups=total_followups,
        pending_followups=pending_followups,
        completion_rate=completion_rate,
        quick_functions=[qf.to_dict() for qf in QuickFunction.query.filter_by(
            is_active=True
        ).order_by(QuickFunction.sort_order).all()],
        custom_fields=active_custom_fields,
        custom_values=custom_values,
        client_attachments=client_attachments,
        attachment_categories=attachment_categories,
        attachment_tags=attachment_tags,
        client_id=client.id,
        all_users=all_users,
    )


@clients_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_client(id):
    client = db.get_or_404(Client, id)
    if not can_access_record(client):
        abort(403)

    active_custom_fields = CustomFieldDefinition.query.filter_by(is_active=True).order_by(
        CustomFieldDefinition.sort_order
    ).all()

    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        if not company_name:
            flash("Company name is required.", "danger")
            custom_values = {
                v.definition_id: v.value
                for v in CustomFieldValue.query.filter_by(client_id=client.id).all()
            }
            return render_template(
                "clients/form.html",
                client=client,
                statuses=CLIENT_STATUSES,
                custom_fields=active_custom_fields,
                custom_values=custom_values,
            )

        client.company_name = company_name
        client.industry = request.form.get("industry", "").strip()
        client.phone = request.form.get("phone", "").strip()
        client.email = request.form.get("email", "").strip()
        client.contact_person = request.form.get("contact_person", "").strip()
        client.status = request.form.get("status", "lead")

        # Upsert custom field values
        for cf in active_custom_fields:
            val = request.form.get(f"custom_field_{cf.id}", "").strip()
            existing = CustomFieldValue.query.filter_by(
                definition_id=cf.id, client_id=client.id
            ).first()
            if existing:
                existing.value = val
            elif val:
                db.session.add(CustomFieldValue(definition_id=cf.id, client_id=client.id, value=val))

        db.session.commit()
        flash(f"Client '{client.company_name}' updated successfully.", "success")
        return redirect(url_for("clients.detail_client", id=client.id))

    custom_values = {
        v.definition_id: v.value
        for v in CustomFieldValue.query.filter_by(client_id=client.id).all()
    }
    return render_template(
        "clients/form.html",
        client=client,
        statuses=CLIENT_STATUSES,
        custom_fields=active_custom_fields,
        custom_values=custom_values,
    )


@clients_bp.route("/<int:id>/status", methods=["PATCH"])
@login_required
def update_status(id):
    client = db.get_or_404(Client, id)
    if not can_access_record(client):
        abort(403)
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "")
    if new_status not in CLIENT_STATUSES:
        return jsonify({"ok": False, "error": f"Invalid status. Must be one of: {', '.join(CLIENT_STATUSES)}"}), 400
    client.status = new_status
    db.session.commit()
    return jsonify({"ok": True, "status": new_status})


@clients_bp.route("/<int:id>/quick-action", methods=["POST"])
@login_required
def quick_action(id):
    client = db.get_or_404(Client, id)
    if not can_access_record(client):
        abort(403)

    try:
        action_id = int(request.form.get("action_id", "0"))
    except (ValueError, TypeError):
        action_id = 0

    qf = db.session.get(QuickFunction, action_id)
    if not qf:
        if _is_ajax():
            return jsonify({"ok": False, "error": "Invalid quick function."}), 400
        flash("Invalid quick function.", "danger")
        return redirect(url_for("clients.detail_client", id=client.id))

    contact = Contact(
        client_id=client.id,
        date=date.today(),
        time=datetime.now().time().replace(microsecond=0),
        contact_type=qf.contact_type,
        notes=qf.notes,
        outcome=qf.outcome,
        user_id=current_user.id,
    )
    db.session.add(contact)
    db.session.commit()

    message = f'"{qf.label}" logged for {client.company_name}.'
    if _is_ajax():
        return jsonify({"ok": True, "message": message})

    flash(message, "success")
    return redirect(url_for("clients.detail_client", id=client.id))


@clients_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_client(id):
    client = db.get_or_404(Client, id)
    if not can_access_record(client):
        abort(403)

    name = client.company_name
    client_id = client.id
    db.session.delete(client)
    db.session.commit()

    # Clean up uploads directory for this client
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], str(client_id))
    if os.path.isdir(upload_dir):
        shutil.rmtree(upload_dir)

    flash(f"Client '{name}' deleted successfully.", "success")
    return redirect(url_for("clients.list_clients"))


@clients_bp.route("/<int:id>/reassign", methods=["POST"])
@role_required("manager")
def reassign_client(id):
    """Reassign a single client (optionally with child contacts/followups)."""
    client = db.get_or_404(Client, id)
    data = request.get_json(silent=True) or {}
    target_user_id = data.get("target_user_id")

    if not target_user_id:
        return jsonify({"ok": False, "error": "Target user is required."}), 400

    target_user = db.get_or_404(User, int(target_user_id))
    client.user_id = target_user.id

    if data.get("cascade"):
        Contact.query.filter_by(client_id=client.id).update({"user_id": target_user.id})
        FollowUp.query.filter_by(client_id=client.id).update({"user_id": target_user.id})

    db.session.commit()
    return jsonify({"ok": True, "message": f"Client reassigned to {target_user.display_name}."})


@clients_bp.route("/bulk-reassign", methods=["POST"])
@role_required("manager")
def bulk_reassign():
    """Bulk-reassign selected clients to another user."""
    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])
    target_user_id = data.get("target_user_id")
    if not ids or not target_user_id:
        return jsonify({"ok": False, "error": "IDs and target user are required."}), 400
    target_user = db.get_or_404(User, int(target_user_id))
    Client.query.filter(Client.id.in_(ids)).update({"user_id": target_user.id})
    db.session.commit()
    return jsonify({"ok": True, "message": f"{len(ids)} client(s) reassigned to {target_user.display_name}."})
