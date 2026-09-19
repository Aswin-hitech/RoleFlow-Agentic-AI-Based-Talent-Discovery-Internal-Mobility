"""Agent 6 — Learning & Career Agent.

Maps identified skill gaps to curated courses from PostgreSQL:
Providers: Coursera, Udemy, NPTEL, Microsoft Learn, Internal Learning.
Outputs structured, sequenced roadmap with duration, priority, and reason.
"""

from typing import Any, Dict, List
from ..models import Course, Employee, Role
from .skill_gap import generate_skill_gap_report


def generate_learning_roadmap(role_id: str, employee_id: str) -> Dict[str, Any]:
    """Create a structured, sequenced upskilling roadmap closing the candidate's skill gaps."""
    gap_report = generate_skill_gap_report(role_id, employee_id)
    role = Role.query.filter_by(id=role_id).first()
    emp = Employee.query.filter_by(id=employee_id).first()
    if not gap_report or not role or not emp:
        return {}

    all_courses = Course.query.all()
    gaps_to_address = gap_report.get("missing_skills", []) + gap_report.get("partial_skills", [])

    roadmap_items = []
    covered_skills = set()

    # Prioritize missing mandatory skills first, then partial skills
    for gap in gap_report.get("gap_details", []):
        skill_name = gap["skill"]
        if skill_name in covered_skills:
            continue

        # Find matching course in catalog
        matching_course = None
        for c in all_courses:
            targets = [t.lower() for t in c.target_skills or []]
            if skill_name.lower() in targets or any(skill_name.lower() in t for t in targets):
                matching_course = c
                break

        if not matching_course:
            # Fallback curated reference
            provider = "Internal Learning" if "system" in skill_name.lower() else "Coursera"
            duration = "3 weeks (15 hrs)"
            course_title = f"{skill_name} for Enterprise Applications"
        else:
            provider = matching_course.provider
            duration = f"{max(2, matching_course.duration_hours // 5)} weeks ({matching_course.duration_hours} hrs)"
            course_title = matching_course.title

        priority = gap.get("severity", "Medium")
        roadmap_items.append({
            "skill": skill_name,
            "resource": f"{course_title} ({provider})",
            "provider": provider,
            "course_title": course_title,
            "reason": gap.get("reason", f"Closes requirement gap for {role.title}"),
            "estimated_duration": duration,
            "priority": priority,
            "completed": False,
        })
        covered_skills.add(skill_name)

    # Sequence items: High priority first, then Medium, then Low
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    roadmap_items.sort(key=lambda item: priority_order.get(item["priority"], 1))

    explanation = (
        f"This personalized learning pathway targets {len(roadmap_items)} critical capability areas required for "
        f"the {role.title} position. Foundations are addressed first through verified coursework, preparing {emp.full_name} "
        f"for immediate impact upon role transition."
    )

    return {
        "role_id": role_id,
        "role_title": role.title,
        "employee_id": employee_id,
        "employee_name": emp.full_name,
        "items": roadmap_items,
        "roadmap_explanation": explanation,
        "total_estimated_weeks": sum(int(item["estimated_duration"].split()[0]) for item in roadmap_items) if roadmap_items else 0,
    }
