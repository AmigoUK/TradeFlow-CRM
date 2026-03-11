from flask import render_template, request

from blueprints.followups import followups_bp


@followups_bp.route("/")
def list_followups():
    return render_template("followups/list.html")


@followups_bp.route("/new")
def create_followup():
    client_id = request.args.get("client_id")
    return render_template("followups/list.html")
