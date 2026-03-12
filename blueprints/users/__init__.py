from flask import Blueprint

users_bp = Blueprint("users", __name__, template_folder="../../templates")

from blueprints.users import routes  # noqa: E402, F401
