from functools import wraps

from flask import abort
from flask_login import current_user, login_required


def role_required(minimum_role):
    """Decorator: require login AND at least *minimum_role*."""
    def decorator(f):
        @wraps(f)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.has_role_at_least(minimum_role):
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def can_access_record(record):
    """Return True if current_user may view/edit *record*.

    Managers and admins can access any record.
    Regular users can only access records they own.
    """
    if current_user.has_role_at_least("manager"):
        return True
    return getattr(record, "user_id", None) == current_user.id
