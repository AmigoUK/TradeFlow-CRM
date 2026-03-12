from datetime import date, datetime

from flask import flash, redirect, render_template, request, url_for

from blueprints.contacts import contacts_bp
from extensions import db
from models import Client, Contact, CONTACT_TYPES


@contacts_bp.route("/")
def list_contacts():
    contact_type = request.args.get("type", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    query = Contact.query.join(Client)

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

    contacts = query.order_by(Contact.date.desc()).all()
    return render_template(
        "contacts/list.html",
        contacts=contacts,
        contact_types=CONTACT_TYPES,
        selected_type=contact_type,
        date_from=date_from,
        date_to=date_to,
    )


@contacts_bp.route("/new", methods=["GET", "POST"])
def create_contact():
    if request.method == "POST":
        client_id = request.form.get("client_id")
        contact_date = request.form.get("date", "").strip()
        contact_type = request.form.get("contact_type", "phone")

        if not client_id:
            flash("Please select a client.", "danger")
            return redirect(url_for("contacts.create_contact"))

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
        )
        db.session.add(contact)
        db.session.commit()
        flash("Interaction logged successfully.", "success")
        return redirect(url_for("clients.detail_client", id=contact.client_id))

    client_id = request.args.get("client_id")
    prefill_notes = request.args.get("notes", "")
    prefill_date = request.args.get("date", date.today().isoformat())
    clients = Client.query.order_by(Client.company_name).all()
    return render_template(
        "contacts/form.html",
        contact=None,
        clients=clients,
        contact_types=CONTACT_TYPES,
        selected_client_id=int(client_id) if client_id else None,
        today=prefill_date,
        prefill_notes=prefill_notes,
    )


@contacts_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_contact(id):
    contact = db.get_or_404(Contact, id)

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
                contact_types=CONTACT_TYPES,
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
        db.session.commit()
        flash("Interaction updated successfully.", "success")
        return redirect(url_for("clients.detail_client", id=contact.client_id))

    clients = Client.query.order_by(Client.company_name).all()
    return render_template(
        "contacts/form.html",
        contact=contact,
        clients=clients,
        contact_types=CONTACT_TYPES,
        selected_client_id=contact.client_id,
        today=date.today().isoformat(),
    )


@contacts_bp.route("/<int:id>/delete", methods=["POST"])
def delete_contact(id):
    contact = db.get_or_404(Contact, id)
    client_id = contact.client_id
    db.session.delete(contact)
    db.session.commit()
    flash("Interaction deleted successfully.", "success")
    return redirect(url_for("clients.detail_client", id=client_id))
