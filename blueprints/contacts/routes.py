from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from blueprints.auth.decorators import can_access_record, role_required
from blueprints.contacts import contacts_bp
from extensions import db
from models import Company, Contact, SocialAccount, SOCIAL_PLATFORMS, Interaction, AppSettings
from models.user import User


def _is_ajax():
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@contacts_bp.route("/")
@login_required
def list_contacts():
    q = request.args.get("q", "").strip()
    company_id = request.args.get("company_id", "").strip()

    query = Contact.query.options(db.joinedload(Contact.company))

    if not current_user.has_role_at_least("manager"):
        query = query.filter(Contact.user_id == current_user.id)

    if q:
        query = query.filter(
            db.or_(
                Contact.first_name.ilike(f"%{q}%"),
                Contact.last_name.ilike(f"%{q}%"),
                Contact.email.ilike(f"%{q}%"),
            )
        )
    if company_id:
        query = query.filter(Contact.company_id == int(company_id))

    settings = AppSettings.get()
    page = request.args.get("page", 1, type=int)
    ordered = query.order_by(Contact.first_name)

    if settings.pagination_enabled:
        pagination = ordered.paginate(page=page, per_page=settings.pagination_size, error_out=False)
        contacts = pagination.items
    else:
        pagination = None
        contacts = ordered.all()

    companies = Company.query.order_by(Company.company_name).all()

    return render_template(
        "contacts/list.html",
        contacts=contacts,
        q=q,
        selected_company_id=company_id,
        companies=companies,
        pagination=pagination,
    )


@contacts_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_contact():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        if not first_name:
            flash("First name is required.", "danger")
            companies = Company.query.order_by(Company.company_name).all()
            return render_template(
                "contacts/form.html",
                contact=None,
                companies=companies,
                social_platforms=SOCIAL_PLATFORMS,
            )

        company_id = request.form.get("company_id")

        contact = Contact(
            first_name=first_name,
            last_name=request.form.get("last_name", "").strip(),
            email=request.form.get("email", "").strip(),
            phone=request.form.get("phone", "").strip(),
            job_title=request.form.get("job_title", "").strip(),
            company_id=int(company_id) if company_id else None,
            is_primary="is_primary" in request.form,
            notes=request.form.get("notes", "").strip(),
            user_id=current_user.id,
        )
        db.session.add(contact)
        db.session.flush()

        # Save social accounts
        _save_social_accounts(contact.id, request.form)

        db.session.commit()

        flash(f"Contact '{contact.full_name}' created successfully.", "success")
        return redirect(url_for("contacts.detail_contact", id=contact.id))

    companies = Company.query.order_by(Company.company_name).all()
    preselect_company = request.args.get("company_id")
    return render_template(
        "contacts/form.html",
        contact=None,
        companies=companies,
        social_platforms=SOCIAL_PLATFORMS,
        preselect_company_id=int(preselect_company) if preselect_company else None,
    )


@contacts_bp.route("/<int:id>")
@login_required
def detail_contact(id):
    contact = db.get_or_404(Contact, id)
    if not can_access_record(contact):
        abort(403)

    # Interaction history across all companies
    interactions = Interaction.query.filter_by(contact_id=contact.id).order_by(
        Interaction.date.desc()
    ).all()

    return render_template(
        "contacts/detail.html",
        contact=contact,
        interactions=interactions,
        social_platforms=SOCIAL_PLATFORMS,
    )


@contacts_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_contact(id):
    contact = db.get_or_404(Contact, id)
    if not can_access_record(contact):
        abort(403)

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        if not first_name:
            flash("First name is required.", "danger")
            companies = Company.query.order_by(Company.company_name).all()
            return render_template(
                "contacts/form.html",
                contact=contact,
                companies=companies,
                social_platforms=SOCIAL_PLATFORMS,
            )

        company_id = request.form.get("company_id")
        contact.first_name = first_name
        contact.last_name = request.form.get("last_name", "").strip()
        contact.email = request.form.get("email", "").strip()
        contact.phone = request.form.get("phone", "").strip()
        contact.job_title = request.form.get("job_title", "").strip()
        contact.company_id = int(company_id) if company_id else None
        contact.is_primary = "is_primary" in request.form
        contact.notes = request.form.get("notes", "").strip()

        # Update social accounts
        SocialAccount.query.filter_by(contact_id=contact.id).delete()
        _save_social_accounts(contact.id, request.form)

        db.session.commit()

        flash(f"Contact '{contact.full_name}' updated successfully.", "success")
        return redirect(url_for("contacts.detail_contact", id=contact.id))

    companies = Company.query.order_by(Company.company_name).all()
    return render_template(
        "contacts/form.html",
        contact=contact,
        companies=companies,
        social_platforms=SOCIAL_PLATFORMS,
    )


@contacts_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_contact(id):
    contact = db.get_or_404(Contact, id)
    if not can_access_record(contact):
        abort(403)
    company_id = contact.company_id
    name = contact.full_name

    # Nullify interaction/followup references
    Interaction.query.filter_by(contact_id=contact.id).update({"contact_id": None})
    from models import FollowUp
    FollowUp.query.filter_by(contact_id=contact.id).update({"contact_id": None})

    db.session.delete(contact)
    db.session.commit()
    flash(f"Contact '{name}' deleted successfully.", "success")
    if company_id:
        return redirect(url_for("companies.detail_company", id=company_id))
    return redirect(url_for("contacts.list_contacts"))


@contacts_bp.route("/<int:id>/move-company", methods=["POST"])
@login_required
def move_company(id):
    """Move a contact to a new company, preserving previous_company_id."""
    contact = db.get_or_404(Contact, id)
    if not can_access_record(contact):
        abort(403)

    new_company_id = request.form.get("new_company_id")
    if not new_company_id:
        flash("Please select a company.", "danger")
        return redirect(url_for("contacts.detail_contact", id=contact.id))

    new_company = db.get_or_404(Company, int(new_company_id))

    # Set previous company
    if contact.company_id:
        contact.previous_company_id = contact.company_id
    contact.company_id = new_company.id
    db.session.commit()

    flash(f"Contact moved to {new_company.company_name}.", "success")
    return redirect(url_for("contacts.detail_contact", id=contact.id))


@contacts_bp.route("/<int:id>/reassign", methods=["POST"])
@role_required("manager")
def reassign_contact(id):
    contact = db.get_or_404(Contact, id)
    data = request.get_json(silent=True) or {}
    target_user_id = data.get("target_user_id")
    if not target_user_id:
        return jsonify({"ok": False, "error": "Target user is required."}), 400
    target_user = db.get_or_404(User, int(target_user_id))
    contact.user_id = target_user.id
    db.session.commit()
    return jsonify({"ok": True, "message": f"Contact reassigned to {target_user.display_name}."})


def _save_social_accounts(contact_id, form):
    """Parse repeater fields for social accounts and save them."""
    idx = 0
    while True:
        platform = form.get(f"social_platform_{idx}", "").strip()
        if not platform:
            break
        handle = form.get(f"social_handle_{idx}", "").strip()
        url = form.get(f"social_url_{idx}", "").strip()
        if handle or url:
            sa = SocialAccount(
                contact_id=contact_id,
                platform=platform,
                handle=handle,
                url=url,
            )
            db.session.add(sa)
        idx += 1
