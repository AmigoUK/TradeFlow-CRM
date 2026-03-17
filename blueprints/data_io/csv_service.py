"""CSV generation, parsing, and validation for bulk data import/export."""

import csv
import io
from datetime import date, datetime, time

from sqlalchemy import func

from extensions import db
from models.company import COMPANY_STATUSES, Company
from models.interaction import Interaction
from models.custom_field import CustomFieldDefinition, CustomFieldValue
from models.followup import PRIORITIES, FollowUp
from models.user import User


# ── Column definitions ─────────────────────────────────────────

COMPANY_COLUMNS = [
    "company_name", "industry", "phone", "email",
    "contact_person", "status", "owner",
]

INTERACTION_COLUMNS = [
    "company_name", "date", "time", "interaction_type",
    "notes", "outcome", "owner",
]

FOLLOWUP_COLUMNS = [
    "company_name", "due_date", "due_time", "priority",
    "completed", "notes", "owner",
]

ENTITY_COLUMNS = {
    "companies": COMPANY_COLUMNS,
    "interactions": INTERACTION_COLUMNS,
    "followups": FOLLOWUP_COLUMNS,
}


# ── Helpers ────────────────────────────────────────────────────

def _active_custom_field_labels():
    """Return ordered list of active custom field labels."""
    defs = (
        CustomFieldDefinition.query
        .filter_by(is_active=True)
        .order_by(CustomFieldDefinition.sort_order)
        .all()
    )
    return [d.label for d in defs]


def _resolve_owner(username):
    """Resolve a username to a User, returning (user, error_msg)."""
    if not username:
        return None, None
    user = User.query.filter(
        func.lower(User.username) == username.strip().lower(),
        User.is_active_user.is_(True),
    ).first()
    if not user:
        return None, f"Unknown or inactive user: '{username}'"
    return user, None


def _resolve_company(company_name):
    """Resolve a company name to a company ID. Returns (company_id, error_msg)."""
    if not company_name or not company_name.strip():
        return None, "company_name is required"
    matches = Company.query.filter(
        func.lower(Company.company_name) == company_name.strip().lower()
    ).all()
    if len(matches) == 0:
        return None, f"No company found with company_name: '{company_name}'"
    if len(matches) > 1:
        return None, f"Multiple companies match company_name: '{company_name}'"
    return matches[0].id, None


def _parse_bool(value):
    """Parse a boolean string. Returns (bool, error_msg)."""
    if not value or not str(value).strip():
        return False, None
    v = str(value).strip().lower()
    if v in ("true", "yes", "1"):
        return True, None
    if v in ("false", "no", "0"):
        return False, None
    return None, f"Invalid boolean value: '{value}'"


def _parse_date(value, field_name="date"):
    """Parse YYYY-MM-DD date string. Returns (date, error_msg)."""
    if not value or not str(value).strip():
        return date.today(), None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date(), None
    except ValueError:
        return None, f"Invalid {field_name} format (expected YYYY-MM-DD): '{value}'"


def _parse_time(value, field_name="time"):
    """Parse HH:MM time string. Returns (time|None, error_msg)."""
    if not value or not str(value).strip():
        return None, None
    try:
        return datetime.strptime(value.strip(), "%H:%M").time(), None
    except ValueError:
        return None, f"Invalid {field_name} format (expected HH:MM): '{value}'"


def _read_csv(file_stream):
    """Read a CSV file stream and return (headers, rows).

    Handles BOM (utf-8-sig) and uses csv.Sniffer for delimiter detection.
    """
    raw = file_stream.read()
    if isinstance(raw, bytes):
        text = raw.decode("utf-8-sig")
    else:
        text = raw.lstrip("\ufeff")

    # Detect dialect from a sample
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    headers = reader.fieldnames or []
    rows = list(reader)
    return headers, rows


# ── Export ─────────────────────────────────────────────────────

def generate_export_csv(entity_type):
    """Generate a CSV StringIO with all records for the given entity type."""
    output = io.StringIO()

    if entity_type == "companies":
        return _export_companies(output)
    elif entity_type == "interactions":
        return _export_interactions(output)
    elif entity_type == "followups":
        return _export_followups(output)
    else:
        raise ValueError(f"Unknown entity type: {entity_type}")


