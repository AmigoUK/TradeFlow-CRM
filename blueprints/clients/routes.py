from flask import flash, redirect, render_template, request, url_for
from sqlalchemy import func

from blueprints.clients import clients_bp
from extensions import db
from models import Client, CLIENT_STATUSES, Contact, FollowUp


@clients_bp.route("/")
def list_clients():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

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
    if status:
        query = query.filter(Client.status == status)

    results = query.order_by(Client.company_name).all()

    # Attach computed dates to client objects for template access
    clients = []
    for client, last_contact, next_followup in results:
        client.last_contact = last_contact
        client.next_followup = next_followup
        clients.append(client)

    return render_template(
        "clients/list.html",
        clients=clients,
        statuses=CLIENT_STATUSES,
        q=q,
        status=status,
    )


@clients_bp.route("/new", methods=["GET", "POST"])
def create_client():
    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        if not company_name:
            flash("Company name is required.", "danger")
            return render_template(
                "clients/form.html",
                client=None,
                statuses=CLIENT_STATUSES,
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
        db.session.commit()
        flash(f"Client '{client.company_name}' created successfully.", "success")
        return redirect(url_for("clients.detail_client", id=client.id))

    return render_template(
        "clients/form.html",
        client=None,
        statuses=CLIENT_STATUSES,
    )


@clients_bp.route("/<int:id>")
def detail_client(id):
    client = db.get_or_404(Client, id)

    # Build unified timeline merging contacts + follow-ups
    timeline = []
    for c in client.contacts:
        timeline.append({
            "type": "contact",
            "date": c.date,
            "icon": "bi-chat-dots",
            "badge_class": f"badge-{c.contact_type}",
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

    return render_template(
        "clients/detail.html",
        client=client,
        timeline=timeline,
        last_contact=last_contact,
        next_followup=next_followup,
    )


@clients_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_client(id):
    client = db.get_or_404(Client, id)

    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        if not company_name:
            flash("Company name is required.", "danger")
            return render_template(
                "clients/form.html",
                client=client,
                statuses=CLIENT_STATUSES,
            )

        client.company_name = company_name
        client.industry = request.form.get("industry", "").strip()
        client.phone = request.form.get("phone", "").strip()
        client.email = request.form.get("email", "").strip()
        client.contact_person = request.form.get("contact_person", "").strip()
        client.status = request.form.get("status", "lead")
        db.session.commit()
        flash(f"Client '{client.company_name}' updated successfully.", "success")
        return redirect(url_for("clients.detail_client", id=client.id))

    return render_template(
        "clients/form.html",
        client=client,
        statuses=CLIENT_STATUSES,
    )


@clients_bp.route("/<int:id>/delete", methods=["POST"])
def delete_client(id):
    client = db.get_or_404(Client, id)
    name = client.company_name
    db.session.delete(client)
    db.session.commit()
    flash(f"Client '{name}' deleted successfully.", "success")
    return redirect(url_for("clients.list_clients"))
