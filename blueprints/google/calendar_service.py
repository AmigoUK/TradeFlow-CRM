"""Google Calendar API service — create, update, delete events."""

import logging
from datetime import datetime, timedelta

from extensions import db
from blueprints.google.google_service import build_service

logger = logging.getLogger(__name__)


def _build_event_body(title, description, event_date, event_time=None, completed=False):
    """Build a Google Calendar event body dict."""
    summary = f"{'✓ ' if completed else ''}{title}"

    if event_time:
        start_dt = datetime.combine(event_date, event_time)
        end_dt = start_dt + timedelta(hours=1)
        start = {"dateTime": start_dt.isoformat(), "timeZone": "UTC"}
        end = {"dateTime": end_dt.isoformat(), "timeZone": "UTC"}
    else:
        start = {"date": event_date.isoformat()}
        end = {"date": event_date.isoformat()}

    body = {
        "summary": summary,
        "description": description or "",
        "start": start,
        "end": end,
    }

    if completed:
        body["transparency"] = "transparent"

    return body


def sync_followup_to_calendar(followup, user_id):
    """Create or update a Google Calendar event for a follow-up."""
    from models.google_calendar_sync import GoogleCalendarSync

    service = build_service("calendar", "v3", user_id=user_id)
    if not service:
        return None

    title = followup.client.company_name
    description = followup.notes or ""
    body = _build_event_body(
        title, description, followup.due_date,
        followup.due_time, followup.completed,
    )

    try:
        sync = GoogleCalendarSync.query.filter_by(
            followup_id=followup.id, user_id=user_id
        ).first()

        if sync:
            # Update existing event
            event = service.events().update(
                calendarId=sync.google_calendar_id,
                eventId=sync.google_event_id,
                body=body,
            ).execute()
            sync.google_etag = event.get("etag")
            sync.last_synced_at = datetime.utcnow()
        else:
            # Create new event
            event = service.events().insert(
                calendarId="primary",
                body=body,
            ).execute()
            sync = GoogleCalendarSync(
                user_id=user_id,
                followup_id=followup.id,
                google_event_id=event["id"],
                google_calendar_id="primary",
                sync_direction="outbound",
                google_etag=event.get("etag"),
            )
            db.session.add(sync)

        db.session.commit()
        return sync
    except Exception as e:
        logger.error("Failed to sync follow-up %s to calendar: %s", followup.id, e)
        return None


def sync_contact_to_calendar(contact, user_id):
    """Create or update a Google Calendar event for a contact."""
    from models.google_calendar_sync import GoogleCalendarSync

    service = build_service("calendar", "v3", user_id=user_id)
    if not service:
        return None

    title = f"{contact.contact_type.capitalize()}: {contact.client.company_name}"
    description = contact.notes or ""
    if contact.outcome:
        description += f"\nOutcome: {contact.outcome}"
    body = _build_event_body(title, description, contact.date, contact.time)

    try:
        sync = GoogleCalendarSync.query.filter_by(
            contact_id=contact.id, user_id=user_id
        ).first()

        if sync:
            event = service.events().update(
                calendarId=sync.google_calendar_id,
                eventId=sync.google_event_id,
                body=body,
            ).execute()
            sync.google_etag = event.get("etag")
            sync.last_synced_at = datetime.utcnow()
        else:
            event = service.events().insert(
                calendarId="primary",
                body=body,
            ).execute()
            sync = GoogleCalendarSync(
                user_id=user_id,
                contact_id=contact.id,
                google_event_id=event["id"],
                google_calendar_id="primary",
                sync_direction="outbound",
                google_etag=event.get("etag"),
            )
            db.session.add(sync)

        db.session.commit()
        return sync
    except Exception as e:
        logger.error("Failed to sync contact %s to calendar: %s", contact.id, e)
        return None


def delete_calendar_event(sync_record, user_id):
    """Delete a Google Calendar event linked to a sync record."""
    service = build_service("calendar", "v3", user_id=user_id)
    if not service or not sync_record:
        return

    try:
        service.events().delete(
            calendarId=sync_record.google_calendar_id,
            eventId=sync_record.google_event_id,
        ).execute()
    except Exception as e:
        logger.warning("Failed to delete calendar event %s: %s", sync_record.google_event_id, e)

    db.session.delete(sync_record)
    db.session.commit()


def fetch_google_events(user_id, time_min, time_max):
    """Fetch events from the user's primary Google Calendar."""
    service = build_service("calendar", "v3", user_id=user_id)
    if not service:
        return []

    try:
        events_result = service.events().list(
            calendarId="primary",
            timeMin=time_min.isoformat() + "Z",
            timeMax=time_max.isoformat() + "Z",
            singleEvents=True,
            orderBy="startTime",
            maxResults=250,
        ).execute()
        return events_result.get("items", [])
    except Exception as e:
        logger.error("Failed to fetch Google Calendar events: %s", e)
        return []
