from datetime import date, datetime, timedelta

from flask import jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from collections import defaultdict

from blueprints.dashboard import dashboard_bp
from extensions import db
from models import Client, Contact, FollowUp, InteractionType


def _ownership_filter(query, model):
    """Filter query by ownership — managers/admins see all, users see only own."""
    if current_user.has_role_at_least("manager"):
        return query
    return query.filter(model.user_id == current_user.id)


@dashboard_bp.route("/")
@login_required
def index():
    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    today = date.today()

    # Stats
    client_q = Client.query
    if not current_user.has_role_at_least("manager"):
        client_q = client_q.filter(Client.user_id == current_user.id)

    active_clients = client_q.filter(Client.status == "active").count()
    total_clients = client_q.count()

    due_today_q = FollowUp.query.filter(
        FollowUp.due_date == today,
        FollowUp.completed == False,  # noqa: E712
    )
    due_today = _ownership_filter(due_today_q, FollowUp).all()

    overdue_q = FollowUp.query.filter(
        FollowUp.due_date < today,
        FollowUp.completed == False,  # noqa: E712
    )
    overdue = _ownership_filter(overdue_q, FollowUp).all()

    # Recent interactions (last 5)
    recent_q = Contact.query.order_by(Contact.date.desc(), Contact.created_at.desc())
    recent_contacts = _ownership_filter(recent_q, Contact).limit(5).all()

    return render_template(
        "dashboard/index.html",
        active_clients=active_clients,
        total_clients=total_clients,
        due_today=due_today,
        overdue=overdue,
        recent_contacts=recent_contacts,
    )


@dashboard_bp.route("/calendar")
@login_required
def calendar():
    return render_template("dashboard/calendar.html")


@dashboard_bp.route("/api/events")
@login_required
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
    followups_q = FollowUp.query.filter(
        FollowUp.due_date >= start_date,
        FollowUp.due_date <= end_date,
    )
    followups = _ownership_filter(followups_q, FollowUp).all()
    for fu in followups:
        colour = "#6c757d" if fu.completed else priority_colours.get(fu.priority, "#0d6efd")
        text_colour = "#000" if fu.priority == "medium" and not fu.completed else "#fff"
        if fu.due_time:
            start_val = f"{fu.due_date.isoformat()}T{fu.due_time.strftime('%H:%M:%S')}"
        else:
            start_val = fu.due_date.isoformat()
        events.append({
            "id": f"followup-{fu.id}",
            "title": f"{'✓ ' if fu.completed else ''}{fu.client.company_name}",
            "start": start_val,
            "backgroundColor": colour,
            "borderColor": colour,
            "textColor": text_colour,
            "extendedProps": {
                "type": "followup",
                "clientId": fu.client_id,
                "priority": fu.priority,
                "completed": fu.completed,
                "notes": fu.notes[:100] if fu.notes else "",
                "time": fu.due_time.strftime("%H:%M") if fu.due_time else None,
            },
        })

    # Contacts — colour by type
    type_colours = {t.label: t.colour for t in InteractionType.query.all()}
    contacts_q = Contact.query.filter(
        Contact.date >= start_date,
        Contact.date <= end_date,
    )
    contacts = _ownership_filter(contacts_q, Contact).all()
    for c in contacts:
        colour = type_colours.get(c.contact_type, "#0d6efd")
        if c.time:
            start_val = f"{c.date.isoformat()}T{c.time.strftime('%H:%M:%S')}"
        else:
            start_val = c.date.isoformat()
        events.append({
            "id": f"contact-{c.id}",
            "title": f"{c.contact_type.capitalize()}: {c.client.company_name}",
            "start": start_val,
            "backgroundColor": colour,
            "borderColor": colour,
            "textColor": "#fff",
            "extendedProps": {
                "type": "contact",
                "clientId": c.client_id,
                "contactType": c.contact_type,
                "notes": c.notes[:100] if c.notes else "",
                "time": c.time.strftime("%H:%M") if c.time else None,
            },
        })

    return jsonify(events)


