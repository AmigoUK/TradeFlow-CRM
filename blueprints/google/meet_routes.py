"""Google Meet routes — generate Meet links via Calendar API conferenceData."""

import uuid
from datetime import datetime, timedelta

from flask import flash, jsonify, redirect, request, url_for
from flask_login import current_user, login_required

from blueprints.auth.decorators import can_access_record
from blueprints.google import google_bp
from blueprints.google.google_service import build_service, google_required
from extensions import db
from models import Interaction, FollowUp


@google_bp.route("/meet/create-for-followup/<int:id>", methods=["POST"])
@login_required
@google_required
def create_meet_for_followup(id):
    """Generate a Google Meet link for a follow-up via Calendar API."""
    followup = db.get_or_404(FollowUp, id)
    if not can_access_record(followup):
        return jsonify({"ok": False, "error": "Access denied."}), 403

    service = build_service("calendar", "v3")
    if not service:
        flash("Could not connect to Google Calendar.", "danger")
        return redirect(request.referrer or url_for("companies.detail_company", id=followup.company_id))

    # Build a calendar event with conferenceData to generate a Meet link
    if followup.due_time:
        start_dt = datetime.combine(followup.due_date, followup.due_time)
        end_dt = start_dt + timedelta(hours=1)
        start = {"dateTime": start_dt.isoformat(), "timeZone": "UTC"}
        end = {"dateTime": end_dt.isoformat(), "timeZone": "UTC"}
    else:
        start_dt = datetime.combine(followup.due_date, datetime.min.time().replace(hour=9))
        end_dt = start_dt + timedelta(hours=1)
        start = {"dateTime": start_dt.isoformat(), "timeZone": "UTC"}
        end = {"dateTime": end_dt.isoformat(), "timeZone": "UTC"}

    event_body = {
        "summary": f"Meeting: {followup.company.company_name}",
        "description": followup.notes or "",
        "start": start,
        "end": end,
        "conferenceData": {
            "createRequest": {
                "requestId": uuid.uuid4().hex,
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    try:
        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1,
        ).execute()

        meet_link = event.get("hangoutLink", "")
        if meet_link:
            followup.meet_link = meet_link
            db.session.commit()
            flash("Google Meet link created.", "success")
        else:
            flash("Event created but no Meet link was generated.", "warning")
    except Exception as e:
        flash(f"Failed to create Meet link: {e}", "danger")

    return redirect(request.referrer or url_for("companies.detail_company", id=followup.company_id))


@google_bp.route("/meet/create-for-interaction/<int:id>", methods=["POST"])
@login_required
@google_required
def create_meet_for_interaction(id):
    """Generate a Google Meet link for an interaction."""
    interaction = db.get_or_404(Interaction, id)
    if not can_access_record(interaction):
        return jsonify({"ok": False, "error": "Access denied."}), 403

    service = build_service("calendar", "v3")
    if not service:
        flash("Could not connect to Google Calendar.", "danger")
        return redirect(request.referrer or url_for("companies.detail_company", id=interaction.company_id))

    if interaction.time:
        start_dt = datetime.combine(interaction.date, interaction.time)
        end_dt = start_dt + timedelta(hours=1)
        start = {"dateTime": start_dt.isoformat(), "timeZone": "UTC"}
        end = {"dateTime": end_dt.isoformat(), "timeZone": "UTC"}
    else:
        start_dt = datetime.combine(interaction.date, datetime.min.time().replace(hour=9))
        end_dt = start_dt + timedelta(hours=1)
        start = {"dateTime": start_dt.isoformat(), "timeZone": "UTC"}
        end = {"dateTime": end_dt.isoformat(), "timeZone": "UTC"}

    event_body = {
        "summary": f"Meeting: {interaction.company.company_name}",
        "description": interaction.notes or "",
        "start": start,
        "end": end,
        "conferenceData": {
            "createRequest": {
                "requestId": uuid.uuid4().hex,
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }

    try:
        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1,
        ).execute()

        meet_link = event.get("hangoutLink", "")
        if meet_link:
            interaction.meet_link = meet_link
            db.session.commit()
            flash("Google Meet link created.", "success")
        else:
            flash("Event created but no Meet link was generated.", "warning")
    except Exception as e:
        flash(f"Failed to create Meet link: {e}", "danger")

    return redirect(request.referrer or url_for("companies.detail_company", id=interaction.company_id))
