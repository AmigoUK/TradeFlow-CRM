"""Google OAuth2 service — token encryption, credential building, and refresh logic."""

import base64
import hashlib
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app, flash, redirect, url_for
from flask_login import current_user

from extensions import db

logger = logging.getLogger(__name__)


def _get_fernet():
    """Derive a Fernet key from Flask SECRET_KEY via PBKDF2."""
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    # Use PBKDF2 to derive a 32-byte key, then base64-encode for Fernet
    dk = hashlib.pbkdf2_hmac("sha256", secret, b"nextstep-google-tokens", 100_000)
    return Fernet(base64.urlsafe_b64encode(dk))


def encrypt_token(plaintext):
    """Encrypt a token string. Returns base64-encoded ciphertext."""
    if not plaintext:
        return None
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_token(ciphertext):
    """Decrypt a token string. Returns plaintext or None on failure."""
    if not ciphertext:
        return None
    try:
        f = _get_fernet()
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception) as e:
        logger.warning("Failed to decrypt token: %s", e)
        return None


def encrypt_client_secret(plaintext):
    """Encrypt the OAuth client secret for storage."""
    return encrypt_token(plaintext)


def decrypt_client_secret(ciphertext):
    """Decrypt the OAuth client secret."""
    return decrypt_token(ciphertext)


def get_google_credentials(user_id=None):
    """Build google.oauth2.credentials.Credentials for a user.

    Auto-refreshes expired tokens. Returns None if no valid credential exists.
    Sets is_valid=False if refresh permanently fails.
    """
    from models.google_credential import GoogleCredential
    from models.google_oauth_config import GoogleOAuthConfig

    uid = user_id or current_user.id
    cred = GoogleCredential.query.filter_by(user_id=uid).first()
    if not cred or not cred.is_valid:
        return None

    access_token = decrypt_token(cred.access_token_encrypted)
    refresh_token = decrypt_token(cred.refresh_token_encrypted)

    if not access_token and not refresh_token:
        return None

    config = GoogleOAuthConfig.get()
    client_secret = decrypt_client_secret(config.client_secret_encrypted)

    try:
        from google.oauth2.credentials import Credentials

        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=config.client_id,
            client_secret=client_secret,
            scopes=cred.granted_scopes.split(" ") if cred.granted_scopes else [],
        )

        # Check if token is expired and refresh if needed
        if cred.token_expiry and datetime.utcnow() >= cred.token_expiry:
            if refresh_token:
                try:
                    from google.auth.transport.requests import Request
                    credentials.refresh(Request())
                    # Update stored tokens
                    cred.access_token_encrypted = encrypt_token(credentials.token)
                    cred.token_expiry = credentials.expiry
                    db.session.commit()
                except Exception as e:
                    logger.error("Token refresh failed: %s", e)
                    cred.is_valid = False
                    db.session.commit()
                    return None
            else:
                cred.is_valid = False
                db.session.commit()
                return None

        return credentials
    except Exception as e:
        logger.error("Failed to build Google credentials: %s", e)
        return None


def build_service(api_name, api_version, user_id=None):
    """Build a Google API service client.

    Returns None if credentials are unavailable.
    """
    credentials = get_google_credentials(user_id)
    if not credentials:
        return None

    try:
        from googleapiclient.discovery import build
        return build(api_name, api_version, credentials=credentials)
    except Exception as e:
        logger.error("Failed to build %s service: %s", api_name, e)
        return None


def is_google_enabled():
    """Check if Google integration is enabled and configured."""
    from models.google_oauth_config import GoogleOAuthConfig
    config = GoogleOAuthConfig.get()
    return config.is_enabled and config.is_configured


def is_google_connected(user_id=None):
    """Check if a user has a valid Google credential."""
    from models.google_credential import GoogleCredential
    uid = user_id or (current_user.id if current_user and current_user.is_authenticated else None)
    if not uid:
        return False
    cred = GoogleCredential.query.filter_by(user_id=uid, is_valid=True).first()
    return cred is not None


def google_required(f):
    """Decorator for routes that require a valid Google connection."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_google_enabled():
            flash("Google integration is not enabled. Please contact your administrator.", "warning")
            return redirect(url_for("dashboard.dashboard"))
        if not is_google_connected():
            flash("Please connect your Google account first.", "warning")
            return redirect(url_for("google.connect"))
        return f(*args, **kwargs)
    return decorated
