import os
import shutil
from datetime import date, datetime

from flask import abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from blueprints.auth.decorators import can_access_record, role_required
from blueprints.companies import companies_bp
from extensions import db
from models import Company, COMPANY_STATUSES, Interaction, FollowUp, QuickFunction, InteractionType, CustomFieldDefinition, CustomFieldValue, Attachment, AttachmentCategory, AttachmentTag, AppSettings, Contact
from models.user import User


def _is_ajax():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _ownership_filter(query, model):
    if current_user.has_role_at_least("manager"):
        return query
    return query.filter(model.user_id == current_user.id)


@companies_bp.route("/")
@login_required
def list_companies():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    view = request.args.get("view", "table")

    # Subqueries for last interaction and next follow-up per company
    last_interaction_sq = (
        db.session.query(
            Interaction.company_id,
            func.max(Interaction.date).label("last_interaction"),
        )
        .group_by(Interaction.company_id)
        .subquery()
    )

    next_followup_sq = (
        db.session.query(
            FollowUp.company_id,
            func.min(FollowUp.due_date).label("next_followup"),
        )
        .filter(FollowUp.completed == False)  # noqa: E712
        .group_by(FollowUp.company_id)
        .subquery()
    )

    query = (
        db.session.query(
            Company,
            last_interaction_sq.c.last_interaction,
            next_followup_sq.c.next_followup,
        )
        .outerjoin(last_interaction_sq, Company.id == last_interaction_sq.c.company_id)
        .outerjoin(next_followup_sq, Company.id == next_followup_sq.c.company_id)
        .options(joinedload(Company.owner))
    )

    # Ownership filter
    if not current_user.has_role_at_least("manager"):
        query = query.filter(Company.user_id == current_user.id)

    if q:
        query = query.filter(Company.company_name.ilike(f"%{q}%"))
    if status and view != "board":
        query = query.filter(Company.status == status)

    settings = AppSettings.get()
    page = request.args.get("page", 1, type=int)
    ordered = query.order_by(Company.company_name)

    if settings.pagination_enabled and view != "board":
        pagination = ordered.paginate(page=page, per_page=settings.pagination_size, error_out=False)
        results = pagination.items
    else:
        pagination = None
        results = ordered.all()

    # Attach computed dates to company objects for template access
    companies = []
    for company, last_interaction, next_followup in results:
        company.last_interaction = last_interaction
        company.next_followup = next_followup
        companies.append(company)

    active_qfs = QuickFunction.query.filter_by(is_active=True).order_by(
        QuickFunction.sort_order
    ).all()

    # Pass all_users for reassignment (Manager+)
    all_users = None
    if current_user.has_role_at_least("manager"):
        all_users = User.query.filter_by(is_active_user=True).order_by(User.display_name).all()

    return render_template(
        "companies/list.html",
        companies=companies,
        statuses=COMPANY_STATUSES,
        q=q,
        status=status,
        view=view,
        quick_functions=[qf.to_dict() for qf in active_qfs],
        pagination=pagination,
        all_users=all_users,
    )


@companies_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_company():
    active_custom_fields = CustomFieldDefinition.query.filter_by(is_active=True).order_by(
        CustomFieldDefinition.sort_order
    ).all()

    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        if not company_name:
            if _is_ajax():
                html = render_template(
                    "companies/_form_fields.html",
                    company=None,
                    statuses=COMPANY_STATUSES,
                    custom_fields=active_custom_fields,
                    custom_values={},
                    panel_mode=True,
                )
                return jsonify({"ok": False, "html": html})
            flash("Company name is required.", "danger")
            return render_template(
                "companies/form.html",
                company=None,
                statuses=COMPANY_STATUSES,
                custom_fields=active_custom_fields,
                custom_values={},
            )

        company = Company(
            company_name=company_name,
            industry=request.form.get("industry", "").strip(),
            phone=request.form.get("phone", "").strip(),
            email=request.form.get("email", "").strip(),
            contact_person=request.form.get("contact_person", "").strip(),
            status=request.form.get("status", "lead"),
            user_id=current_user.id,
        )
        db.session.add(company)
        db.session.flush()

        # Save custom field values
        for cf in active_custom_fields:
            val = request.form.get(f"custom_field_{cf.id}", "").strip()
            if val:
                db.session.add(CustomFieldValue(definition_id=cf.id, company_id=company.id, value=val))
        db.session.commit()

        if _is_ajax():
            return jsonify({
                "ok": True,
                "message": f"Company '{company.company_name}' created successfully.",
                "redirect": url_for("companies.detail_company", id=company.id),
            })

        flash(f"Company '{company.company_name}' created successfully.", "success")
        return redirect(url_for("companies.detail_company", id=company.id))

    if _is_ajax():
        return render_template(
            "companies/_form_fields.html",
            company=None,
            statuses=COMPANY_STATUSES,
            custom_fields=active_custom_fields,
            custom_values={},
            panel_mode=True,
        )

    return render_template(
        "companies/form.html",
        company=None,
        statuses=COMPANY_STATUSES,
        custom_fields=active_custom_fields,
        custom_values={},
    )


