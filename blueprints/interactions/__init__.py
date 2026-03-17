from flask import Blueprint

interactions_bp = Blueprint("interactions", __name__, template_folder="../../templates")

from blueprints.interactions import routes  # noqa: E402, F401
