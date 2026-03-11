from datetime import date, datetime

from flask import flash, redirect, render_template, request, url_for

from blueprints.followups import followups_bp
from extensions import db
from models import Client, FollowUp, PRIORITIES


@followups_bp.route("/")
def list_followups():
    priority = request.args.get("priority", "").strip()
    show_overdue = request.args.get("overdue", "").strip()
    show_completed = request.args.get("completed", "").strip()

    query = FollowUp.query.join(Client)

    if priority:
        query = query.filter(FollowUp.priority == priority)
    if show_overdue == "1":
        query = query.filter(
            FollowUp.completed == False,  # noqa: E712
            FollowUp.due_date < date.today(),
        )
    if show_completed == "1":
        query = query.filter(FollowUp.completed == True)  # noqa: E712
    elif show_completed == "0":
        query = query.filter(FollowUp.completed == False)  # noqa: E712

    followups = query.order_by(FollowUp.due_date).all()
    return render_template(
        "followups/list.html",
        followups=followups,
        priorities=PRIORITIES,
        selected_priority=priority,
        show_overdue=show_overdue,
        show_completed=show_completed,
    )


@followups_bp.route("/new", methods=["GET", "POST"])
def create_followup():
    if request.method == "POST":
        client_id = request.form.get("client_id")
        due_date_str = request.form.get("due_date", "").strip()
        priority = request.form.get("priority", "medium")

        if not client_id:
            flash("Please select a client.", "danger")
            return redirect(url_for("followups.create_followup"))

        try:
            parsed_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else date.today()
        except ValueError:
            parsed_date = date.today()

        followup = FollowUp(
            client_id=int(client_id),
            due_date=parsed_date,
            priority=priority,
            notes=request.form.get("notes", "").strip(),
        )
        db.session.add(followup)
        db.session.commit()
        flash("Follow-up created successfully.", "success")
        return redirect(url_for("clients.detail_client", id=followup.client_id))

    client_id = request.args.get("client_id")
    clients = Client.query.order_by(Client.company_name).all()
    return render_template(
        "followups/form.html",
        followup=None,
        clients=clients,
        priorities=PRIORITIES,
        selected_client_id=int(client_id) if client_id else None,
        today=date.today().isoformat(),
    )


@followups_bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit_followup(id):
    followup = db.get_or_404(FollowUp, id)

    if request.method == "POST":
        client_id = request.form.get("client_id")
        due_date_str = request.form.get("due_date", "").strip()

        if not client_id:
            flash("Please select a client.", "danger")
            clients = Client.query.order_by(Client.company_name).all()
            return render_template(
                "followups/form.html",
                followup=followup,
                clients=clients,
                priorities=PRIORITIES,
                selected_client_id=followup.client_id,
                today=date.today().isoformat(),
            )

        try:
            followup.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else date.today()
        except ValueError:
            followup.due_date = date.today()

        followup.client_id = int(client_id)
        followup.priority = request.form.get("priority", "medium")
        followup.notes = request.form.get("notes", "").strip()
        followup.completed = "completed" in request.form
        db.session.commit()
        flash("Follow-up updated successfully.", "success")
        return redirect(url_for("clients.detail_client", id=followup.client_id))

    clients = Client.query.order_by(Client.company_name).all()
    return render_template(
        "followups/form.html",
        followup=followup,
        clients=clients,
        priorities=PRIORITIES,
        selected_client_id=followup.client_id,
        today=date.today().isoformat(),
    )


@followups_bp.route("/<int:id>/complete", methods=["POST"])
def complete_followup(id):
    followup = db.get_or_404(FollowUp, id)
    followup.completed = not followup.completed
    db.session.commit()
    status = "completed" if followup.completed else "reopened"
    flash(f"Follow-up marked as {status}.", "success")
    return redirect(request.referrer or url_for("followups.list_followups"))


@followups_bp.route("/<int:id>/delete", methods=["POST"])
def delete_followup(id):
    followup = db.get_or_404(FollowUp, id)
    client_id = followup.client_id
    db.session.delete(followup)
    db.session.commit()
    flash("Follow-up deleted successfully.", "success")
    return redirect(url_for("clients.detail_client", id=client_id))