def _export_companies(output):
    cf_labels = _active_custom_field_labels()
    columns = COMPANY_COLUMNS + cf_labels

    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()

    companies = (
        db.session.query(Company, User.username)
        .outerjoin(User, Company.user_id == User.id)
        .order_by(Company.company_name)
        .all()
    )

    # Pre-load custom field values keyed by company_id
    cf_defs = (
        CustomFieldDefinition.query
        .filter_by(is_active=True)
        .order_by(CustomFieldDefinition.sort_order)
        .all()
    )
    cf_values = {}
    if cf_defs:
        all_vals = CustomFieldValue.query.filter(
            CustomFieldValue.definition_id.in_([d.id for d in cf_defs])
        ).all()
        for v in all_vals:
            cf_values.setdefault(v.company_id, {})[v.definition_id] = v.value

    cf_id_to_label = {d.id: d.label for d in cf_defs}

    for c, owner_username in companies:
        row = {
            "company_name": c.company_name,
            "industry": c.industry or "",
            "phone": c.phone or "",
            "email": c.email or "",
            "contact_person": c.contact_person or "",
            "status": c.status,
            "owner": owner_username or "",
        }
        company_cf = cf_values.get(c.id, {})
        for d in cf_defs:
            row[cf_id_to_label[d.id]] = company_cf.get(d.id, "")
        writer.writerow(row)

    output.seek(0)
    return output


def _export_interactions(output):
    writer = csv.DictWriter(output, fieldnames=INTERACTION_COLUMNS)
    writer.writeheader()

    interactions = (
        db.session.query(Interaction, Company.company_name, User.username)
        .join(Company, Interaction.company_id == Company.id)
        .outerjoin(User, Interaction.user_id == User.id)
        .order_by(Interaction.date.desc())
        .all()
    )

    for ct, company_name, owner_username in interactions:
        writer.writerow({
            "company_name": company_name,
            "date": ct.date.isoformat() if ct.date else "",
            "time": ct.time.strftime("%H:%M") if ct.time else "",
            "interaction_type": ct.interaction_type or "",
            "notes": ct.notes or "",
            "outcome": ct.outcome or "",
            "owner": owner_username or "",
        })

    output.seek(0)
    return output


def _export_followups(output):
    writer = csv.DictWriter(output, fieldnames=FOLLOWUP_COLUMNS)
    writer.writeheader()

    followups = (
        db.session.query(FollowUp, Company.company_name, User.username)
        .join(Company, FollowUp.company_id == Company.id)
        .outerjoin(User, FollowUp.user_id == User.id)
        .order_by(FollowUp.due_date.desc())
        .all()
    )

    for fu, company_name, owner_username in followups:
        writer.writerow({
            "company_name": company_name,
            "due_date": fu.due_date.isoformat() if fu.due_date else "",
            "due_time": fu.due_time.strftime("%H:%M") if fu.due_time else "",
            "priority": fu.priority or "",
            "completed": "true" if fu.completed else "false",
            "notes": fu.notes or "",
            "owner": owner_username or "",
        })

    output.seek(0)
    return output


# ── Templates ──────────────────────────────────────────────────

