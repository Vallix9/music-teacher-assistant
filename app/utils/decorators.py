from functools import wraps

from flask import abort, redirect, url_for, flash
from flask_login import current_user

from app.models import Role


def roles_required(*roles):
    """Доступ только для указанных ролей."""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request_path()))
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(f):
    return roles_required(Role.ADMIN)(f)


def staff_required(f):
    """Учитель или администратор."""
    return roles_required(Role.ADMIN, Role.TEACHER)(f)


def request_path():
    from flask import request
    return request.full_path if request.query_string else request.path
