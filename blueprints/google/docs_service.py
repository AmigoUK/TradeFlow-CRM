"""Google Docs service — create, copy, and link documents."""

import logging

from blueprints.google.google_service import build_service

logger = logging.getLogger(__name__)


def create_blank_document(title, user_id=None):
    """Create a blank Google Document and return (doc_id, url)."""
    service = build_service("docs", "v1", user_id=user_id)
    if not service:
        return None, None

    try:
        doc = service.documents().create(body={"title": title}).execute()
        doc_id = doc.get("documentId")
        url = f"https://docs.google.com/document/d/{doc_id}/edit"
        return doc_id, url
    except Exception as e:
        logger.error("Failed to create blank document: %s", e)
        return None, None


def create_from_template(template_doc_id, new_title, user_id=None):
    """Copy a template Google Doc and return (doc_id, url)."""
    drive_service = build_service("drive", "v3", user_id=user_id)
    if not drive_service:
        return None, None

    try:
        copy = drive_service.files().copy(
            fileId=template_doc_id,
            body={"name": new_title},
        ).execute()
        doc_id = copy.get("id")
        url = f"https://docs.google.com/document/d/{doc_id}/edit"
        return doc_id, url
    except Exception as e:
        logger.error("Failed to copy template document: %s", e)
        return None, None
