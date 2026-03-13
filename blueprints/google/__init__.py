from flask import Blueprint

google_bp = Blueprint("google", __name__, template_folder="../../templates")

from blueprints.google import routes  # noqa: E402, F401
from blueprints.google import calendar_routes  # noqa: E402, F401
from blueprints.google import meet_routes  # noqa: E402, F401
from blueprints.google import docs_routes  # noqa: E402, F401
from blueprints.google import drive_routes  # noqa: E402, F401
