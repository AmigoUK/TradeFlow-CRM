from flask import Blueprint

data_io_bp = Blueprint("data_io", __name__, template_folder="../../templates")

from blueprints.data_io import routes  # noqa: E402, F401
