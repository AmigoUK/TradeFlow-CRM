from datetime import date, datetime

from flask import flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import func

from blueprints.clients import clients_bp
from extensions import db
from models import Client, CLIENT_STATUSES, Contact, FollowUp, QuickFunction, InteractionType, CustomFieldDefinition, CustomFieldValue


def _is_ajax():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@clients_bp.route("/")
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
    )

    if q:
        query = query.filter(Client.company_name.ilike(f"%{q}%"))
    if status and view != "board":
        query = query.filter(Client.status == status)

    results = query.order_by(Client.company_name).all()

    # Attach computed dates to client objects for template access
    clients = []
    for client, last_contact, next_followup in results:
        client.last_contact = last_contact
        client.next_followup = next_followup
        clients.append(client)

    active_qfs = QuickFunction.query.filter_by(is_active=True).order_by(
        QuickFunction.sort_order
    ).all()

    return render_template(
        "clients/list.html",
        clients=clients,
        statuses=CLIENT_STATUSES,
        q=q,
        status=status,
        view=view,
        quick_functions=[qf.to_dict() for qf in active_qfs],
    )


@clients_bp.route("/new", methods=["GET", "POST"])
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
def detail_client(id):
    client = db.get_or_404(Client, id)

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
    )


@clients_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_client(id):
    client = db.get_or_404(Client, id)
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
def update_status(id):
    client = db.get_or_404(Client, id)
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "")
    if new_status not in CLIENT_STATUSES:
        return jsonify({"ok": False, "error": f"Invalid status. Must be one of: {', '.join(CLIENT_STATUSES)}"}), 400
    client.status = new_status
    db.session.commit()
    return jsonify({"ok": True, "status": new_status})


@clients_bp.route("/<int:id>/quick-action", methods=["POST"])
def quick_action(id):
    client = db.get_or_404(Client, id)

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
    )
    db.session.add(contact)
    db.session.commit()

    message = f'"{qf.label}" logged for {client.company_name}.'
    if _is_ajax():
        return jsonify({"ok": True, "message": message})

    flash(message, "success")
    return redirect(url_for("clients.detail_client", id=client.id))


@clients_bp.route("/<int:id>/delete", methods=["POST"])
def delete_client(id):
    client = db.get_or_404(Client, id)
    name = client.company_name
    db.session.delete(client)
    db.session.commit()
    flash(f"Client '{name}' deleted successfully.", "success")
    return redirect(url_for("clients.list_clients"))
