"""Admin-only routes for CSV import and export of CRM data."""

import csv
import io
import json
from datetime import date

from flask import (
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from blueprints.auth.decorators import role_required
from blueprints.data_io import data_io_bp
from blueprints.data_io.csv_service import (
    ENTITY_COLUMNS,
    generate_export_csv,
    generate_template_csv,
    validate_and_import,
)


def _csv_response(string_io, filename):
    """Return a downloadable CSV response."""
    return Response(
        string_io.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Export routes ──────────────────────────────────────────────


@data_io_bp.route("/export/clients")
@role_required("admin")
def export_clients():
    output = generate_export_csv("clients")
    return _csv_response(output, f"clients_{date.today().isoformat()}.csv")


@data_io_bp.route("/export/contacts")
@role_required("admin")
def export_contacts():
    output = generate_export_csv("contacts")
    return _csv_response(output, f"contacts_{date.today().isoformat()}.csv")


@data_io_bp.route("/export/followups")
@role_required("admin")
def export_followups():
    output = generate_export_csv("followups")
    return _csv_response(output, f"followups_{date.today().isoformat()}.csv")


# ── Template download ─────────────────────────────────────────


@data_io_bp.route("/template/<entity>")
@role_required("admin")
def download_template(entity):
    if entity not in ENTITY_COLUMNS:
        flash("Unknown entity type.", "danger")
        return redirect(url_for("settings.settings_page")), 404
    output = generate_template_csv(entity)
    return _csv_response(output, f"{entity}_template.csv")


# ── Import routes ──────────────────────────────────────────────


@data_io_bp.route("/import", methods=["GET"])
@role_required("admin")
def import_page():
    return render_template("settings/data_import.html")


@data_io_bp.route("/import", methods=["POST"])
@role_required("admin")
def process_import():
    from flask_login import current_user

    entity_type = request.form.get("entity_type", "").strip()
    if entity_type not in ENTITY_COLUMNS:
        flash("Please select a valid entity type.", "danger")
        return render_template("settings/data_import.html")

    file = request.files.get("csv_file")
    if not file or not file.filename:
        flash("Please select a CSV file to upload.", "danger")
        return render_template("settings/data_import.html")

    result = validate_and_import(entity_type, file.stream, current_user)

    # Store errors in session for download
    if result["errors"]:
        session["import_errors"] = json.dumps(result["errors"])
        session["import_errors_entity"] = entity_type
    else:
        session.pop("import_errors", None)
        session.pop("import_errors_entity", None)

    return render_template(
        "settings/data_import.html",
        result=result,
        entity_type=entity_type,
    )


@data_io_bp.route("/import/errors")
@role_required("admin")
def download_errors():
    errors_json = session.get("import_errors")
    if not errors_json:
        flash("No error report available.", "info")
        return redirect(url_for("data_io.import_page"))

    errors = json.loads(errors_json)
    entity_type = session.get("import_errors_entity", "unknown")

    output = io.StringIO()
    columns = ENTITY_COLUMNS.get(entity_type, [])
    fieldnames = ["row", "error"] + columns
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for err in errors:
        row_data = err.get("data", {})
        out_row = {
            "row": err.get("row", ""),
            "error": err.get("error", ""),
        }
        for col in columns:
            out_row[col] = row_data.get(col, "")
        writer.writerow(out_row)

    output.seek(0)
    return _csv_response(output, f"{entity_type}_import_errors.csv")
