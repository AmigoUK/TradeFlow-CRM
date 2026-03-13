import os
from datetime import date, timedelta

from flask import Flask, render_template
from markupsafe import Markup

from config import Config
from extensions import csrf, db, login_manager

APP_VERSION = "0.23.0-beta"


def tel_link(value):
    """Jinja2 filter: render phone number as a clickable tel: link."""
    if value:
        safe_value = Markup.escape(value)
        return Markup(f'<a href="tel:{safe_value}">{safe_value}</a>')
    return "—"


def mailto_link(value):
    """Jinja2 filter: render email address as a clickable mailto: link."""
    if value:
        safe_value = Markup.escape(value)
        return Markup(f'<a href="mailto:{safe_value}">{safe_value}</a>')
    return "—"


def relative_date(d):
    """Jinja2 filter: render a date relative to today."""
    if d is None:
        return "—"
    today = date.today()
    if isinstance(d, str):
        return d
    # Handle datetime objects
    if hasattr(d, "date"):
        d = d.date()
    delta = (d - today).days

    if delta == 0:
        return "Today"
    if delta == -1:
        return "Yesterday"
    if delta == 1:
        return "Tomorrow"
    if -7 <= delta < -1:
        return f"{abs(delta)} days ago"
    if 1 < delta <= 7:
        return f"In {delta} days"
    if -14 <= delta < -7:
        return f"Last {d.strftime('%A')}"
    if 7 < delta <= 14:
        return f"Next {d.strftime('%A')}"
    return d.strftime("%d %b %Y")


def days_overdue(d):
    """Jinja2 filter: integer days overdue (positive) or until due (negative)."""
    if d is None:
        return 0
    today = date.today()
    if hasattr(d, "date"):
        d = d.date()
    return (today - d).days


