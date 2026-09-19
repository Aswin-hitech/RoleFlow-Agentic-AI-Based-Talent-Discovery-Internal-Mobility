"""RoleFlow — Multi-Threaded Crawler API (§58).

Provides independent, asynchronous endpoints to execute multi-threaded
knowledge crawlers across educational repositories and market intelligence sources.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..extensions import db
from ..models import Course, Role
from ..security import rate_limit
from ..services.crawler import crawl_courses_concurrently, crawl_market_trends_concurrently

crawler_bp = Blueprint("crawler", __name__)


@crawler_bp.post("/courses")
@rate_limit(max_requests=30, window_seconds=60.0)
def crawl_courses():
    """Trigger a concurrent multi-threaded web crawl across multi-provider learning repositories."""
    data = request.get_json(silent=True) or {}
    skills = data.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    if not skills:
        skills = ["Python", "Machine Learning", "System Design"]

    max_workers = int(data.get("max_workers", 5))
    result = crawl_courses_concurrently(skills, max_workers=min(max_workers, 8))

    # Opportunistically persist new high-quality courses to catalog
    for c in result.get("courses", [])[:3]:
        existing = Course.query.filter_by(title=c["title"]).first()
        if not existing:
            new_course = Course(
                id=f"crawled-{abs(hash(c['title'])) % 1000000:06d}",
                title=c["title"],
                provider=c["provider"],
                description=f"Crawled educational resource. Duration: {c['hours']} hours. Rating: {c['rating']}/5.0",
                target_skills=c["skills"],
                duration_hours=c["hours"],
                level=c["level"],
            )
            db.session.add(new_course)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify(result), 200


@crawler_bp.post("/market-skills")
@rate_limit(max_requests=30, window_seconds=60.0)
def crawl_market_skills():
    """Execute multi-threaded market crawl to discover trending skills and requirements for a domain."""
    data = request.get_json(silent=True) or {}
    domain = data.get("domain", "Data & AI")
    role_title = data.get("role_title", "")
    max_workers = int(data.get("max_workers", 3))

    result = crawl_market_trends_concurrently(domain, role_title, max_workers=min(max_workers, 6))
    return jsonify(result), 200


@crawler_bp.post("/roles/<role_id>/candidate-upskilling/<employee_id>")
def crawl_candidate_upskilling(role_id: str, employee_id: str):
    """Execute multi-threaded crawl targeting candidate's specific skill gaps for a role."""
    from ..agents.skill_gap import generate_skill_gap_report

    gap_report = generate_skill_gap_report(role_id, employee_id)
    target_skills = gap_report.get("missing_skills", []) + gap_report.get("partial_skills", [])
    if not target_skills:
        role = Role.query.filter_by(id=role_id).first()
        target_skills = (role.mandatory_skills if role else []) or ["General Professional Development"]

    crawl_res = crawl_courses_concurrently(target_skills, max_workers=5)
    return jsonify(
        role_id=role_id,
        employee_id=employee_id,
        gap_skills_targeted=target_skills,
        crawl_results=crawl_res,
    ), 200
