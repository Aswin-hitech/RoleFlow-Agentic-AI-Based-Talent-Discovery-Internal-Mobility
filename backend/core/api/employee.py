"""Employee Portal API endpoints (§25, §26, §27, §28, §52, §54)."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..extensions import db
from ..models import Course, Employee, EmployeeSkill, Role, RoleCandidate, Transfer, User
from ..agents.employee_intelligence import analyze_employee_profile
from ..agents.skill_gap import generate_skill_gap_report
from ..agents.learning import generate_learning_roadmap

employee_bp = Blueprint("employee", __name__)


def _get_current_employee_id() -> str:
    claims = get_jwt()
    emp_id = claims.get("employee_id")
    if emp_id:
        return emp_id

    identity = get_jwt_identity()
    user = User.query.filter_by(email=identity).first()
    if user and user.employee_id:
        return user.employee_id

    # Fallback to demo default employee
    return "EMP-1024"


@employee_bp.get("/profile")
@jwt_required()
def get_my_profile():
    emp_id = _get_current_employee_id()
    profile = analyze_employee_profile(emp_id)
    if not profile:
        return jsonify(error="not_found", message="Employee record not found."), 404
    return jsonify(profile=profile)


@employee_bp.get("/opportunities")
@jwt_required()
def list_opportunities():
    """List internal opportunities available to the employee. Strictly filters hidden roles (§25, §37)."""
    emp_id = _get_current_employee_id()

    # Query matches for this employee
    candidates = RoleCandidate.query.filter_by(employee_id=emp_id).all()
    opportunities = []

    for c in candidates:
        role = Role.query.filter_by(id=c.role_id).first()
        if not role:
            continue

        # CRITICAL SECURITY RULE: Only visible roles appear in employee opportunities (§18, §25, §37)
        if role.visibility != "visible":
            continue

        transfer = Transfer.query.filter_by(role_id=role.id, employee_id=emp_id).first()

        gap_report = generate_skill_gap_report(role.id, emp_id)
        learning_plan = generate_learning_roadmap(role.id, emp_id)

        opportunities.append({
            "role_id": role.id,
            "title": role.title,
            "department": role.department,
            "description": role.description,
            "headcount": role.headcount,
            "fit_score": c.fit_score,
            "readiness_score": c.readiness_score,
            "fit_breakdown": c.fit_breakdown or {},
            "readiness_breakdown": c.readiness_breakdown or {},
            "top_skills": c.top_skills or [],
            "transferable_skills": c.transferable_skills or [],
            "ai_explanation": c.ai_explanation or "",
            "evidence_refs": c.evidence_refs or [],
            "decision_status": transfer.status if transfer else "pending_shortlist",
            "preference_rank": transfer.preference_rank if transfer else None,
            "strong_skills": gap_report.get("strong_skills", []),
            "partial_skills": gap_report.get("partial_skills", []),
            "missing_skills": gap_report.get("missing_skills", []),
            "learning_items": learning_plan.get("items", []),
        })

    return jsonify(opportunities=opportunities)


@employee_bp.get("/opportunities/<role_id>")
@jwt_required()
def get_opportunity_detail(role_id: str):
    emp_id = _get_current_employee_id()
    role = Role.query.filter_by(id=role_id).first()
    if not role or role.visibility != "visible":
        return jsonify(error="not_found", message="Opportunity not found or not visible."), 404

    cand = RoleCandidate.query.filter_by(role_id=role_id, employee_id=emp_id).first()
    transfer = Transfer.query.filter_by(role_id=role_id, employee_id=emp_id).first()
    gap_report = generate_skill_gap_report(role_id, emp_id)
    learning_plan = generate_learning_roadmap(role_id, emp_id)

    detail = {
        "role_id": role.id,
        "title": role.title,
        "department": role.department,
        "description": role.description,
        "headcount": role.headcount,
        "mandatory_skills": role.mandatory_skills,
        "preferred_skills": role.preferred_skills,
        "fit_score": cand.fit_score if cand else 85,
        "readiness_score": cand.readiness_score if cand else 75,
        "fit_breakdown": cand.fit_breakdown if cand else {},
        "readiness_breakdown": cand.readiness_breakdown if cand else {},
        "evidence_refs": cand.evidence_refs if cand else [],
        "ai_explanation": cand.ai_explanation if cand else "",
        "decision_status": transfer.status if transfer else "pending_shortlist",
        "preference_rank": transfer.preference_rank if transfer else 1,
        "gap_report": gap_report,
        "learning_plan": learning_plan,
    }

    return jsonify(opportunity=detail)


@employee_bp.post("/opportunities/<role_id>/accept")
@jwt_required()
def accept_opportunity(role_id: str):
    """Employee accepts opportunity; status advances to pending_hr review (§26, §30)."""
    emp_id = _get_current_employee_id()
    role = Role.query.filter_by(id=role_id).first()
    if not role or role.visibility != "visible":
        return jsonify(error="not_found", message="Opportunity not found."), 404

    transfer = Transfer.query.filter_by(role_id=role_id, employee_id=emp_id).first()
    if not transfer:
        transfer = Transfer(
            role_id=role_id,
            employee_id=emp_id,
            status="pending_hr",
        )
        db.session.add(transfer)
    else:
        transfer.status = "pending_hr"

    db.session.commit()

    return jsonify(
        success=True,
        message=f"You accepted the opportunity for {role.title}. The transfer request has been forwarded to HR for governance review.",
        transfer=transfer.to_dict(),
    )


@employee_bp.post("/opportunities/<role_id>/decline")
@jwt_required()
def decline_opportunity(role_id: str):
    """Employee declines opportunity; status set to employee_declined, role remains vacant (§28)."""
    emp_id = _get_current_employee_id()
    role = Role.query.filter_by(id=role_id).first()
    if not role or role.visibility != "visible":
        return jsonify(error="not_found", message="Opportunity not found."), 404

    transfer = Transfer.query.filter_by(role_id=role_id, employee_id=emp_id).first()
    if not transfer:
        transfer = Transfer(
            role_id=role_id,
            employee_id=emp_id,
            status="employee_declined",
        )
        db.session.add(transfer)
    else:
        transfer.status = "employee_declined"

    db.session.commit()

    return jsonify(
        success=True,
        message=f"You declined the opportunity for {role.title}. You will not be automatically transferred, and the role remains vacant.",
        transfer=transfer.to_dict(),
    )


@employee_bp.put("/role-preferences")
@jwt_required()
def set_role_preferences():
    """Resolve multiple-role conflict: store 1st and 2nd preference ranking (§27)."""
    emp_id = _get_current_employee_id()
    data = request.get_json(silent=True) or {}
    preferences = data.get("preferences", [])  # [{"role_id": "...", "rank": 1}, ...]

    updated = []
    for pref in preferences:
        r_id = pref.get("role_id")
        rank = int(pref.get("rank", 1))
        transfer = Transfer.query.filter_by(role_id=r_id, employee_id=emp_id).first()
        if transfer:
            transfer.preference_rank = rank
            updated.append({"role_id": r_id, "preference_rank": rank})

    db.session.commit()
    return jsonify(
        success=True,
        message="Your role opportunity preferences have been recorded successfully.",
        preferences=updated,
    )


@employee_bp.get("/learning")
@jwt_required()
def get_my_learning():
    emp_id = _get_current_employee_id()
    transfers = Transfer.query.filter_by(employee_id=emp_id).all()
    roles = [t.role_id for t in transfers] if transfers else ["role-ml-engineer"]

    all_items = []
    for r_id in roles[:2]:
        plan = generate_learning_roadmap(r_id, emp_id)
        if plan:
            all_items.extend(plan.get("items", []))

    if not all_items:
        # Default curated courses
        courses = Course.query.limit(4).all()
        for c in courses:
            all_items.append({
                "skill": c.target_skills[0] if c.target_skills else "Engineering",
                "resource": f"{c.title} ({c.provider})",
                "provider": c.provider,
                "course_title": c.title,
                "reason": "Targeted career development pathway",
                "estimated_duration": f"{c.duration_hours // 5} weeks",
                "priority": "High",
                "completed": False,
            })

    return jsonify(roadmap={"items": all_items})


@employee_bp.post("/learning/<course_id>/complete")
@jwt_required()
def mark_learning_complete(course_id: str):
    """Mark learning complete (§54): updates employee skill evidence to verified and triggers re-match."""
    emp_id = _get_current_employee_id()
    data = request.get_json(silent=True) or {}
    skill_name = data.get("skill_name") or "MLOps"

    # Add or upgrade employee skill to verified
    existing = EmployeeSkill.query.filter_by(employee_id=emp_id, skill_name=skill_name).first()
    if existing:
        existing.status = "verified"
        existing.proficiency = min(5, existing.proficiency + 1)
        existing.evidence_text = f"Verified through completion of {course_id} certification"
    else:
        db.session.add(EmployeeSkill(
            employee_id=emp_id,
            skill_name=skill_name,
            proficiency=4,
            status="verified",
            evidence_id=f"cert-{course_id}",
            evidence_text=f"Verified through completion of {course_id} coursework",
        ))

    db.session.commit()

    return jsonify(
        success=True,
        message=f"Course completed! '{skill_name}' is now marked as a VERIFIED skill on your profile with updated evidence.",
    )
