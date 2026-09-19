"""Manager API endpoints (§21, §22, §23, §24, §52)."""

import socket
import threading
from datetime import datetime, timezone
from urllib.parse import urlparse
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from ..extensions import db
from ..models import Employee, MatchRun, Project, Role, RoleCandidate, Transfer
from ..tasks import celery_app
from ..tasks.discovery import run_discovery_task

manager_bp = Blueprint("manager", __name__)


def _broker_reachable(timeout: float = 0.5) -> bool:
    try:
        parsed = urlparse(celery_app.conf.broker_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


@manager_bp.get("/roles")
@jwt_required()
def list_roles():
    claims = get_jwt()
    if claims.get("role") not in {"manager", "hr", "admin"}:
        return jsonify(error="forbidden", message="Manager or HR authorization required."), 403

    roles = Role.query.order_by(Role.created_at.desc()).all()
    out = []
    for r in roles:
        cand_count = RoleCandidate.query.filter_by(role_id=r.id).count()
        ready_count = RoleCandidate.query.filter_by(role_id=r.id).filter(RoleCandidate.readiness_score >= 70).count()
        shortlisted_count = RoleCandidate.query.filter_by(role_id=r.id, status="shortlisted").count()

        d = r.to_dict()
        d["candidates_found"] = cand_count
        d["ready_now"] = ready_count
        d["self_nominated"] = shortlisted_count
        d["new_candidates"] = 1 if cand_count > 5 else 0
        out.append(d)

    return jsonify(roles=out)


@manager_bp.post("/roles")
@jwt_required()
def create_role():
    claims = get_jwt()
    if claims.get("role") not in {"manager", "hr", "admin"}:
        return jsonify(error="forbidden", message="Manager or HR authorization required."), 403

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify(error="bad_request", message="Role title is required."), 400

    import uuid
    role_id = f"role-{uuid.uuid4().hex[:8]}"

    role = Role(
        id=role_id,
        title=title,
        department=data.get("department") or "Engineering",
        description=data.get("description") or "",
        jd_text=data.get("jd_text") or "",
        headcount=int(data.get("headcount", 1)),
        minimum_experience=float(data.get("minimum_experience", 2.0)),
        mandatory_skills=data.get("mandatory_skills", []),
        preferred_skills=data.get("preferred_skills", []),
        certifications=data.get("certifications", []),
        responsibilities=data.get("responsibilities", []),
        domain=data.get("domain") or "Engineering",
        visibility=data.get("visibility") or "visible",
        created_by_id=claims.get("name", "Manager"),
    )
    db.session.add(role)
    db.session.commit()

    # Automatically queue discovery (§19)
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    match_run = MatchRun(
        id=run_id,
        role_id=role_id,
        status="queued",
        current_stage="Discovery queued",
        progress=10,
    )
    db.session.add(match_run)
    db.session.commit()

    if _broker_reachable():
        try:
            run_discovery_task.delay(role_id, run_id)
        except Exception:
            threading.Thread(target=run_discovery_task, args=(role_id, run_id), daemon=True).start()
    else:
        # Seamless async fallback so discovery completes without Redis
        threading.Thread(target=run_discovery_task, args=(role_id, run_id), daemon=True).start()

    return jsonify(role=role.to_dict(), match_run_id=run_id), 201


@manager_bp.get("/roles/<role_id>")
@jwt_required()
def get_role(role_id: str):
    claims = get_jwt()
    if claims.get("role") not in {"manager", "hr", "admin"}:
        return jsonify(error="forbidden", message="Manager or HR authorization required."), 403

    role = Role.query.filter_by(id=role_id).first()
    if not role:
        return jsonify(error="not_found", message="Role not found."), 404

    d = role.to_dict()
    d["candidates_count"] = RoleCandidate.query.filter_by(role_id=role.id).count()
    d["ready_count"] = RoleCandidate.query.filter_by(role_id=role.id).filter(RoleCandidate.readiness_score >= 70).count()
    return jsonify(role=d)


@manager_bp.put("/roles/<role_id>")
@jwt_required()
def update_role(role_id: str):
    claims = get_jwt()
    if claims.get("role") not in {"manager", "hr", "admin"}:
        return jsonify(error="forbidden", message="Manager or HR authorization required."), 403

    role = Role.query.filter_by(id=role_id).first()
    if not role:
        return jsonify(error="not_found", message="Role not found."), 404

    data = request.get_json(silent=True) or {}
    if "title" in data:
        role.title = data["title"]
    if "department" in data:
        role.department = data["department"]
    if "description" in data:
        role.description = data["description"]
    if "headcount" in data:
        role.headcount = int(data["headcount"])
    if "visibility" in data:
        role.visibility = data["visibility"]
    if "status" in data:
        role.status = data["status"]

    db.session.commit()
    return jsonify(role=role.to_dict())


@manager_bp.post("/roles/<role_id>/discovery")
def trigger_discovery(role_id: str):
    role = Role.query.filter_by(id=role_id).first()
    if not role:
        return jsonify(error="not_found", message="Role not found."), 404

    import uuid
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    match_run = MatchRun(
        id=run_id,
        role_id=role_id,
        status="queued",
        current_stage="Discovery queued",
        progress=10,
    )
    db.session.add(match_run)
    db.session.commit()

    if _broker_reachable():
        try:
            task = run_discovery_task.delay(role_id, run_id)
            return jsonify(queued=True, task_id=task.id, match_run_id=run_id, role_id=role_id), 202
        except Exception:
            pass

    # Seamless background fallback
    threading.Thread(target=run_discovery_task, args=(role_id, run_id), daemon=True).start()
    return jsonify(queued=True, match_run_id=run_id, role_id=role_id), 202


@manager_bp.get("/roles/<role_id>/candidates")
@jwt_required()
def get_role_candidates(role_id: str):
    claims = get_jwt()
    if claims.get("role") not in {"manager", "hr", "admin"}:
        return jsonify(error="forbidden", message="Manager or HR authorization required."), 403

    role = Role.query.filter_by(id=role_id).first()
    if not role:
        return jsonify(error="not_found", message="Role not found."), 404

    tab = request.args.get("tab", "all")
    min_fit = int(request.args.get("min_fit", 0))
    min_readiness = int(request.args.get("min_readiness", 0))

    query = RoleCandidate.query.filter_by(role_id=role_id)
    if min_fit > 0:
        query = query.filter(RoleCandidate.fit_score >= min_fit)
    if min_readiness > 0:
        query = query.filter(RoleCandidate.readiness_score >= min_readiness)

    if tab == "high_fit":
        query = query.filter(RoleCandidate.fit_score >= 80)
    elif tab == "high_readiness":
        query = query.filter(RoleCandidate.readiness_score >= 70)
    elif tab == "shortlisted":
        query = query.filter(RoleCandidate.status == "shortlisted")

    candidates = query.order_by(RoleCandidate.fit_score.desc(), RoleCandidate.readiness_score.desc()).all()
    results = []

    for c in candidates:
        emp = Employee.query.filter_by(id=c.employee_id).first()
        if not emp:
            continue

        curr_proj = Project.query.filter_by(employee_id=emp.id, status="in_progress").first()
        d = c.to_dict()
        d["name"] = emp.full_name
        d["full_name"] = emp.full_name
        d["email"] = emp.email
        d["current_role"] = emp.current_role
        d["department"] = emp.department
        d["availability_days"] = emp.availability_days
        d["current_project"] = curr_proj.to_dict() if curr_proj else None
        results.append(d)

    return jsonify(candidates=results)


@manager_bp.get("/candidates/<employee_id>")
@jwt_required()
def get_candidate_details(employee_id: str):
    claims = get_jwt()
    if claims.get("role") not in {"manager", "hr", "admin"}:
        return jsonify(error="forbidden", message="Manager or HR authorization required."), 403

    from ..agents.employee_intelligence import analyze_employee_profile
    profile = analyze_employee_profile(employee_id)
    if not profile:
        return jsonify(error="not_found", message="Employee not found."), 404

    return jsonify(profile=profile)


@manager_bp.post("/roles/<role_id>/candidates/<employee_id>/shortlist")
@jwt_required()
def shortlist_candidate(role_id: str, employee_id: str):
    """Shortlist candidate: creates a transfer opportunity with pending_employee decision (§24)."""
    claims = get_jwt()
    if claims.get("role") not in {"manager", "hr", "admin"}:
        return jsonify(error="forbidden", message="Manager authorization required."), 403

    role = Role.query.filter_by(id=role_id).first()
    emp = Employee.query.filter_by(id=employee_id).first()
    if not role or not emp:
        return jsonify(error="not_found", message="Role or employee not found."), 404

    candidate = RoleCandidate.query.filter_by(role_id=role_id, employee_id=employee_id).first()
    if candidate:
        candidate.status = "shortlisted"

    # Create or update Transfer record
    transfer = Transfer.query.filter_by(role_id=role_id, employee_id=employee_id).first()
    if not transfer:
        transfer = Transfer(
            role_id=role_id,
            employee_id=employee_id,
            candidate_id=candidate.id if candidate else None,
            status="pending_employee",
            manager_id=claims.get("name", "Manager"),
        )
        db.session.add(transfer)
    else:
        transfer.status = "pending_employee"

    db.session.commit()

    return jsonify(
        success=True,
        message=f"{emp.full_name} has been shortlisted. An opportunity has been sent to their portal for review.",
        transfer=transfer.to_dict(),
    )
