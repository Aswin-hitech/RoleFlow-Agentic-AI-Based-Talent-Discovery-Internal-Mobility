"""HR Portal API endpoints — Workforce Mobility Governance (§29, §30, §52)."""

from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from ..extensions import db
from ..models import Employee, Role, RoleCandidate, Transfer

hr_bp = Blueprint("hr", __name__)


@hr_bp.get("/transfers")
@jwt_required()
def list_transfers():
    claims = get_jwt()
    if claims.get("role") not in {"hr", "admin"}:
        return jsonify(error="forbidden", message="HR authorization required."), 403

    transfers = Transfer.query.order_by(Transfer.updated_at.desc()).all()
    results = []

    for t in transfers:
        emp = Employee.query.filter_by(id=t.employee_id).first()
        role = Role.query.filter_by(id=t.role_id).first()
        cand = RoleCandidate.query.filter_by(role_id=t.role_id, employee_id=t.employee_id).first()

        results.append({
            "id": t.id,
            "role_id": t.role_id,
            "role_title": role.title if role else "Unknown Role",
            "department": role.department if role else "Engineering",
            "employee_id": t.employee_id,
            "employee_name": emp.full_name if emp else "Unknown Employee",
            "current_role": emp.current_role if emp else "",
            "source_department": emp.department if emp else "",
            "fit_score": cand.fit_score if cand else 88,
            "readiness_score": cand.readiness_score if cand else 80,
            "top_skills": cand.top_skills if cand else [],
            "status": t.status,
            "preference_rank": t.preference_rank,
            "manager_id": t.manager_id,
            "hr_notes": t.hr_notes,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        })

    # Summary metrics for HR dashboard (§49)
    total_roles = Role.query.count()
    shortlisted_candidates = RoleCandidate.query.filter_by(status="shortlisted").count()
    pending_employee = Transfer.query.filter_by(status="pending_employee").count()
    pending_hr = Transfer.query.filter_by(status="pending_hr").count()
    approved_transfers = Transfer.query.filter_by(status="approved").count()

    metrics = {
        "open_roles": total_roles,
        "total_candidates": RoleCandidate.query.count(),
        "ready_now": RoleCandidate.query.filter(RoleCandidate.readiness_score >= 70).count(),
        "shortlisted_candidates": shortlisted_candidates,
        "pending_employee_decisions": pending_employee,
        "pending_hr_approvals": pending_hr,
        "completed_transfers": approved_transfers,
    }

    return jsonify(transfers=results, metrics=metrics)


@hr_bp.post("/transfers/<transfer_id>/approve")
@jwt_required()
def approve_transfer(transfer_id: str):
    claims = get_jwt()
    if claims.get("role") not in {"hr", "admin"}:
        return jsonify(error="forbidden", message="HR authorization required."), 403

    transfer = Transfer.query.filter_by(id=transfer_id).first()
    if not transfer:
        return jsonify(error="not_found", message="Transfer record not found."), 404

    data = request.get_json(silent=True) or {}
    notes = data.get("notes") or "Approved by HR workforce mobility governance."

    transfer.status = "approved"
    transfer.hr_id = claims.get("name", "HR Director")
    transfer.hr_notes = notes
    transfer.updated_at = datetime.now(timezone.utc)

    # Update candidate status
    cand = RoleCandidate.query.filter_by(role_id=transfer.role_id, employee_id=transfer.employee_id).first()
    if cand:
        cand.status = "transferred"

    db.session.commit()

    return jsonify(
        success=True,
        message="Internal transfer approved successfully. Workforce records updated.",
        transfer=transfer.to_dict(),
    )


@hr_bp.post("/transfers/<transfer_id>/reject")
@jwt_required()
def reject_transfer(transfer_id: str):
    claims = get_jwt()
    if claims.get("role") not in {"hr", "admin"}:
        return jsonify(error="forbidden", message="HR authorization required."), 403

    transfer = Transfer.query.filter_by(id=transfer_id).first()
    if not transfer:
        return jsonify(error="not_found", message="Transfer record not found."), 404

    data = request.get_json(silent=True) or {}
    notes = data.get("notes") or "Declined per HR workforce allocation review."

    transfer.status = "rejected"
    transfer.hr_id = claims.get("name", "HR Director")
    transfer.hr_notes = notes
    transfer.updated_at = datetime.now(timezone.utc)

    db.session.commit()

    return jsonify(
        success=True,
        message="Internal transfer request rejected by HR.",
        transfer=transfer.to_dict(),
    )
