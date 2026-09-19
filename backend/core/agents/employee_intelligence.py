"""Agent 1 — Employee Intelligence Agent.

Purpose:
Understand each employee beyond the current job title.
Inputs:
Employee profile, skills, experience, projects, certifications, courses,
completed modules, assessments, current project, career interests,
transfer willingness, availability.
"""

from typing import Any, Dict
from ..models import Employee, EmployeeSkill, Project, Certification


def analyze_employee_profile(employee_id: str) -> Dict[str, Any]:
    """Extract and structure comprehensive employee intelligence from records."""
    emp = Employee.query.filter_by(id=employee_id).first()
    if not emp:
        return {}

    skills = EmployeeSkill.query.filter_by(employee_id=employee_id).all()
    projects = Project.query.filter_by(employee_id=employee_id).all()
    certs = Certification.query.filter_by(employee_id=employee_id).all()

    # Identify current active project if any
    current_proj = None
    for p in projects:
        if p.status == "in_progress":
            current_proj = p
            break

    profile = {
        "employee_id": emp.id,
        "full_name": emp.full_name,
        "email": emp.email,
        "current_role": emp.current_role,
        "department": emp.department,
        "experience_years": emp.experience_years,
        "bio": emp.bio or "",
        "open_to_transfer": emp.open_to_transfer,
        "availability_days": emp.availability_days,
        "career_interests": emp.career_interests or [],
        "skills": [
            {
                "name": s.skill_name,
                "proficiency": s.proficiency,
                "status": s.status,  # explicit | inferred | transferable | verified
                "evidence_id": s.evidence_id,
                "evidence_text": s.evidence_text,
            }
            for s in skills
        ],
        "projects": [p.to_dict() for p in projects],
        "certifications": [c.to_dict() for c in certs],
        "current_project": current_proj.to_dict() if current_proj else None,
    }

    return profile
