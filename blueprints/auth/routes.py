import time as _time
from collections import defaultdict

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from blueprints.auth import auth_bp
from models.user import User

# ── Simple rate limiting (in-memory, per-IP) ────────────────────
_failed_attempts = defaultdict(list)
_LOCKOUT_WINDOW = 30  # seconds
_MAX_FAILURES = 5


def _is_locked_out(ip):
    now = _time.time()
    attempts = _failed_attempts[ip]
    # Prune old entries
    _failed_attempts[ip] = [t for t in attempts if now - t < _LOCKOUT_WINDOW]
    return len(_failed_attempts[ip]) >= _MAX_FAILURES


def _record_failure(ip):
    _failed_attempts[ip].append(_time.time())


def _clear_failures(ip):
    _failed_attempts.pop(ip, None)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        ip = request.remote_addr or "unknown"

        if _is_locked_out(ip):
            flash("Too many failed attempts. Please wait 30 seconds.", "danger")
            return render_template("auth/login.html"), 429

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = "remember" in request.form

        user = User.query.filter_by(username=username).first()

        if user and user.is_active_user and user.check_password(password):
            _clear_failures(ip)
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.dashboard"))

        _record_failure(ip)
        flash("Invalid username or password.", "danger")
        return render_template("auth/login.html")

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