def generate_template_csv(entity_type):
    """Generate a CSV StringIO with headers and 2 example rows."""
    output = io.StringIO()

    if entity_type == "companies":
        cf_labels = _active_custom_field_labels()
        columns = COMPANY_COLUMNS + cf_labels
        examples = [
            {
                "company_name": "Acme Ltd",
                "industry": "Manufacturing",
                "phone": "+44 20 7946 0958",
                "email": "info@acme.example.com",
                "contact_person": "Jane Smith",
                "status": "active",
                "owner": "",
            },
            {
                "company_name": "Globex Corp",
                "industry": "Technology",
                "phone": "+44 20 7946 0959",
                "email": "hello@globex.example.com",
                "contact_person": "John Doe",
                "status": "lead",
                "owner": "",
            },
        ]
        for label in cf_labels:
            examples[0][label] = ""
            examples[1][label] = ""
    elif entity_type == "interactions":
        columns = INTERACTION_COLUMNS
        examples = [
            {
                "company_name": "Acme Ltd",
                "date": date.today().isoformat(),
                "time": "14:30",
                "interaction_type": "phone",
                "notes": "Discussed new contract",
                "outcome": "Follow-up scheduled",
                "owner": "",
            },
            {
                "company_name": "Globex Corp",
                "date": date.today().isoformat(),
                "time": "",
                "interaction_type": "email",
                "notes": "Sent proposal",
                "outcome": "Awaiting response",
                "owner": "",
            },
        ]
    elif entity_type == "followups":
        columns = FOLLOWUP_COLUMNS
        examples = [
            {
                "company_name": "Acme Ltd",
                "due_date": date.today().isoformat(),
                "due_time": "10:00",
                "priority": "high",
                "completed": "false",
                "notes": "Review contract terms",
                "owner": "",
            },
            {
                "company_name": "Globex Corp",
                "due_date": date.today().isoformat(),
                "due_time": "",
                "priority": "medium",
                "completed": "false",
                "notes": "Send follow-up email",
                "owner": "",
            },
        ]
    else:
        raise ValueError(f"Unknown entity type: {entity_type}")

    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for ex in examples:
        writer.writerow(ex)

    output.seek(0)
    return output


# ── Import / Validation ───────────────────────────────────────

def validate_and_import(entity_type, file_stream, current_user):
    """Parse, validate, and import CSV data.

    Returns dict with keys: imported, skipped, errors, warnings.
    """
    headers, rows = _read_csv(file_stream)

    if not rows:
        return {"imported": 0, "skipped": 0, "errors": [], "warnings": ["File is empty or contains only headers."]}

    if entity_type == "companies":
        return _import_companies(headers, rows, current_user)
    elif entity_type == "interactions":
        return _import_interactions(headers, rows, current_user)
    elif entity_type == "followups":
        return _import_followups(headers, rows, current_user)
    else:
        return {"imported": 0, "skipped": 0, "errors": [], "warnings": [f"Unknown entity type: {entity_type}"]}


def _import_companies(headers, rows, current_user):
    errors = []
    warnings = []
    valid_records = []

    # Identify custom field columns
    cf_defs = (
        CustomFieldDefinition.query
        .filter_by(is_active=True)
        .order_by(CustomFieldDefinition.sort_order)
        .all()
    )
    cf_label_to_id = {d.label.lower(): d.id for d in cf_defs}

    for i, row in enumerate(rows, start=2):  # Row 1 is header
        row_errors = []
        company_name = row.get("company_name", "").strip()

        if not company_name:
            row_errors.append("company_name is required")
        elif len(company_name) > 200:
            row_errors.append("company_name must be 200 characters or fewer")

        status = row.get("status", "").strip().lower()
        if status:
            if status not in COMPANY_STATUSES:
                row_errors.append(f"Invalid status: '{status}' (valid: {', '.join(COMPANY_STATUSES)})")
        else:
            status = "lead"

        email = row.get("email", "").strip()
        if email and "@" not in email:
            row_errors.append(f"Invalid email: '{email}'")

        owner_username = row.get("owner", "").strip()
        owner_user = None
        if owner_username:
            owner_user, owner_err = _resolve_owner(owner_username)
            if owner_err:
                row_errors.append(owner_err)
        else:
            owner_user = current_user

        if row_errors:
            errors.append({
                "row": i,
                "data": dict(row),
                "error": "; ".join(row_errors),
            })
            continue

        cf_values = {}
        for key, val in row.items():
            if key and key.lower() in cf_label_to_id and val and val.strip():
                cf_values[cf_label_to_id[key.lower()]] = val.strip()

        valid_records.append({
            "company_name": company_name,
            "industry": row.get("industry", "").strip(),
            "phone": row.get("phone", "").strip(),
            "email": email,
            "contact_person": row.get("contact_person", "").strip(),
            "status": status,
            "user_id": owner_user.id if owner_user else None,
            "cf_values": cf_values,
        })

    imported = 0
    try:
        for rec in valid_records:
            cf_vals = rec.pop("cf_values")
            company = Company(**rec)
            db.session.add(company)
            db.session.flush()  # Get company.id for custom fields
            for def_id, val in cf_vals.items():
                cfv = CustomFieldValue(
                    definition_id=def_id,
                    company_id=company.id,
                    value=val,
                )
                db.session.add(cfv)
            imported += 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        warnings.append(f"Database error: {e}")
        imported = 0

    return {
        "imported": imported,
        "skipped": len(errors),
        "errors": errors,
        "warnings": warnings,
    }


