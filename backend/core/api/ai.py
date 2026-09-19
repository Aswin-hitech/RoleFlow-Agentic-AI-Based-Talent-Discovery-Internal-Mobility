"""AI API endpoints (§52).

Endpoints:
- POST /api/v1/roles/parse-jd
- POST /api/v1/roles/:id/gap-report/:employeeId
- POST /api/v1/roles/:id/learning-plan/:employeeId
- GET  /api/v1/match-runs/:id/status
"""

from flask import Blueprint, jsonify, request
from ..models import MatchRun
from ..security import rate_limit
from ..agents.role_intelligence import parse_job_description
from ..agents.skill_gap import generate_skill_gap_report
from ..agents.learning import generate_learning_roadmap

ai_bp = Blueprint("ai", __name__)


@ai_bp.post("/roles/parse-jd")
@rate_limit(max_requests=30, window_seconds=60.0)
def parse_jd():
    data = request.get_json(silent=True) or {}
    jd_text = data.get("jd_text") or data.get("description") or ""
    if not jd_text.strip():
        return jsonify(error="bad_request", message="Job description text is required."), 400

    title_hint = data.get("title", "")
    dept_hint = data.get("department", "")

    parsed = parse_job_description(jd_text, title_hint, dept_hint)
    return jsonify(parsed=parsed)


@ai_bp.post("/roles/<role_id>/gap-report/<employee_id>")
def get_gap_report(role_id: str, employee_id: str):
    report = generate_skill_gap_report(role_id, employee_id)
    if not report:
        return jsonify(error="not_found", message="Role or employee not found."), 404
    return jsonify(gap_report=report)


@ai_bp.post("/roles/<role_id>/learning-plan/<employee_id>")
def get_learning_plan(role_id: str, employee_id: str):
    plan = generate_learning_roadmap(role_id, employee_id)
    if not plan:
        return jsonify(error="not_found", message="Role or employee not found."), 404
    return jsonify(learning_plan=plan)


@ai_bp.get("/match-runs/<run_id>/status")
def get_match_run_status(run_id: str):
    run = MatchRun.query.filter_by(id=run_id).first()
    if not run:
        # If not found yet, return placeholder queued
        return jsonify(status="queued", current_stage="Discovery queued", progress=10)
    return jsonify(run.to_dict())


@ai_bp.post("/roles/<role_id>/live-course-crawl/<employee_id>")
def live_course_crawl(role_id: str, employee_id: str):
    """Trigger a multi-threaded parallel web crawl for live courses targeting candidate's skill gaps."""
    from ..services.crawler import crawl_courses_concurrently
    report = generate_skill_gap_report(role_id, employee_id)
    target_skills = report.get("missing_skills", []) + report.get("partial_skills", [])
    if not target_skills:
        target_skills = ["Software Engineering", "System Design"]

    crawl_res = crawl_courses_concurrently(target_skills, max_workers=5)
    return jsonify(
        role_id=role_id,
        employee_id=employee_id,
        gap_skills_targeted=target_skills,
        crawl_results=crawl_res,
    ), 200
