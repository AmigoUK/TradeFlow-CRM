import re

from flask import flash, jsonify, redirect, render_template, request, url_for

from blueprints.auth.decorators import role_required
from blueprints.settings import settings_bp
from extensions import db
from models import (
    QuickFunction, AppSettings, InteractionType, Contact, CustomFieldDefinition,
    AttachmentCategory, AttachmentTag, Attachment, GoogleOAuthConfig, DocTemplate,
)


def _is_ajax():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@settings_bp.route("/")
@role_required("admin")
def settings_page():
    quick_functions = QuickFunction.query.order_by(
        QuickFunction.sort_order, QuickFunction.id
    ).all()
    interaction_types = InteractionType.query.order_by(
        InteractionType.sort_order, InteractionType.id
    ).all()
    custom_fields = CustomFieldDefinition.query.order_by(
        CustomFieldDefinition.sort_order, CustomFieldDefinition.id
    ).all()
    attachment_categories = AttachmentCategory.query.order_by(
        AttachmentCategory.sort_order, AttachmentCategory.id
    ).all()
    attachment_tags = AttachmentTag.query.order_by(
        AttachmentTag.sort_order, AttachmentTag.id
    ).all()
    settings = AppSettings.get()
    google_config = GoogleOAuthConfig.get()
    doc_templates = DocTemplate.query.order_by(DocTemplate.sort_order, DocTemplate.id).all()
    return render_template(
        "settings/index.html",
        quick_functions=quick_functions,
        interaction_types=interaction_types,
        custom_fields=custom_fields,
        attachment_categories=attachment_categories,
        attachment_tags=attachment_tags,
        settings=settings,
        google_config=google_config,
        doc_templates=doc_templates,
    )


# ── Quick Functions ──────────────────────────────────────────────

@settings_bp.route("/quick-functions/new", methods=["POST"])
@role_required("admin")
def create_quick_function():
    label = request.form.get("label", "").strip()
    if not label:
        flash("Label is required.", "danger")
        return redirect(url_for("settings.settings_page"))

    icon = request.form.get("icon", "bi-lightning-charge").strip()
    if not icon.startswith("bi-"):
        icon = "bi-" + icon

    max_order = db.session.query(db.func.max(QuickFunction.sort_order)).scalar() or 0

    qf = QuickFunction(
        label=label,
        icon=icon,
        contact_type=request.form.get("contact_type", "phone"),
        notes=request.form.get("notes", "").strip(),
        outcome=request.form.get("outcome", "").strip(),
        sort_order=max_order + 1,
    )
    db.session.add(qf)
    db.session.commit()
    flash(f"Quick function '{qf.label}' created.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/quick-functions/<int:id>/edit", methods=["POST"])
