"""Google Calendar routes — sync follow-ups/contacts, pull events, FullCalendar feed."""

from datetime import datetime, timedelta

from flask import flash, jsonify, redirect, request, url_for
from flask_login import current_user, login_required

from blueprints.auth.decorators import can_access_record
from blueprints.google import google_bp
from blueprints.google.calendar_service import (
    delete_calendar_event,
    fetch_google_events,
    sync_interaction_to_calendar,
    sync_followup_to_calendar,
)
from blueprints.google.google_service import google_required
from extensions import db
from models import Company, Interaction, FollowUp
from models.google_calendar_sync import GoogleCalendarSync


@google_bp.route("/calendar/sync-followup/<int:id>", methods=["POST"])
@login_required
@google_required
def sync_followup(id):
    """Push a follow-up to Google Calendar."""
    followup = db.get_or_404(FollowUp, id)
    if not can_access_record(followup):
        return jsonify({"ok": False, "error": "Access denied."}), 403

    sync = sync_followup_to_calendar(followup, current_user.id)
    if sync:
        flash("Follow-up synced to Google Calendar.", "success")
    else:
        flash("Failed to sync to Google Calendar.", "danger")

    return redirect(request.referrer or url_for("companies.detail_company", id=followup.company_id))


@google_bp.route("/calendar/sync-interaction/<int:id>", methods=["POST"])
@login_required
@google_required
def sync_interaction(id):
    """Push an interaction to Google Calendar."""
    interaction = db.get_or_404(Interaction, id)
    if not can_access_record(interaction):
        return jsonify({"ok": False, "error": "Access denied."}), 403

    sync = sync_interaction_to_calendar(interaction, current_user.id)
    if sync:
        flash("Interaction synced to Google Calendar.", "success")
    else:
        flash("Failed to sync to Google Calendar.", "danger")

    return redirect(request.referrer or url_for("companies.detail_company", id=interaction.company_id))


@google_bp.route("/calendar/unsync/<int:id>", methods=["POST"])
@login_required
@google_required
def unsync(id):
    """Remove a calendar sync link and delete the Google event."""
    sync = db.get_or_404(GoogleCalendarSync, id)
    if sync.user_id != current_user.id:
        return jsonify({"ok": False, "error": "Access denied."}), 403

    delete_calendar_event(sync, current_user.id)
    flash("Calendar sync removed.", "success")
    return redirect(request.referrer or url_for("dashboard.calendar"))


@google_bp.route("/calendar/events")
@login_required
@google_required
def google_calendar_events():
    """JSON feed for FullCalendar — Google Calendar events (read-only, Google-blue)."""
    start_str = request.args.get("start", "")
    end_str = request.args.get("end", "")

    try:
        start_dt = datetime.fromisoformat(start_str[:10]) if start_str else datetime.utcnow() - timedelta(days=90)
        end_dt = datetime.fromisoformat(end_str[:10]) if end_str else datetime.utcnow() + timedelta(days=90)
    except (ValueError, TypeError):
        start_dt = datetime.utcnow() - timedelta(days=90)
        end_dt = datetime.utcnow() + timedelta(days=90)

    # Get synced event IDs so we don't duplicate them
    synced_event_ids = {
        s.google_event_id
        for s in GoogleCalendarSync.query.filter_by(user_id=current_user.id).all()
    }

    raw_events = fetch_google_events(current_user.id, start_dt, end_dt)
    events = []

    for ge in raw_events:
        # Skip events already synced from CRM (avoid duplicates)
        if ge.get("id") in synced_event_ids:
            continue

        start = ge.get("start", {})
        end = ge.get("end", {})
        start_val = start.get("dateTime", start.get("date", ""))
        end_val = end.get("dateTime", end.get("date", ""))

        events.append({
            "id": f"google-{ge['id']}",
            "title": ge.get("summary", "(No title)"),
            "start": start_val,
            "end": end_val,
            "backgroundColor": "#4285F4",
            "borderColor": "#4285F4",
            "textColor": "#fff",
            "editable": False,
            "extendedProps": {
                "type": "google",
                "description": ge.get("description", ""),
                "location": ge.get("location", ""),
                "meetLink": ge.get("hangoutLink", ""),
            },
        })

    return jsonify(events)


@google_bp.route("/calendar/pull", methods=["POST"])
@login_required
@google_required
def pull_events():
    """Pull Google Calendar events (refresh the feed)."""
    flash("Google Calendar events refreshed.", "success")
    return redirect(url_for("dashboard.calendar"))
