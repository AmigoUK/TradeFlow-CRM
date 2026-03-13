"""Google OAuth2 routes — connect, callback, disconnect, status, and admin config."""

import secrets

from flask import current_app, flash, jsonify, redirect, request, session, url_for
from flask_login import current_user, login_required

from blueprints.auth.decorators import role_required
from blueprints.google import google_bp
from blueprints.google.google_service import (
    decrypt_client_secret,
    decrypt_token,
    encrypt_client_secret,
    encrypt_token,
    is_google_connected,
    is_google_enabled,
)
from extensions import db
from models.google_credential import GoogleCredential
from models.google_oauth_config import GoogleOAuthConfig


# ── Admin config routes ─────────────────────────────────────────


@google_bp.route("/config", methods=["POST"])
@role_required("admin")
def save_config():
    """Save Google OAuth configuration (admin only)."""
    config = GoogleOAuthConfig.get()

    client_id = request.form.get("google_client_id", "").strip()
    client_secret = request.form.get("google_client_secret", "").strip()
    is_enabled = "google_enabled" in request.form

    # Build scopes from checkboxes
    scope_parts = ["https://www.googleapis.com/auth/userinfo.email"]
    if "scope_calendar" in request.form:
        scope_parts.append("https://www.googleapis.com/auth/calendar")
    if "scope_docs" in request.form:
        scope_parts.append("https://www.googleapis.com/auth/documents")
    if "scope_drive" in request.form:
        scope_parts.append("https://www.googleapis.com/auth/drive.file")

    config.client_id = client_id
    # Only update secret if a new one was provided (not the placeholder)
    if client_secret and client_secret != "••••••••":
        config.client_secret_encrypted = encrypt_client_secret(client_secret)
    config.scopes = " ".join(scope_parts)
    config.is_enabled = is_enabled

    db.session.commit()
    flash("Google integration settings saved.", "success")
    return redirect(url_for("settings.settings_page"))


# ── OAuth flow routes ────────────────────────────────────────────


@google_bp.route("/connect")
@login_required
def connect():
    """Initiate OAuth2 flow — redirect user to Google consent screen."""
    if not is_google_enabled():
        flash("Google integration is not enabled.", "warning")
        return redirect(url_for("dashboard.dashboard"))

    config = GoogleOAuthConfig.get()
    client_secret = decrypt_client_secret(config.client_secret_encrypted)

    if not config.client_id or not client_secret:
        flash("Google integration is not properly configured.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    # Generate and store state for CSRF protection
    state = secrets.token_urlsafe(32)
    session["google_oauth_state"] = state

    try:
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": config.client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [url_for("google.callback", _external=True)],
                }
            },
            scopes=config.scopes.split(" "),
        )
        flow.redirect_uri = url_for("google.callback", _external=True)

        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )

        return redirect(authorization_url)
    except Exception as e:
        current_app.logger.error("OAuth connect failed: %s", e)
        flash("Failed to initiate Google sign-in. Please try again.", "danger")
        return redirect(url_for("dashboard.dashboard"))


@google_bp.route("/callback")
@login_required
def callback():
    """Handle OAuth2 callback — store encrypted tokens."""
    # Verify state for CSRF protection
    stored_state = session.pop("google_oauth_state", None)
    received_state = request.args.get("state")

    if not stored_state or stored_state != received_state:
        flash("Invalid OAuth state. Please try again.", "danger")
        return redirect(url_for("dashboard.dashboard"))

    error = request.args.get("error")
    if error:
        flash(f"Google authorisation denied: {error}", "warning")
        return redirect(url_for("dashboard.dashboard"))

    config = GoogleOAuthConfig.get()
    client_secret = decrypt_client_secret(config.client_secret_encrypted)

    try:
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": config.client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [url_for("google.callback", _external=True)],
                }
            },
            scopes=config.scopes.split(" "),
        )
        flow.redirect_uri = url_for("google.callback", _external=True)
        flow.fetch_token(authorization_response=request.url)

        credentials = flow.credentials

        # Fetch the user's Google email
        google_email = None
        try:
            from googleapiclient.discovery import build
            service = build("oauth2", "v2", credentials=credentials)
            user_info = service.userinfo().get().execute()
            google_email = user_info.get("email")
        except Exception:
            pass

        # Store or update credential
        cred = GoogleCredential.query.filter_by(user_id=current_user.id).first()
        if not cred:
            cred = GoogleCredential(user_id=current_user.id)
            db.session.add(cred)

        cred.access_token_encrypted = encrypt_token(credentials.token)
        cred.refresh_token_encrypted = encrypt_token(credentials.refresh_token) if credentials.refresh_token else cred.refresh_token_encrypted
        cred.token_expiry = credentials.expiry
        cred.granted_scopes = " ".join(credentials.scopes) if credentials.scopes else config.scopes
        cred.google_email = google_email
        cred.is_valid = True

        db.session.commit()
        flash(f"Google account connected: {google_email or 'unknown'}", "success")
    except Exception as e:
        current_app.logger.error("OAuth callback failed: %s", e)
        flash("Failed to complete Google sign-in. Please try again.", "danger")

    return redirect(url_for("dashboard.dashboard"))


@google_bp.route("/disconnect", methods=["POST"])
@login_required
def disconnect():
    """Revoke tokens and delete credential."""
    cred = GoogleCredential.query.filter_by(user_id=current_user.id).first()

    if cred:
        # Attempt to revoke the token with Google
        access_token = decrypt_token(cred.access_token_encrypted)
        if access_token:
            try:
                import requests as http_requests
                http_requests.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": access_token},
                    headers={"Content-type": "application/x-www-form-urlencoded"},
                    timeout=5,
                )
            except Exception:
                pass  # Best-effort revocation

        db.session.delete(cred)
        db.session.commit()
        flash("Google account disconnected.", "success")
    else:
        flash("No Google account connected.", "info")

    return redirect(url_for("dashboard.dashboard"))


@google_bp.route("/status")
@login_required
def status():
    """JSON: connection state for the current user."""
    cred = GoogleCredential.query.filter_by(user_id=current_user.id).first()
    return jsonify({
        "enabled": is_google_enabled(),
        "connected": is_google_connected(),
        "email": cred.google_email if cred and cred.is_valid else None,
        "valid": cred.is_valid if cred else False,
    })
