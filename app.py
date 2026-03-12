from datetime import date, timedelta

from flask import Flask

from config import Config
from extensions import db

APP_VERSION = "0.9.0-beta"


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


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Register Jinja2 template filters and globals
    app.jinja_env.filters["relative_date"] = relative_date
    app.jinja_env.filters["days_overdue"] = days_overdue
    app.jinja_env.globals["app_version"] = APP_VERSION

    from blueprints.dashboard import dashboard_bp
    from blueprints.clients import clients_bp
    from blueprints.contacts import contacts_bp
    from blueprints.followups import followups_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clients_bp, url_prefix="/clients")
    app.register_blueprint(contacts_bp, url_prefix="/contacts")
    app.register_blueprint(followups_bp, url_prefix="/followups")

    with app.app_context():
        from models import Client, Contact, FollowUp  # noqa: F401
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