def _import_interactions(headers, rows, current_user):
    errors = []
    warnings = []
    valid_records = []

    for i, row in enumerate(rows, start=2):
        row_errors = []

        company_name = row.get("company_name", "").strip()
        company_id, company_err = _resolve_company(company_name)
        if company_err:
            row_errors.append(company_err)

        dt, dt_err = _parse_date(row.get("date", ""), "date")
        if dt_err:
            row_errors.append(dt_err)

        tm, tm_err = _parse_time(row.get("time", ""), "time")
        if tm_err:
            row_errors.append(tm_err)

        interaction_type = row.get("interaction_type", "").strip() or "phone"

        owner_username = row.get("owner", "").strip()
        owner_user = None
        if owner_username:
            owner_user, owner_err = _resolve_owner(owner_username)
            if owner_err:
                row_errors.append(owner_err)
        else:
            owner_user = current_user

        if row_errors:
            errors.append({
                "row": i,
                "data": dict(row),
                "error": "; ".join(row_errors),
            })
            continue

        valid_records.append({
            "company_id": company_id,
            "date": dt,
            "time": tm,
            "interaction_type": interaction_type,
            "notes": row.get("notes", "").strip(),
            "outcome": row.get("outcome", "").strip(),
            "user_id": owner_user.id if owner_user else None,
        })

    imported = 0
    try:
        for rec in valid_records:
            db.session.add(Interaction(**rec))
            imported += 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        warnings.append(f"Database error: {e}")
        imported = 0

    return {
        "imported": imported,
        "skipped": len(errors),
        "errors": errors,
        "warnings": warnings,
    }


def _import_followups(headers, rows, current_user):
    errors = []
    warnings = []
    valid_records = []

    for i, row in enumerate(rows, start=2):
        row_errors = []

        company_name = row.get("company_name", "").strip()
        company_id, company_err = _resolve_company(company_name)
        if company_err:
            row_errors.append(company_err)

        dt, dt_err = _parse_date(row.get("due_date", ""), "due_date")
        if dt_err:
            row_errors.append(dt_err)

        tm, tm_err = _parse_time(row.get("due_time", ""), "due_time")
        if tm_err:
            row_errors.append(tm_err)

        priority = row.get("priority", "").strip().lower() or "medium"
        if priority not in PRIORITIES:
            row_errors.append(f"Invalid priority: '{priority}' (valid: {', '.join(PRIORITIES)})")

        completed, bool_err = _parse_bool(row.get("completed", ""))
        if bool_err:
            row_errors.append(bool_err)

        owner_username = row.get("owner", "").strip()
        owner_user = None
        if owner_username:
            owner_user, owner_err = _resolve_owner(owner_username)
            if owner_err:
                row_errors.append(owner_err)
        else:
            owner_user = current_user

        if row_errors:
            errors.append({
                "row": i,
                "data": dict(row),
                "error": "; ".join(row_errors),
            })
            continue

        valid_records.append({
            "company_id": company_id,
            "due_date": dt,
            "due_time": tm,
            "priority": priority,
            "completed": completed,
            "notes": row.get("notes", "").strip(),
            "user_id": owner_user.id if owner_user else None,
        })

    imported = 0
    try:
        for rec in valid_records:
            db.session.add(FollowUp(**rec))
            imported += 1
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        warnings.append(f"Database error: {e}")
        imported = 0

    return {
        "imported": imported,
        "skipped": len(errors),
        "errors": errors,
        "warnings": warnings,
    }
