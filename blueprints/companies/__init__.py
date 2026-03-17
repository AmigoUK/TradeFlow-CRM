from flask import Blueprint

companies_bp = Blueprint("companies", __name__, template_folder="../../templates")

from blueprints.companies import routes  # noqa: E402, F401