@dashboard_bp.route("/agenda")
@login_required
def agenda():
    """Daily planner view — follow-ups grouped by time horizon."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    end_of_week = today + timedelta(days=(6 - today.weekday()))
    start_next_week = end_of_week + timedelta(days=1)
    end_next_week = start_next_week + timedelta(days=6)
    later_end = today + timedelta(days=60)

    def _fq(extra_filters):
        q = FollowUp.query
        for f in extra_filters:
            q = q.filter(f)
        return _ownership_filter(q, FollowUp)

    # Overdue
    overdue = _fq([
        FollowUp.due_date < today,
        FollowUp.completed == False,  # noqa: E712
    ]).order_by(FollowUp.due_date).all()

    # Today
    today_followups = _fq([
        FollowUp.due_date == today,
        FollowUp.completed == False,  # noqa: E712
    ]).order_by(FollowUp.due_date).all()

    # Today's interactions
    today_contacts_q = Contact.query.filter(Contact.date == today)
    today_contacts = _ownership_filter(today_contacts_q, Contact).order_by(Contact.created_at.desc()).all()

    # Tomorrow
    tomorrow_followups = _fq([
        FollowUp.due_date == tomorrow,
        FollowUp.completed == False,  # noqa: E712
    ]).all()

    # This week (day after tomorrow through end of week)
    day_after_tomorrow = tomorrow + timedelta(days=1)
    this_week = _fq([
        FollowUp.due_date >= day_after_tomorrow,
        FollowUp.due_date <= end_of_week,
        FollowUp.completed == False,  # noqa: E712
    ]).order_by(FollowUp.due_date).all()

    # Next week
    next_week = _fq([
        FollowUp.due_date >= start_next_week,
        FollowUp.due_date <= end_next_week,
        FollowUp.completed == False,  # noqa: E712
    ]).order_by(FollowUp.due_date).all()

    # Later (beyond next week, up to 60 days)
    later = _fq([
        FollowUp.due_date > end_next_week,
        FollowUp.due_date <= later_end,
        FollowUp.completed == False,  # noqa: E712
    ]).order_by(FollowUp.due_date).all()

    return render_template(
        "dashboard/agenda.html",
        overdue=overdue,
        today_followups=today_followups,
        today_contacts=today_contacts,
        tomorrow_followups=tomorrow_followups,
        this_week=this_week,
        next_week=next_week,
        later=later,
    )


@dashboard_bp.route("/quarterly")
@login_required
def quarterly():
    year = request.args.get("year", date.today().year, type=int)
    return render_template("dashboard/quarterly.html", year=year)


@dashboard_bp.route("/api/quarterly-data")
@login_required
def api_quarterly_data():
    """JSON API returning quarterly metrics for a given year."""
    year = request.args.get("year", date.today().year, type=int)
    today = date.today()

    # Quarter date ranges
    quarter_ranges = {
        1: (date(year, 1, 1), date(year, 3, 31)),
        2: (date(year, 4, 1), date(year, 6, 30)),
        3: (date(year, 7, 1), date(year, 9, 30)),
        4: (date(year, 10, 1), date(year, 12, 31)),
    }

    quarter_months = {
        1: ["January", "February", "March"],
        2: ["April", "May", "June"],
        3: ["July", "August", "September"],
        4: ["October", "November", "December"],
    }

    # Determine current quarter
    current_quarter = None
    if year == today.year:
        current_quarter = (today.month - 1) // 3 + 1

    # Fetch all data for the year in bulk (with ownership filter)
    contacts_q = Contact.query.filter(
        Contact.date >= date(year, 1, 1),
        Contact.date <= date(year, 12, 31),
    )
    all_contacts = _ownership_filter(contacts_q, Contact).all()

    followups_q = FollowUp.query.filter(
        FollowUp.due_date >= date(year, 1, 1),
        FollowUp.due_date <= date(year, 12, 31),
    )
    all_followups = _ownership_filter(followups_q, FollowUp).all()

    # Build dynamic type breakdown keys from all interaction types
    all_interaction_types = InteractionType.query.all()
    type_colours_map = {t.label: t.colour for t in all_interaction_types}

    max_monthly_activity = 0
    quarters = {}

    for q_num in range(1, 5):
        q_start, q_end = quarter_ranges[q_num]

        # Filter to this quarter
        q_contacts = [c for c in all_contacts if q_start <= c.date <= q_end]
        q_followups = [f for f in all_followups if q_start <= f.due_date <= q_end]

        # Type breakdown — dynamic from DB
        type_breakdown = {t.label: 0 for t in all_interaction_types}
        for c in q_contacts:
            if c.contact_type in type_breakdown:
                type_breakdown[c.contact_type] += 1
            else:
                type_breakdown[c.contact_type] = 1

        # Priority breakdown
        priority_breakdown = {"high": 0, "medium": 0, "low": 0}
        completed = 0
        pending = 0
        for f in q_followups:
            if f.priority in priority_breakdown:
                priority_breakdown[f.priority] += 1
            if f.completed:
                completed += 1
            else:
                pending += 1

        # Monthly activity
        months_data = []
        start_month = (q_num - 1) * 3 + 1
        for i in range(3):
            m = start_month + i
            m_contacts = sum(1 for c in q_contacts if c.date.month == m)
            m_followups = sum(1 for f in q_followups if f.due_date.month == m)
            total = m_contacts + m_followups
            if total > max_monthly_activity:
                max_monthly_activity = total
            months_data.append({
                "name": quarter_months[q_num][i],
                "contacts": m_contacts,
                "followups": m_followups,
                "total": total,
            })

        # Top clients by combined activity
        client_activity = defaultdict(lambda: {"count": 0, "name": ""})
        for c in q_contacts:
            client_activity[c.client_id]["count"] += 1
            client_activity[c.client_id]["name"] = c.client.company_name
        for f in q_followups:
            client_activity[f.client_id]["count"] += 1
            client_activity[f.client_id]["name"] = f.client.company_name

        top_clients = sorted(
            [{"id": cid, "name": data["name"], "count": data["count"]}
             for cid, data in client_activity.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:5]

        quarters[str(q_num)] = {
            "total_contacts": len(q_contacts),
            "total_followups": len(q_followups),
            "completed": completed,
            "pending": pending,
            "type_breakdown": type_breakdown,
            "priority_breakdown": priority_breakdown,
            "months": months_data,
            "top_clients": top_clients,
        }

    return jsonify({
        "year": year,
        "current_quarter": current_quarter,
        "max_monthly_activity": max_monthly_activity or 1,
        "quarters": quarters,
        "type_colours": type_colours_map,
    })
