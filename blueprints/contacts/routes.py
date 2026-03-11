from flask import render_template, request

from blueprints.contacts import contacts_bp


@contacts_bp.route("/")
def list_contacts():
    return render_template("contacts/list.html")


@contacts_bp.route("/new")
def create_contact():
    client_id = request.args.get("client_id")
    return render_template("contacts/list.html")