@companies_bp.route("/<int:id>")
@login_required
def detail_company(id):
    company = db.get_or_404(Company, id)
    if not can_access_record(company):
        abort(403)

    # Build unified timeline merging interactions + follow-ups
    types_map = {t.label: {"icon": t.icon, "colour": t.colour} for t in InteractionType.query.all()}
    timeline = []
    for c in company.interactions:
        type_info = types_map.get(c.interaction_type, {})
        timeline.append({
            "type": "interaction",
            "date": c.date,
            "time": c.time,
            "icon": type_info.get("icon", "bi-chat-dots"),
            "badge_class": f"badge-{c.interaction_type}",
            "badge_colour": type_info.get("colour", "#6c757d"),
            "badge_text": c.interaction_type.capitalize(),
            "notes": c.notes,
            "outcome": c.outcome,
            "edit_url": url_for("interactions.edit_interaction", id=c.id),
            "obj": c,
            "attachment_count": len(c.attachments),
            "contact_person": c.contact_person.full_name if c.contact_person else None,
        })
    for fu in company.followups:
        timeline.append({
            "type": "followup",
            "date": fu.due_date,
            "time": fu.due_time,
            "icon": "bi-calendar-check",
            "badge_class": f"badge-{fu.priority}",
            "badge_text": fu.priority.capitalize(),
            "notes": fu.notes,
            "completed": fu.completed,
            "is_overdue": fu.is_overdue,
            "edit_url": url_for("followups.edit_followup", id=fu.id),
            "complete_url": url_for("followups.complete_followup", id=fu.id),
            "obj": fu,
            "attachment_count": len(fu.attachments),
        })
    timeline.sort(key=lambda x: x["date"], reverse=True)

    # Summary dates
    interaction_dates = [c.date for c in company.interactions]
    last_interaction = max(interaction_dates) if interaction_dates else None
    pending_dates = [fu.due_date for fu in company.followups if not fu.completed]
    next_followup = min(pending_dates) if pending_dates else None

    # Relationship summary stats
    total_interactions = len(company.interactions)
    total_followups = len(company.followups)
    completed_followups = sum(1 for fu in company.followups if fu.completed)
    pending_followups = total_followups - completed_followups
    completion_rate = round((completed_followups / total_followups) * 100) if total_followups else 0

    # Custom field values for display
    active_custom_fields = CustomFieldDefinition.query.filter_by(is_active=True).order_by(
        CustomFieldDefinition.sort_order
    ).all()
    custom_values = {
        v.definition_id: v.value
        for v in CustomFieldValue.query.filter_by(company_id=company.id).all()
    }

    # All attachments for this company (direct + via interactions/followups)
    company_attachments = Attachment.query.filter_by(company_id=company.id).options(
        joinedload(Attachment.category),
        joinedload(Attachment.tags),
    ).order_by(Attachment.created_at.desc()).all()

    # Active categories and tags for upload/edit modals
    attachment_categories = AttachmentCategory.query.filter_by(is_active=True).order_by(
        AttachmentCategory.sort_order
    ).all()
    attachment_tags = AttachmentTag.query.filter_by(is_active=True).order_by(
        AttachmentTag.sort_order
    ).all()

    # Contacts (people) at this company
    company_contacts = Contact.query.filter_by(company_id=company.id).order_by(
        Contact.is_primary.desc(), Contact.first_name
    ).all()

    # Pass all_users for reassignment (Manager+)
    all_users = None
    if current_user.has_role_at_least("manager"):
        all_users = User.query.filter_by(is_active_user=True).order_by(User.display_name).all()

    return render_template(
        "companies/detail.html",
        company=company,
        timeline=timeline,
        last_interaction=last_interaction,
        next_followup=next_followup,
        total_interactions=total_interactions,
        total_followups=total_followups,
        pending_followups=pending_followups,
        completion_rate=completion_rate,
        quick_functions=[qf.to_dict() for qf in QuickFunction.query.filter_by(
            is_active=True
        ).order_by(QuickFunction.sort_order).all()],
        custom_fields=active_custom_fields,
        custom_values=custom_values,
        company_attachments=company_attachments,
        attachment_categories=attachment_categories,
        attachment_tags=attachment_tags,
        company_id=company.id,
        company_contacts=company_contacts,
        all_users=all_users,
    )


