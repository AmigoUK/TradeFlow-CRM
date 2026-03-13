"""Google Meet routes — generate Meet links via Calendar API conferenceData."""

import uuid
from datetime import datetime, timedelta

from flask import flash, jsonify, redirect, request, url_for
from flask_login import current_user, login_required

from blueprints.auth.decorators import can_access_record
from blueprints.google import google_bp
from blueprints.google.google_service import build_service, google_required
from extensions import db
from models import Contact, FollowUp


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
        return redirect(request.referrer or url_for("clients.detail_client", id=followup.client_id))

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
        "summary": f"Meeting: {followup.client.company_name}",
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

    return redirect(request.referrer or url_for("clients.detail_client", id=followup.client_id))


@google_bp.route("/meet/create-for-contact/<int:id>", methods=["POST"])
@login_required
@google_required
def create_meet_for_contact(id):
    """Generate a Google Meet link for a contact/interaction."""
    contact = db.get_or_404(Contact, id)
    if not can_access_record(contact):
        return jsonify({"ok": False, "error": "Access denied."}), 403

    service = build_service("calendar", "v3")
    if not service:
        flash("Could not connect to Google Calendar.", "danger")
        return redirect(request.referrer or url_for("clients.detail_client", id=contact.client_id))

    if contact.time:
        start_dt = datetime.combine(contact.date, contact.time)
        end_dt = start_dt + timedelta(hours=1)
        start = {"dateTime": start_dt.isoformat(), "timeZone": "UTC"}
        end = {"dateTime": end_dt.isoformat(), "timeZone": "UTC"}
    else:
        start_dt = datetime.combine(contact.date, datetime.min.time().replace(hour=9))
        end_dt = start_dt + timedelta(hours=1)
        start = {"dateTime": start_dt.isoformat(), "timeZone": "UTC"}
        end = {"dateTime": end_dt.isoformat(), "timeZone": "UTC"}

    event_body = {
        "summary": f"Meeting: {contact.client.company_name}",
        "description": contact.notes or "",
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
            contact.meet_link = meet_link
            db.session.commit()
            flash("Google Meet link created.", "success")
        else:
            flash("Event created but no Meet link was generated.", "warning")
    except Exception as e:
        flash(f"Failed to create Meet link: {e}", "danger")

    return redirect(request.referrer or url_for("clients.detail_client", id=contact.client_id))
