"""RoleFlow — LangGraph Pipeline Orchestrating the Six Logical Agents.

State machine flow:
role_intelligence
       ↓
employee_intelligence
       ↓
transferable_skill_discovery
       ↓
role_matching (deterministic Fit + Readiness)
       ↓
skill_gap (for top candidates)
       ↓
learning (curated roadmaps)
"""

import logging
from typing import Any, Dict, List, TypedDict

from ..models import Role, RoleCandidate, db
from .role_intelligence import parse_job_description
from .employee_intelligence import analyze_employee_profile
from .matching import run_role_matching
from .skill_gap import generate_skill_gap_report
from .learning import generate_learning_roadmap

logger = logging.getLogger(__name__)


class RoleFlowState(TypedDict, total=False):
    role_id: str
    role_profile: Dict[str, Any]
    employees: List[Dict[str, Any]]
    employee_profiles: List[Dict[str, Any]]
    transferable_skills: List[Dict[str, Any]]
    candidate_scores: List[Dict[str, Any]]
    explanations: List[Dict[str, Any]]
    skill_gaps: List[Dict[str, Any]]
    learning_plan: Dict[str, Any]
    current_stage: str


def _node_role_intelligence(state: RoleFlowState) -> RoleFlowState:
    role = Role.query.filter_by(id=state["role_id"]).first()
    if not role:
        return {**state, "current_stage": "Role not found"}

    profile = role.to_dict()
    # If role has jd_text but requirements not extracted, parse it
    if role.jd_text and not role.mandatory_skills:
        parsed = parse_job_description(role.jd_text, role.title, role.department)
        role.mandatory_skills = parsed.get("mandatory_skills", [])
        role.preferred_skills = parsed.get("preferred_skills", [])
        role.domain = parsed.get("domain", role.domain)
        role.minimum_experience = parsed.get("minimum_experience", role.minimum_experience)
        db.session.commit()
        profile = role.to_dict()

    return {**state, "role_profile": profile, "current_stage": "Analyzing employee profiles"}


def _node_employee_intelligence(state: RoleFlowState) -> RoleFlowState:
    # Set stage for employee intelligence analysis
    return {**state, "current_stage": "Finding transferable skills"}


def _node_transferable_skills(state: RoleFlowState) -> RoleFlowState:
    return {**state, "current_stage": "Scoring candidates"}


def _node_role_matching(state: RoleFlowState) -> RoleFlowState:
    role_id = state["role_id"]
    candidates = run_role_matching(role_id, top_k=25)

    # Persist matched candidates to database
    # Clean up previous discovered runs for this role
    RoleCandidate.query.filter_by(role_id=role_id, status="discovered").delete()

    for cand in candidates:
        rc = RoleCandidate(
            role_id=role_id,
            employee_id=cand["employee_id"],
            fit_score=cand["fit_score"],
            readiness_score=cand["readiness_score"],
            fit_breakdown=cand["fit_breakdown"],
            readiness_breakdown=cand["readiness_breakdown"],
            top_skills=cand["top_skills"],
            transferable_skills=cand["transferable_skills"],
            ai_explanation=cand.get("ai_explanation", ""),
            evidence_refs=cand.get("evidence_refs", []),
            status="discovered",
        )
        db.session.add(rc)

    from datetime import datetime, timezone
    role = Role.query.filter_by(id=role_id).first()
    if role:
        role.last_discovered_at = datetime.now(timezone.utc)

    db.session.commit()

    return {**state, "candidate_scores": candidates, "current_stage": "Generating explanations"}


def _node_skill_gap(state: RoleFlowState) -> RoleFlowState:
    role_id = state["role_id"]
    candidates = state.get("candidate_scores", [])
    gaps = []
    for c in candidates[:3]:
        gap = generate_skill_gap_report(role_id, c["employee_id"])
        gaps.append(gap)
    return {**state, "skill_gaps": gaps, "current_stage": "Generating learning roadmaps"}


def _node_learning(state: RoleFlowState) -> RoleFlowState:
    role_id = state["role_id"]
    candidates = state.get("candidate_scores", [])
    plans = {}
    for c in candidates[:3]:
        plan = generate_learning_roadmap(role_id, c["employee_id"])
        plans[c["employee_id"]] = plan
    return {**state, "learning_plan": plans, "current_stage": "Completed"}


def build_discovery_graph():
    try:
        from langgraph.graph import END, START, StateGraph

        graph = StateGraph(RoleFlowState)
        graph.add_node("role_intelligence", _node_role_intelligence)
        graph.add_node("employee_intelligence", _node_employee_intelligence)
        graph.add_node("transferable_skills", _node_transferable_skills)
        graph.add_node("role_matching", _node_role_matching)
        graph.add_node("skill_gap", _node_skill_gap)
        graph.add_node("learning", _node_learning)

        graph.add_edge(START, "role_intelligence")
        graph.add_edge("role_intelligence", "employee_intelligence")
        graph.add_edge("employee_intelligence", "transferable_skills")
        graph.add_edge("transferable_skills", "role_matching")
        graph.add_edge("role_matching", "skill_gap")
        graph.add_edge("skill_gap", "learning")
        graph.add_edge("learning", END)
        return graph.compile()
    except Exception as exc:
        logger.warning("Could not compile LangGraph: %s. Using sequential executor.", exc)
        return None


def run_discovery(role_id: str, on_progress=None) -> Dict[str, Any]:
    """Execute end-to-end candidate discovery across all six agents."""
    state: RoleFlowState = {"role_id": role_id, "current_stage": "Discovery queued"}

    stages = [
        ("Analyzing employee profiles", _node_role_intelligence),
        ("Finding transferable skills", _node_employee_intelligence),
        ("Scoring candidates", _node_transferable_skills),
        ("Generating explanations", _node_role_matching),
        ("Analyzing skill gaps", _node_skill_gap),
        ("Completed", _node_learning),
    ]

    for stage_name, node_fn in stages:
        if on_progress:
            on_progress(stage_name)
        state = node_fn(state)

    if on_progress:
        on_progress("Completed")

    return state
