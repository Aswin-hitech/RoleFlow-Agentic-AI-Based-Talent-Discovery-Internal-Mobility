"""Agent 5 — Skill Gap Agent.

For candidate vs target role:
- Strong skills (✓)
- Developing / Partial skills (△)
- Missing skills (○)
Each gap detail contains: skill, current_level, required_level, severity, reason.
"""

from typing import Any, Dict
from ..models import Employee, Role
from .employee_intelligence import analyze_employee_profile


def generate_skill_gap_report(role_id: str, employee_id: str) -> Dict[str, Any]:
    """Analyze skill alignment and detail gaps between candidate and role."""
    role = Role.query.filter_by(id=role_id).first()
    emp = Employee.query.filter_by(id=employee_id).first()
    if not role or not emp:
        return {}

    profile = analyze_employee_profile(employee_id)
    emp_skills = {s["name"].lower(): s for s in profile.get("skills", [])}

    mandatory = role.mandatory_skills or []
    preferred = role.preferred_skills or []
    all_requirements = mandatory + preferred

    strong = []
    partial = []
    missing = []
    gap_details = []

    for req in all_requirements:
        req_lower = req.lower()
        is_mandatory = req in mandatory

        if req_lower in emp_skills:
            prof = emp_skills[req_lower].get("proficiency", 3)
            if prof >= 4:
                strong.append(req)
            elif prof >= 2:
                partial.append(req)
                gap_details.append({
                    "skill": req,
                    "current_level": f"Level {prof}/5 (Developing)",
                    "required_level": "Level 4/5 (Proficient)",
                    "severity": "Medium" if not is_mandatory else "High",
                    "reason": f"Demonstrated foundation in existing work; requires deeper hands-on depth for {role.title}.",
                })
            else:
                partial.append(req)
                gap_details.append({
                    "skill": req,
                    "current_level": f"Level {prof}/5 (Beginner)",
                    "required_level": "Level 3/5 (Competent)",
                    "severity": "High" if is_mandatory else "Medium",
                    "reason": f"Early familiarity; needs practical project application to reach production readiness.",
                })
        else:
            missing.append(req)
            gap_details.append({
                "skill": req,
                "current_level": "None (Unverified)",
                "required_level": "Level 3/5 (Competent)",
                "severity": "High" if is_mandatory else "Low",
                "reason": f"Required for {role.title} day-to-day responsibilities; recommended for targeted learning.",
            })

    return {
        "role_id": role_id,
        "role_title": role.title,
        "employee_id": employee_id,
        "employee_name": emp.full_name,
        "strong_skills": strong,
        "partial_skills": partial,
        "missing_skills": missing,
        "gap_details": gap_details,
    }
