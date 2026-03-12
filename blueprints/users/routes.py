from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from blueprints.auth.decorators import role_required
from blueprints.users import users_bp
from extensions import db
from models.user import ROLES, User
from models import Client, Contact, FollowUp


def _is_ajax():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@users_bp.route("/")
@role_required("manager")
def list_users():
    users = User.query.order_by(User.username).all()
    return render_template("users/list.html", users=users)


@users_bp.route("/new", methods=["GET", "POST"])
@role_required("manager")
def create_user():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        display_name = request.form.get("display_name", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "user")

        if not username or not display_name or not password:
            flash("Username, display name, and password are required.", "danger")
            return render_template("users/form.html", user=None, roles=ROLES)

        if User.query.filter_by(username=username).first():
            flash(f"Username '{username}' is already taken.", "danger")
            return render_template("users/form.html", user=None, roles=ROLES)

        # Managers can only create users with role=user
        if not current_user.has_role_at_least("admin") and role != "user":
            role = "user"

        user = User(username=username, display_name=display_name, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash(f"User '{user.display_name}' created successfully.", "success")
        return redirect(url_for("users.list_users"))

    return render_template("users/form.html", user=None, roles=ROLES)


@users_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@role_required("manager")
def edit_user(id):
    user = db.get_or_404(User, id)

    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        role = request.form.get("role", user.role)

        if not display_name:
            flash("Display name is required.", "danger")
            return render_template("users/form.html", user=user, roles=ROLES)

        # Managers cannot change roles to anything above user
        if not current_user.has_role_at_least("admin") and role != "user":
            role = user.role

        user.display_name = display_name
        user.role = role
        db.session.commit()

        flash(f"User '{user.display_name}' updated successfully.", "success")
        return redirect(url_for("users.list_users"))

    return render_template("users/form.html", user=user, roles=ROLES)


@users_bp.route("/<int:id>/toggle", methods=["POST"])
@role_required("manager")
def toggle_user(id):
    user = db.get_or_404(User, id)

    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("users.list_users"))

    user.is_active_user = not user.is_active_user
    db.session.commit()

    state = "activated" if user.is_active_user else "deactivated"
    flash(f"User '{user.display_name}' {state}.", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/<int:id>/reset-password", methods=["POST"])
@role_required("manager")
def reset_password(id):
    user = db.get_or_404(User, id)
    new_password = request.form.get("new_password", "").strip()

    if not new_password:
        flash("Password cannot be empty.", "danger")
        return redirect(url_for("users.list_users"))

    user.set_password(new_password)
    db.session.commit()

    flash(f"Password for '{user.display_name}' has been reset.", "success")
    return redirect(url_for("users.list_users"))


@users_bp.route("/<int:id>/delegate", methods=["POST"])
@role_required("manager")
def delegate_records(id):
    """Transfer ALL records from user <id> to the target user."""
    source_user = db.get_or_404(User, id)
    target_user_id = request.form.get("target_user_id")

    if not target_user_id:
        flash("Please select a target user.", "danger")
        return redirect(url_for("users.list_users"))

    target_user_id = int(target_user_id)
    target_user = db.get_or_404(User, target_user_id)

    if source_user.id == target_user.id:
        flash("Source and target users must be different.", "danger")
        return redirect(url_for("users.list_users"))

    # Transfer all records
    Client.query.filter_by(user_id=source_user.id).update({"user_id": target_user.id})
    Contact.query.filter_by(user_id=source_user.id).update({"user_id": target_user.id})
    FollowUp.query.filter_by(user_id=source_user.id).update({"user_id": target_user.id})
    db.session.commit()

    flash(
        f"All records from '{source_user.display_name}' transferred to '{target_user.display_name}'.",
        "success",
    )
    return redirect(url_for("users.list_users"))
