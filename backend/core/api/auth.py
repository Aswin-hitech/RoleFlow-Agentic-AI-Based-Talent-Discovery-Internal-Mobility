"""Authentication API — JWT Login, Refresh, Me with demo user support."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash

from ..config import Config
from ..models import User

auth_bp = Blueprint("auth", __name__)

DEMO_USERS = {
    "manager@roleflow.io": {
        "id": "usr-mgr-01",
        "employee_id": "EMP-0001",
        "name": "Priya Sharma",
        "full_name": "Priya Sharma",
        "role": "manager",
        "title": "Engineering Manager, Platform",
    },
    "employee@roleflow.io": {
        "id": "usr-emp-01",
        "employee_id": "EMP-1024",
        "name": "Arjun Mehta",
        "full_name": "Arjun Mehta",
        "role": "employee",
        "title": "Senior Data Analyst",
    },
    "hr@roleflow.io": {
        "id": "usr-hr-01",
        "employee_id": "EMP-0002",
        "name": "Sneha Rao",
        "full_name": "Sneha Rao",
        "role": "hr",
        "title": "Head of Talent & Workforce Mobility",
    },
}


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = None
    # Check database first
    db_user = User.query.filter_by(email=email).first()
    if db_user:
        pwd_valid = (
            check_password_hash(db_user.password_hash, password)
            if db_user.password_hash
            else (password == Config.DEMO_USER_PASSWORD)
        )
        if pwd_valid:
            user = {
                "id": db_user.id,
                "email": db_user.email,
                "name": db_user.full_name,
                "full_name": db_user.full_name,
                "role": db_user.role,
                "employee_id": db_user.employee_id or "EMP-1024",
            }

    # Fallback to in-memory demo accounts if DB empty or not seeded
    if not user and email in DEMO_USERS:
        if password == Config.DEMO_USER_PASSWORD:
            user = {"email": email, **DEMO_USERS[email]}

    if not user:
        return jsonify(error="invalid_credentials", message="Email or password is incorrect."), 401

    claims = {
        "role": user["role"],
        "name": user["name"],
        "employee_id": user.get("employee_id", "EMP-1024"),
    }

    return jsonify(
        access_token=create_access_token(identity=user["email"], additional_claims=claims),
        refresh_token=create_refresh_token(identity=user["email"], additional_claims=claims),
        user=user,
    )


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role", "employee")
    name = claims.get("name", identity)
    emp_id = claims.get("employee_id", "EMP-1024")

    new_claims = {"role": role, "name": name, "employee_id": emp_id}
    return jsonify(access_token=create_access_token(identity=identity, additional_claims=new_claims))


@auth_bp.get("/me")
@jwt_required()
def me():
    identity = get_jwt_identity()
    claims = get_jwt()
    role = claims.get("role", "employee")
    name = claims.get("name", identity)
    emp_id = claims.get("employee_id", "EMP-1024")

    db_user = User.query.filter_by(email=identity).first()
    if db_user:
        return jsonify({
            "id": db_user.id,
            "email": db_user.email,
            "name": db_user.full_name,
            "full_name": db_user.full_name,
            "role": db_user.role,
            "employee_id": db_user.employee_id or emp_id,
        })

    demo = DEMO_USERS.get(identity)
    if demo:
        return jsonify({"email": identity, **demo})

    return jsonify({"email": identity, "name": name, "role": role, "employee_id": emp_id})
