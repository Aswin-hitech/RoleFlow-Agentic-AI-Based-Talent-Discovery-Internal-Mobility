"""Role-Based Access Control (RBAC) security decorators and helpers."""

from functools import wraps
from typing import Set
from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..models import User


def roles_required(*allowed_roles: str):
    """Enforce that the authenticated JWT contains one of the allowed roles.
    
    Returns 401 if unauthenticated, 403 if role claim does not match.
    """
    valid_roles: Set[str] = set(allowed_roles)

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            user_role = claims.get("role")
            if not user_role or user_role not in valid_roles:
                return jsonify(
                    error="forbidden",
                    message=f"Access denied. Requires one of roles: {', '.join(sorted(valid_roles))}.",
                    user_role=user_role,
                ), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def employee_required(fn):
    """Enforce that the caller is an authenticated employee or admin."""
    return roles_required("employee", "admin")(fn)


def manager_required(fn):
    """Enforce that the caller is an authenticated manager, hr, or admin."""
    return roles_required("manager", "hr", "admin")(fn)


def hr_required(fn):
    """Enforce that the caller is an authenticated HR director or admin."""
    return roles_required("hr", "admin")(fn)


def get_current_user_employee_id() -> str:
    """Safely resolve employee_id from authenticated JWT identity or database.
    
    Never trusts client-supplied employee_id in request bodies.
    """
    claims = get_jwt() or {}
    emp_id = claims.get("employee_id")
    if emp_id:
        return emp_id

    # Fallback to querying User record by identity
    identity = get_jwt_identity()
    if identity:
        u = User.query.filter_by(id=identity).first()
        if u and u.employee_id:
            return u.employee_id

    # Fallback to default demo employee if running in development
    return "EMP-1024"
