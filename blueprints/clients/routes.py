from flask import flash, redirect, render_template, request, url_for

from blueprints.clients import clients_bp
from extensions import db
from models import Client, CLIENT_STATUSES


@clients_bp.route("/")
def list_clients():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()

    query = Client.query

    if q:
        query = query.filter(Client.company_name.ilike(f"%{q}%"))
    if status:
        query = query.filter(Client.status == status)

    clients = query.order_by(Client.company_name).all()
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
    return render_template("clients/detail.html", client=client)


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