def create_app(config_class=None):
    app = Flask(__name__)
    app.config.from_object(config_class or Config)

    db.init_app(app)

    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to access this page."
    login_manager.login_message_category = "info"

    # CSRF protection
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return db.session.get(User, int(user_id))

    # Register Jinja2 template filters and globals
    app.jinja_env.filters["relative_date"] = relative_date
    app.jinja_env.filters["days_overdue"] = days_overdue
    app.jinja_env.filters["tel_link"] = tel_link
    app.jinja_env.filters["mailto_link"] = mailto_link
    app.jinja_env.globals["app_version"] = APP_VERSION

    from blueprints.auth import auth_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.clients import clients_bp
    from blueprints.contacts import contacts_bp
    from blueprints.followups import followups_bp
    from blueprints.settings import settings_bp
    from blueprints.attachments import attachments_bp
    from blueprints.users import users_bp
    from blueprints.data_io import data_io_bp
    from blueprints.google import google_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clients_bp, url_prefix="/clients")
    app.register_blueprint(contacts_bp, url_prefix="/contacts")
    app.register_blueprint(followups_bp, url_prefix="/followups")
    app.register_blueprint(settings_bp, url_prefix="/settings")
    app.register_blueprint(attachments_bp, url_prefix="/attachments")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(data_io_bp, url_prefix="/settings/data")
    app.register_blueprint(google_bp, url_prefix="/google")

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    with app.app_context():
        from models import (  # noqa: F401
            Client, Contact, FollowUp, QuickFunction, DEFAULT_QUICK_FUNCTIONS,
            AppSettings, InteractionType, DEFAULT_INTERACTION_TYPES,
            CustomFieldDefinition, CustomFieldValue, DEFAULT_CUSTOM_FIELDS,
            AttachmentCategory, DEFAULT_ATTACHMENT_CATEGORIES,
            AttachmentTag, DEFAULT_ATTACHMENT_TAGS,
            Attachment,
            User, ROLES,
            GoogleOAuthConfig, GoogleCredential,
            GoogleCalendarSync,
            GoogleDoc, DocTemplate,
            GoogleDriveFile,
        )
        db.create_all()
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

        # ── Schema migration: add user_id columns if missing ────
        inspector = db.inspect(db.engine)
        for table_name in ("clients", "contacts", "followups"):
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            if "user_id" not in columns:
                db.session.execute(db.text(
                    f"ALTER TABLE {table_name} ADD COLUMN user_id INTEGER REFERENCES users(id)"
                ))

        # ── Schema migration: add meet_link columns ──────────
        for table_name in ("followups", "contacts"):
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            if "meet_link" not in columns:
                db.session.execute(db.text(
                    f"ALTER TABLE {table_name} ADD COLUMN meet_link VARCHAR(300)"
                ))

        # ── Schema migration: add storage_type and google_drive_file_id to attachments ──
        att_columns = [col["name"] for col in inspector.get_columns("attachments")]
        if "storage_type" not in att_columns:
            db.session.execute(db.text(
                "ALTER TABLE attachments ADD COLUMN storage_type VARCHAR(10) DEFAULT 'local'"
            ))
        if "google_drive_file_id" not in att_columns:
            db.session.execute(db.text(
                "ALTER TABLE attachments ADD COLUMN google_drive_file_id INTEGER"
            ))

        db.session.commit()

        # ── Seed default admin user if no users exist ───────────
        if User.query.count() == 0:
            admin = User(
                username="admin",
                display_name="Administrator",
                role="admin",
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()

        # ── Batch-assign orphan records to admin ────────────────
        admin_user = User.query.filter_by(role="admin").first()
        if admin_user:
            for model in (Client, Contact, FollowUp):
                model.query.filter(model.user_id.is_(None)).update(
                    {"user_id": admin_user.id}
                )
            db.session.commit()

        # Seed default quick functions if table is empty
        if QuickFunction.query.count() == 0:
            for i, qf_data in enumerate(DEFAULT_QUICK_FUNCTIONS):
                qf = QuickFunction(sort_order=i, **qf_data)
                db.session.add(qf)
            db.session.commit()

        # Seed default interaction types if table is empty
        if InteractionType.query.count() == 0:
            for i, it_data in enumerate(DEFAULT_INTERACTION_TYPES):
                it = InteractionType(sort_order=i, **it_data)
                db.session.add(it)
            db.session.commit()

        # Seed default custom field definitions if table is empty
        if CustomFieldDefinition.query.count() == 0:
            for i, cf_data in enumerate(DEFAULT_CUSTOM_FIELDS):
                cf = CustomFieldDefinition(sort_order=i, **cf_data)
                db.session.add(cf)
            db.session.commit()

        # Seed default attachment categories if table is empty
        if AttachmentCategory.query.count() == 0:
            for i, ac_data in enumerate(DEFAULT_ATTACHMENT_CATEGORIES):
                ac = AttachmentCategory(sort_order=i, **ac_data)
                db.session.add(ac)
            db.session.commit()

        # Seed default attachment tags if table is empty
        if AttachmentTag.query.count() == 0:
            for i, at_data in enumerate(DEFAULT_ATTACHMENT_TAGS):
                at = AttachmentTag(sort_order=i, **at_data)
                db.session.add(at)
            db.session.commit()

    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from models import AppSettings, InteractionType
        from blueprints.google.google_service import is_google_enabled, is_google_connected
        settings = AppSettings.get()
        active_types = InteractionType.query.filter_by(is_active=True).order_by(
            InteractionType.sort_order, InteractionType.id
        ).all()
        all_types = InteractionType.query.all()

        g_enabled = is_google_enabled()
        g_connected = False
        g_email = None
        if g_enabled and current_user and current_user.is_authenticated:
            from models.google_credential import GoogleCredential
            cred = GoogleCredential.query.filter_by(user_id=current_user.id, is_valid=True).first()
            if cred:
                g_connected = True
                g_email = cred.google_email

        return {
            "app_theme": settings.theme,
            "app_sticky_navbar": settings.sticky_navbar,
            "app_pagination_enabled": settings.pagination_enabled,
            "app_pagination_size": settings.pagination_size,
            "app_back_to_top": settings.back_to_top,
            "interaction_types_map": {t.label: {"icon": t.icon, "colour": t.colour} for t in all_types},
            "active_interaction_types": active_types,
            "google_enabled": g_enabled,
            "google_connected": g_connected,
            "google_email": g_email,
        }

    return app


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", message="resource_tracker:.*semaphore", category=UserWarning)
    app = create_app()
    app.run(debug=True, port=5001)
