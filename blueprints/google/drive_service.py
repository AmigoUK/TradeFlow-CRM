"""Google Drive service — upload, list, and share files."""

import logging
from io import BytesIO

from blueprints.google.google_service import build_service

logger = logging.getLogger(__name__)


def upload_file_to_drive(file_stream, filename, mime_type, user_id=None):
    """Upload a file to Google Drive. Returns (file_id, web_url) or (None, None)."""
    service = build_service("drive", "v3", user_id=user_id)
    if not service:
        return None, None

    try:
        from googleapiclient.http import MediaIoBaseUpload

        media = MediaIoBaseUpload(
            BytesIO(file_stream.read()),
            mimetype=mime_type,
            resumable=True,
        )

        file_metadata = {"name": filename}
        result = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id,webViewLink,size,thumbnailLink",
        ).execute()

        return result.get("id"), result.get("webViewLink")
    except Exception as e:
        logger.error("Failed to upload file to Drive: %s", e)
        return None, None


def list_drive_files(user_id=None, page_token=None, page_size=20):
    """List files in the user's Drive (scoped to app-created files with drive.file)."""
    service = build_service("drive", "v3", user_id=user_id)
    if not service:
        return [], None

    try:
        result = service.files().list(
            pageSize=page_size,
            pageToken=page_token,
            fields="nextPageToken,files(id,name,mimeType,size,webViewLink,thumbnailLink,createdTime)",
            orderBy="createdTime desc",
        ).execute()

        files = result.get("files", [])
        next_token = result.get("nextPageToken")
        return files, next_token
    except Exception as e:
        logger.error("Failed to list Drive files: %s", e)
        return [], None


def set_file_sharing(file_id, role="reader", share_type="anyone", user_id=None):
    """Set sharing permissions on a Drive file."""
    service = build_service("drive", "v3", user_id=user_id)
    if not service:
        return False

    try:
        permission = {"type": share_type, "role": role}
        service.permissions().create(
            fileId=file_id,
            body=permission,
        ).execute()
        return True
    except Exception as e:
        logger.error("Failed to set sharing on file %s: %s", file_id, e)
        return False