@role_required("admin")
def edit_quick_function(id):
    qf = db.get_or_404(QuickFunction, id)

    label = request.form.get("label", "").strip()
    if not label:
        flash("Label is required.", "danger")
        return redirect(url_for("settings.settings_page"))

    icon = request.form.get("icon", qf.icon).strip()
    if not icon.startswith("bi-"):
        icon = "bi-" + icon

    qf.label = label
    qf.icon = icon
    qf.contact_type = request.form.get("contact_type", qf.contact_type)
    qf.notes = request.form.get("notes", "").strip()
    qf.outcome = request.form.get("outcome", "").strip()
    db.session.commit()
    flash(f"Quick function '{qf.label}' updated.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/quick-functions/<int:id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_quick_function(id):
    qf = db.get_or_404(QuickFunction, id)
    qf.is_active = not qf.is_active
    db.session.commit()

    state = "activated" if qf.is_active else "deactivated"
    if _is_ajax():
        return jsonify({"ok": True, "is_active": qf.is_active, "message": f"'{qf.label}' {state}."})

    flash(f"'{qf.label}' {state}.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/quick-functions/<int:id>/delete", methods=["POST"])
@role_required("admin")
def delete_quick_function(id):
    qf = db.get_or_404(QuickFunction, id)
    label = qf.label
    db.session.delete(qf)
    db.session.commit()
    flash(f"Quick function '{label}' deleted.", "success")
    return redirect(url_for("settings.settings_page"))


# ── Interaction Types ────────────────────────────────────────────

def _validate_colour(colour):
    return bool(re.match(r"^#[0-9a-fA-F]{6}$", colour))


@settings_bp.route("/interaction-types/new", methods=["POST"])
@role_required("admin")
def create_interaction_type():
    label = request.form.get("label", "").strip().lower()
    if not label:
        flash("Label is required.", "danger")
        return redirect(url_for("settings.settings_page"))

    if InteractionType.query.filter_by(label=label).first():
        flash(f"Interaction type '{label}' already exists.", "danger")
        return redirect(url_for("settings.settings_page"))

    icon = request.form.get("icon", "bi-chat-dots").strip()
    if not icon.startswith("bi-"):
        icon = "bi-" + icon

    colour = request.form.get("colour", "#0d6efd").strip()
    if not _validate_colour(colour):
        colour = "#0d6efd"

    max_order = db.session.query(db.func.max(InteractionType.sort_order)).scalar() or 0

    it = InteractionType(
        label=label,
        icon=icon,
        colour=colour,
        sort_order=max_order + 1,
    )
    db.session.add(it)
    db.session.commit()
    flash(f"Interaction type '{it.label}' created.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/interaction-types/<int:id>/edit", methods=["POST"])
@role_required("admin")
def edit_interaction_type(id):
    it = db.get_or_404(InteractionType, id)

    label = request.form.get("label", "").strip().lower()
    if not label:
        flash("Label is required.", "danger")
        return redirect(url_for("settings.settings_page"))

    # Check uniqueness if label changed
    if label != it.label:
        existing = InteractionType.query.filter_by(label=label).first()
        if existing:
            flash(f"Interaction type '{label}' already exists.", "danger")
            return redirect(url_for("settings.settings_page"))
        # Update any existing contacts using the old label
        Contact.query.filter_by(contact_type=it.label).update({"contact_type": label})

    icon = request.form.get("icon", it.icon).strip()
    if not icon.startswith("bi-"):
        icon = "bi-" + icon

    colour = request.form.get("colour", it.colour).strip()
    if not _validate_colour(colour):
        colour = it.colour

    it.label = label
    it.icon = icon
    it.colour = colour
    db.session.commit()
    flash(f"Interaction type '{it.label}' updated.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/interaction-types/<int:id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_interaction_type(id):
    it = db.get_or_404(InteractionType, id)
    it.is_active = not it.is_active
    db.session.commit()

    state = "activated" if it.is_active else "deactivated"
    if _is_ajax():
        return jsonify({"ok": True, "is_active": it.is_active, "message": f"'{it.label}' {state}."})

    flash(f"'{it.label}' {state}.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/interaction-types/<int:id>/delete", methods=["POST"])
@role_required("admin")
def delete_interaction_type(id):
    it = db.get_or_404(InteractionType, id)

    # Refuse deletion if any contacts use this type
    in_use = Contact.query.filter_by(contact_type=it.label).first()
    if in_use:
        flash(f"Cannot delete '{it.label}' — it is used by existing interactions. Deactivate it instead.", "danger")
        return redirect(url_for("settings.settings_page"))

    label = it.label
    db.session.delete(it)
    db.session.commit()
    flash(f"Interaction type '{label}' deleted.", "success")
    return redirect(url_for("settings.settings_page"))


# ── Custom Fields ────────────────────────────────────────────────

@settings_bp.route("/custom-fields/new", methods=["POST"])
@role_required("admin")
def create_custom_field():
    label = request.form.get("label", "").strip()
    if not label:
        flash("Label is required.", "danger")
        return redirect(url_for("settings.settings_page"))

    icon = request.form.get("icon", "bi-input-cursor-text").strip()
    if not icon.startswith("bi-"):
        icon = "bi-" + icon

    field_type = request.form.get("field_type", "text")
    if field_type not in ("text", "textarea", "url"):
        field_type = "text"

    max_order = db.session.query(db.func.max(CustomFieldDefinition.sort_order)).scalar() or 0

    cf = CustomFieldDefinition(
        label=label,
        icon=icon,
        field_type=field_type,
        sort_order=max_order + 1,
    )
    db.session.add(cf)
    db.session.commit()
    flash(f"Custom field '{cf.label}' created.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/custom-fields/<int:id>/edit", methods=["POST"])
@role_required("admin")
def edit_custom_field(id):
    cf = db.get_or_404(CustomFieldDefinition, id)

    label = request.form.get("label", "").strip()
    if not label:
        flash("Label is required.", "danger")
        return redirect(url_for("settings.settings_page"))

    icon = request.form.get("icon", cf.icon).strip()
    if not icon.startswith("bi-"):
        icon = "bi-" + icon

    field_type = request.form.get("field_type", cf.field_type)
    if field_type not in ("text", "textarea", "url"):
        field_type = cf.field_type

    cf.label = label
    cf.icon = icon
    cf.field_type = field_type
    db.session.commit()
    flash(f"Custom field '{cf.label}' updated.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/custom-fields/<int:id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_custom_field(id):
    cf = db.get_or_404(CustomFieldDefinition, id)
    cf.is_active = not cf.is_active
    db.session.commit()

    state = "activated" if cf.is_active else "deactivated"
    if _is_ajax():
        return jsonify({"ok": True, "is_active": cf.is_active, "message": f"'{cf.label}' {state}."})

    flash(f"'{cf.label}' {state}.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/custom-fields/<int:id>/delete", methods=["POST"])
@role_required("admin")
def delete_custom_field(id):
    cf = db.get_or_404(CustomFieldDefinition, id)
    label = cf.label
    db.session.delete(cf)
    db.session.commit()
    flash(f"Custom field '{label}' and all its values deleted.", "success")
    return redirect(url_for("settings.settings_page"))


# ── Theme ────────────────────────────────────────────────────────

# ── Attachment Categories ────────────────────────────────────────

@settings_bp.route("/attachment-categories/new", methods=["POST"])
@role_required("admin")
def create_attachment_category():
    label = request.form.get("label", "").strip()
    if not label:
        flash("Label is required.", "danger")
        return redirect(url_for("settings.settings_page"))

    if AttachmentCategory.query.filter_by(label=label).first():
        flash(f"Attachment category '{label}' already exists.", "danger")
        return redirect(url_for("settings.settings_page"))

    icon = request.form.get("icon", "bi-folder").strip()
    if not icon.startswith("bi-"):
        icon = "bi-" + icon

    colour = request.form.get("colour", "#6c757d").strip()
    if not _validate_colour(colour):
        colour = "#6c757d"

    max_order = db.session.query(db.func.max(AttachmentCategory.sort_order)).scalar() or 0

    ac = AttachmentCategory(
        label=label,
        icon=icon,
        colour=colour,
        sort_order=max_order + 1,
    )
    db.session.add(ac)
    db.session.commit()
    flash(f"Attachment category '{ac.label}' created.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/attachment-categories/<int:id>/edit", methods=["POST"])
@role_required("admin")
def edit_attachment_category(id):
    ac = db.get_or_404(AttachmentCategory, id)

    label = request.form.get("label", "").strip()
    if not label:
        flash("Label is required.", "danger")
        return redirect(url_for("settings.settings_page"))

    if label != ac.label:
        existing = AttachmentCategory.query.filter_by(label=label).first()
        if existing:
            flash(f"Attachment category '{label}' already exists.", "danger")
            return redirect(url_for("settings.settings_page"))

    icon = request.form.get("icon", ac.icon).strip()
    if not icon.startswith("bi-"):
        icon = "bi-" + icon

    colour = request.form.get("colour", ac.colour).strip()
    if not _validate_colour(colour):
        colour = ac.colour

    ac.label = label
    ac.icon = icon
    ac.colour = colour
    db.session.commit()
    flash(f"Attachment category '{ac.label}' updated.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/attachment-categories/<int:id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_attachment_category(id):
    ac = db.get_or_404(AttachmentCategory, id)
    ac.is_active = not ac.is_active
    db.session.commit()

    state = "activated" if ac.is_active else "deactivated"
    if _is_ajax():
        return jsonify({"ok": True, "is_active": ac.is_active, "message": f"'{ac.label}' {state}."})

    flash(f"'{ac.label}' {state}.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/attachment-categories/<int:id>/delete", methods=["POST"])
@role_required("admin")
def delete_attachment_category(id):
    ac = db.get_or_404(AttachmentCategory, id)
    label = ac.label

    # SET NULL on attachments using this category
    Attachment.query.filter_by(category_id=ac.id).update({"category_id": None})
    db.session.delete(ac)
    db.session.commit()
    flash(f"Attachment category '{label}' deleted.", "success")
    return redirect(url_for("settings.settings_page"))


# ── Attachment Tags ─────────────────────────────────────────────

@settings_bp.route("/attachment-tags/new", methods=["POST"])
@role_required("admin")
def create_attachment_tag():
    label = request.form.get("label", "").strip()
    if not label:
        flash("Label is required.", "danger")
        return redirect(url_for("settings.settings_page"))

    if AttachmentTag.query.filter_by(label=label).first():
        flash(f"Attachment tag '{label}' already exists.", "danger")
        return redirect(url_for("settings.settings_page"))

    colour = request.form.get("colour", "#6c757d").strip()
    if not _validate_colour(colour):
        colour = "#6c757d"

    max_order = db.session.query(db.func.max(AttachmentTag.sort_order)).scalar() or 0

    at = AttachmentTag(
        label=label,
        colour=colour,
        sort_order=max_order + 1,
    )
    db.session.add(at)
    db.session.commit()
    flash(f"Attachment tag '{at.label}' created.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/attachment-tags/<int:id>/edit", methods=["POST"])
@role_required("admin")
def edit_attachment_tag(id):
    at = db.get_or_404(AttachmentTag, id)

    label = request.form.get("label", "").strip()
    if not label:
        flash("Label is required.", "danger")
        return redirect(url_for("settings.settings_page"))

    if label != at.label:
        existing = AttachmentTag.query.filter_by(label=label).first()
        if existing:
            flash(f"Attachment tag '{label}' already exists.", "danger")
            return redirect(url_for("settings.settings_page"))

    colour = request.form.get("colour", at.colour).strip()
    if not _validate_colour(colour):
        colour = at.colour

    at.label = label
    at.colour = colour
    db.session.commit()
    flash(f"Attachment tag '{at.label}' updated.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/attachment-tags/<int:id>/toggle", methods=["POST"])
@role_required("admin")
def toggle_attachment_tag(id):
    at = db.get_or_404(AttachmentTag, id)
    at.is_active = not at.is_active
    db.session.commit()

    state = "activated" if at.is_active else "deactivated"
    if _is_ajax():
        return jsonify({"ok": True, "is_active": at.is_active, "message": f"'{at.label}' {state}."})

    flash(f"'{at.label}' {state}.", "success")
    return redirect(url_for("settings.settings_page"))


@settings_bp.route("/attachment-tags/<int:id>/delete", methods=["POST"])
@role_required("admin")
def delete_attachment_tag(id):
    at = db.get_or_404(AttachmentTag, id)
    label = at.label
    # M2M rows cascade automatically via the association table
    db.session.delete(at)
    db.session.commit()
    flash(f"Attachment tag '{label}' deleted.", "success")
    return redirect(url_for("settings.settings_page"))


# ── Theme ────────────────────────────────────────────────────────

@settings_bp.route("/ui-preferences", methods=["POST"])
@role_required("admin")
def update_ui_preferences():
    data = request.get_json(silent=True) or {}
    settings = AppSettings.get()
    if "sticky_navbar" in data:
        settings.sticky_navbar = bool(data["sticky_navbar"])
    if "pagination_enabled" in data:
        settings.pagination_enabled = bool(data["pagination_enabled"])
    if "pagination_size" in data:
        size = int(data["pagination_size"])
        if size in (10, 25, 50, 100):
            settings.pagination_size = size
    if "back_to_top" in data:
        settings.back_to_top = bool(data["back_to_top"])
    db.session.commit()
    return jsonify({"ok": True})


@settings_bp.route("/theme", methods=["POST"])
@role_required("admin")
def update_theme():
    data = request.get_json(silent=True) or {}
    theme = data.get("theme", "light")
    if theme not in ("light", "dark", "auto"):
        return jsonify({"ok": False, "error": "Invalid theme."}), 400

    settings = AppSettings.get()
    settings.theme = theme
    db.session.commit()
    return jsonify({"ok": True, "theme": theme})