@companies_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_company(id):
    company = db.get_or_404(Company, id)
    if not can_access_record(company):
        abort(403)

    active_custom_fields = CustomFieldDefinition.query.filter_by(is_active=True).order_by(
        CustomFieldDefinition.sort_order
    ).all()

    if request.method == "POST":
        company_name = request.form.get("company_name", "").strip()
        if not company_name:
            flash("Company name is required.", "danger")
            custom_values = {
                v.definition_id: v.value
                for v in CustomFieldValue.query.filter_by(company_id=company.id).all()
            }
            return render_template(
                "companies/form.html",
                company=company,
                statuses=COMPANY_STATUSES,
                custom_fields=active_custom_fields,
                custom_values=custom_values,
            )

        company.company_name = company_name
        company.industry = request.form.get("industry", "").strip()
        company.phone = request.form.get("phone", "").strip()
        company.email = request.form.get("email", "").strip()
        company.contact_person = request.form.get("contact_person", "").strip()
        company.status = request.form.get("status", "lead")

        # Upsert custom field values
        for cf in active_custom_fields:
            val = request.form.get(f"custom_field_{cf.id}", "").strip()
            existing = CustomFieldValue.query.filter_by(
                definition_id=cf.id, company_id=company.id
            ).first()
            if existing:
                existing.value = val
            elif val:
                db.session.add(CustomFieldValue(definition_id=cf.id, company_id=company.id, value=val))

        db.session.commit()
        flash(f"Company '{company.company_name}' updated successfully.", "success")
        return redirect(url_for("companies.detail_company", id=company.id))

    custom_values = {
        v.definition_id: v.value
        for v in CustomFieldValue.query.filter_by(company_id=company.id).all()
    }
    return render_template(
        "companies/form.html",
        company=company,
        statuses=COMPANY_STATUSES,
        custom_fields=active_custom_fields,
        custom_values=custom_values,
    )


@companies_bp.route("/<int:id>/status", methods=["PATCH"])
@login_required
def update_status(id):
    company = db.get_or_404(Company, id)
    if not can_access_record(company):
        abort(403)
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "")
    if new_status not in COMPANY_STATUSES:
        return jsonify({"ok": False, "error": f"Invalid status. Must be one of: {', '.join(COMPANY_STATUSES)}"}), 400
    company.status = new_status
    db.session.commit()
    return jsonify({"ok": True, "status": new_status})


@companies_bp.route("/<int:id>/quick-action", methods=["POST"])
@login_required
def quick_action(id):
    company = db.get_or_404(Company, id)
    if not can_access_record(company):
        abort(403)

    try:
        action_id = int(request.form.get("action_id", "0"))
    except (ValueError, TypeError):
        action_id = 0

    qf = db.session.get(QuickFunction, action_id)
    if not qf:
        if _is_ajax():
            return jsonify({"ok": False, "error": "Invalid quick function."}), 400
        flash("Invalid quick function.", "danger")
        return redirect(url_for("companies.detail_company", id=company.id))

    interaction = Interaction(
        company_id=company.id,
        date=date.today(),
        time=datetime.now().time().replace(microsecond=0),
        interaction_type=qf.contact_type,
        notes=qf.notes,
        outcome=qf.outcome,
        user_id=current_user.id,
    )
    db.session.add(interaction)
    db.session.commit()

    message = f'"{qf.label}" logged for {company.company_name}.'
    if _is_ajax():
        return jsonify({"ok": True, "message": message})

    flash(message, "success")
    return redirect(url_for("companies.detail_company", id=company.id))


@companies_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_company(id):
    company = db.get_or_404(Company, id)
    if not can_access_record(company):
        abort(403)

    name = company.company_name
    company_id = company.id

    # Nullify contact references before deleting company
    Contact.query.filter_by(company_id=company_id).update({"company_id": None})

    db.session.delete(company)
    db.session.commit()

    # Clean up uploads directory for this company
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], str(company_id))
    if os.path.isdir(upload_dir):
        shutil.rmtree(upload_dir)

    flash(f"Company '{name}' deleted successfully.", "success")
    return redirect(url_for("companies.list_companies"))


@companies_bp.route("/<int:id>/reassign", methods=["POST"])
@role_required("manager")
def reassign_company(id):
    """Reassign a single company (optionally with child interactions/followups)."""
    company = db.get_or_404(Company, id)
    data = request.get_json(silent=True) or {}
    target_user_id = data.get("target_user_id")

    if not target_user_id:
        return jsonify({"ok": False, "error": "Target user is required."}), 400

    target_user = db.get_or_404(User, int(target_user_id))
    company.user_id = target_user.id

    if data.get("cascade"):
        Interaction.query.filter_by(company_id=company.id).update({"user_id": target_user.id})
        FollowUp.query.filter_by(company_id=company.id).update({"user_id": target_user.id})

    db.session.commit()
    return jsonify({"ok": True, "message": f"Company reassigned to {target_user.display_name}."})


@companies_bp.route("/bulk-reassign", methods=["POST"])
@role_required("manager")
def bulk_reassign():
    """Bulk-reassign selected companies to another user."""
    data = request.get_json(silent=True) or {}
    ids = data.get("ids", [])
    target_user_id = data.get("target_user_id")
    if not ids or not target_user_id:
        return jsonify({"ok": False, "error": "IDs and target user are required."}), 400
    target_user = db.get_or_404(User, int(target_user_id))
    Company.query.filter(Company.id.in_(ids)).update({"user_id": target_user.id})
    db.session.commit()
    return jsonify({"ok": True, "message": f"{len(ids)} company/companies reassigned to {target_user.display_name}."})
