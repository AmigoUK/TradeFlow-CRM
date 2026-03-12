from datetime import date, datetime, timedelta

from flask import jsonify, redirect, render_template, request, url_for

from blueprints.dashboard import dashboard_bp
from models import Client, Contact, FollowUp


@dashboard_bp.route("/")
def index():
    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/dashboard")
def dashboard():
    today = date.today()

    # Stats
    active_clients = Client.query.filter(Client.status == "active").count()
    total_clients = Client.query.count()

    due_today = FollowUp.query.filter(
        FollowUp.due_date == today,
        FollowUp.completed == False,  # noqa: E712
    ).all()

    overdue = FollowUp.query.filter(
        FollowUp.due_date < today,
        FollowUp.completed == False,  # noqa: E712
    ).all()

    # Recent interactions (last 5)
    recent_contacts = (
        Contact.query
        .order_by(Contact.date.desc(), Contact.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard/index.html",
        active_clients=active_clients,
        total_clients=total_clients,
        due_today=due_today,
        overdue=overdue,
        recent_contacts=recent_contacts,
    )


@dashboard_bp.route("/calendar")
def calendar():
    return render_template("dashboard/calendar.html")


@dashboard_bp.route("/api/events")
def api_events():
    """JSON feed for FullCalendar — follow-ups + contacts colour-coded."""
    start_str = request.args.get("start", "")
    end_str = request.args.get("end", "")

    try:
        start_date = datetime.fromisoformat(start_str[:10]).date() if start_str else date.today() - timedelta(days=90)
        end_date = datetime.fromisoformat(end_str[:10]).date() if end_str else date.today() + timedelta(days=90)
    except (ValueError, TypeError):
        start_date = date.today() - timedelta(days=90)
        end_date = date.today() + timedelta(days=90)

    events = []

    # Follow-ups — colour by priority
    priority_colours = {"high": "#dc3545", "medium": "#ffc107", "low": "#198754"}
    followups = FollowUp.query.filter(
        FollowUp.due_date >= start_date,
        FollowUp.due_date <= end_date,
    ).all()
    for fu in followups:
        colour = "#6c757d" if fu.completed else priority_colours.get(fu.priority, "#0d6efd")
        text_colour = "#000" if fu.priority == "medium" and not fu.completed else "#fff"
        events.append({
            "id": f"followup-{fu.id}",
            "title": f"{'✓ ' if fu.completed else ''}{fu.client.company_name}",
            "start": fu.due_date.isoformat(),
            "backgroundColor": colour,
            "borderColor": colour,
            "textColor": text_colour,
            "extendedProps": {
                "type": "followup",
                "clientId": fu.client_id,
                "priority": fu.priority,
                "completed": fu.completed,
                "notes": fu.notes[:100] if fu.notes else "",
            },
        })

    # Contacts — colour by type
    type_colours = {"phone": "#0d6efd", "email": "#6f42c1", "meeting": "#fd7e14"}
    contacts = Contact.query.filter(
        Contact.date >= start_date,
        Contact.date <= end_date,
    ).all()
    for c in contacts:
        colour = type_colours.get(c.contact_type, "#0d6efd")
        events.append({
            "id": f"contact-{c.id}",
            "title": f"{c.contact_type.capitalize()}: {c.client.company_name}",
            "start": c.date.isoformat(),
            "backgroundColor": colour,
            "borderColor": colour,
            "textColor": "#fff",
            "extendedProps": {
                "type": "contact",
                "clientId": c.client_id,
                "contactType": c.contact_type,
                "notes": c.notes[:100] if c.notes else "",
            },
        })

    return jsonify(events)
