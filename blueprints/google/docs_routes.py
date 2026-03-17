"""Google Docs routes — create, link, unlink documents."""

from flask import flash, jsonify, redirect, request, url_for
from flask_login import current_user, login_required

from blueprints.auth.decorators import role_required
from blueprints.google import google_bp
from blueprints.google.docs_service import create_blank_document, create_from_template
from blueprints.google.google_service import google_required
from extensions import db
from models.doc_template import DocTemplate
from models.google_doc import GoogleDoc


@google_bp.route("/docs/create", methods=["POST"])
@login_required
@google_required
def create_doc():
    """Create a Google Doc (blank or from template) and link to a CRM record."""
    title = request.form.get("doc_title", "").strip() or "Untitled Document"
    template_id = request.form.get("template_id", "").strip()
    company_id = request.form.get("company_id")
    interaction_id = request.form.get("interaction_id")
    followup_id = request.form.get("followup_id")

    if template_id:
        template = db.session.get(DocTemplate, int(template_id))
        if template:
            doc_id, url = create_from_template(
                template.google_template_doc_id, title, current_user.id
            )
        else:
            flash("Template not found.", "danger")
            return redirect(request.referrer or url_for("dashboard.dashboard"))
    else:
        doc_id, url = create_blank_document(title, current_user.id)

    if not doc_id:
        flash("Failed to create Google Doc.", "danger")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    google_doc = GoogleDoc(
        google_doc_id=doc_id,
        title=title,
        google_url=url,
        doc_type="document",
        company_id=int(company_id) if company_id else None,
        interaction_id=int(interaction_id) if interaction_id else None,
        followup_id=int(followup_id) if followup_id else None,
        created_by_user_id=current_user.id,
    )
    db.session.add(google_doc)
    db.session.commit()

    flash(f"Google Doc '{title}' created.", "success")
    if company_id:
        return redirect(url_for("companies.detail_company", id=int(company_id)))
    return redirect(request.referrer or url_for("dashboard.dashboard"))


@google_bp.route("/docs/link", methods=["POST"])
@login_required
@google_required
def link_doc():
    """Link an existing Google Doc to a CRM record."""
    google_doc_id = request.form.get("google_doc_id", "").strip()
    title = request.form.get("doc_title", "").strip() or "Linked Document"
    google_url = request.form.get("google_url", "").strip()
    doc_type = request.form.get("doc_type", "document")
    company_id = request.form.get("company_id")
    interaction_id = request.form.get("interaction_id")
    followup_id = request.form.get("followup_id")

    if not google_doc_id:
        flash("Google Doc ID is required.", "danger")
        return redirect(request.referrer or url_for("dashboard.dashboard"))

    if not google_url:
        google_url = f"https://docs.google.com/document/d/{google_doc_id}/edit"

    google_doc = GoogleDoc(
        google_doc_id=google_doc_id,
        title=title,
        google_url=google_url,
        doc_type=doc_type,
        company_id=int(company_id) if company_id else None,
        interaction_id=int(interaction_id) if interaction_id else None,
        followup_id=int(followup_id) if followup_id else None,
        created_by_user_id=current_user.id,
    )
    db.session.add(google_doc)
    db.session.commit()

    flash(f"Document '{title}' linked.", "success")
    if company_id:
        return redirect(url_for("companies.detail_company", id=int(company_id)))
    return redirect(request.referrer or url_for("dashboard.dashboard"))


@google_bp.route("/docs/<int:id>/unlink", methods=["POST"])
@login_required
def unlink_doc(id):
    """Remove a Google Doc link from CRM (does not delete the doc in Google)."""
    doc = db.get_or_404(GoogleDoc, id)
    company_id = doc.company_id
    title = doc.title
    db.session.delete(doc)
    db.session.commit()

    flash(f"Document '{title}' unlinked.", "success")
    if company_id:
        return redirect(url_for("companies.detail_company", id=company_id))
    return redirect(request.referrer or url_for("dashboard.dashboard"))


@google_bp.route("/docs/templates")
@login_required
def list_templates():
    """JSON: available document templates."""
    templates = DocTemplate.query.filter_by(is_active=True).order_by(
        DocTemplate.sort_order, DocTemplate.id
    ).all()
    return jsonify([{
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "template_type": t.template_type,
    } for t in templates])


# ── Admin: Doc Template Management ───────────────────────────────


@google_bp.route("/docs/templates/new", methods=["POST"])
@role_required("admin")
def create_template():
    """Create a new doc template."""
    name = request.form.get("template_name", "").strip()
    if not name:
        flash("Template name is required.", "danger")
        return redirect(url_for("settings.settings_page"))

    max_order = db.session.query(db.func.max(DocTemplate.sort_order)).scalar() or 0

    template = DocTemplate(
        name=name,
        description=request.form.get("template_description", "").strip(),
        google_template_doc_id=request.form.get("template_doc_id", "").strip(),
        template_type=request.form.get("template_type", "meeting_notes"),
        sort_order=max_order + 1,
    )
    db.session.add(template)
    db.session.commit()
    flash(f"Template '{name}' created.", "success")
    return redirect(url_for("settings.settings_page"))


@google_bp.route("/docs/templates/<int:id>/delete", methods=["POST"])
@role_required("admin")
def delete_template(id):
    """Delete a doc template."""
    template = db.get_or_404(DocTemplate, id)
    name = template.name
    db.session.delete(template)
    db.session.commit()
    flash(f"Template '{name}' deleted.", "success")
    return redirect(url_for("settings.settings_page"))


@google_bp.route("/docs/templates/<int:id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_template(id):
    """Toggle a doc template active/inactive."""
    template = db.get_or_404(DocTemplate, id)
    template.is_active = not template.is_active
    db.session.commit()
    state = "activated" if template.is_active else "deactivated"
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"ok": True, "is_active": template.is_active, "message": f"'{template.name}' {state}."})
    flash(f"'{template.name}' {state}.", "success")
    return redirect(url_for("settings.settings_page"))
