"""Agent 4 — Internal Role Matching Agent.

Flow (§11):
All employees -> Hard filters -> Semantic retrieval -> Transferable-skill analysis
-> Deterministic scoring -> Top candidates -> LLM explanation for top candidates
"""

import json
from typing import Any, Dict, List

from ..extensions import db
from ..models import Employee, EmployeeSkill, Role
from .employee_intelligence import analyze_employee_profile
from .embeddings import cosine_similarity, embed_texts
from .transferable_skills import discover_transferable_skills
from .scoring import calculate_fit_score, calculate_readiness_score
from .llm import generate_structured


def run_role_matching(role_id: str, top_k: int = 25) -> List[Dict[str, Any]]:
    """Match internal employees against target role using semantic retrieval and deterministic scoring."""
    role = Role.query.filter_by(id=role_id).first()
    if not role:
        return []

    role_profile = role.to_dict()
    all_target_skills = role_profile.get("mandatory_skills", []) + role_profile.get("preferred_skills", [])
    target_text = f"{role.title} {role.department} {role.domain} " + " ".join(all_target_skills)
    role_vec = embed_texts([target_text])[0]
    min_exp = float(role_profile.get("minimum_experience", 2.0))

    # 1. Hard filters in SQL (§11):
    # Retrieve all employees with rich skill/project records, plus an eligible sample of the 10,000 workforce
    rich_ids_query = db.session.query(EmployeeSkill.employee_id).distinct()
    rich_emp_ids = [r[0] for r in rich_ids_query.all()]

    rich_employees = Employee.query.filter(
        Employee.id.in_(rich_emp_ids),
        Employee.experience_years >= (min_exp * 0.3),
    ).all()

    other_employees = Employee.query.filter(
        ~Employee.id.in_(rich_emp_ids),
        Employee.experience_years >= (min_exp * 0.3),
    ).limit(30).all()

    candidate_pool = rich_employees + other_employees
    scored_candidates = []

    # Batch compute embeddings for candidates missing them
    missing_indices = [i for i, emp in enumerate(candidate_pool) if not emp.embedding]
    if missing_indices:
        missing_texts = [
            f"{candidate_pool[i].current_role} {candidate_pool[i].department} {' '.join(candidate_pool[i].career_interests or [])}"
            for i in missing_indices
        ]
        computed_vecs = embed_texts(missing_texts)
        for idx, vec in zip(missing_indices, computed_vecs):
            candidate_pool[idx].embedding = vec

    from concurrent.futures import ThreadPoolExecutor, as_completed
    from flask import current_app

    try:
        app = current_app._get_current_object()
    except Exception:
        from .. import create_app
        app = create_app()

    def _evaluate_single(item):
        emp_id, full_name, email, current_role, department, emp_vec = item
        with app.app_context():
            similarity = cosine_similarity(role_vec, emp_vec)
            profile = analyze_employee_profile(emp_id)
            transferable = discover_transferable_skills(profile, all_target_skills)
            fit_score, fit_breakdown = calculate_fit_score(profile, role_profile, transferable)
            readiness_score, readiness_breakdown = calculate_readiness_score(profile, role_profile)

            emp_skill_names = [s["name"] for s in profile.get("skills", [])]
            matched_direct = [s for s in all_target_skills if s.lower() in [e.lower() for e in emp_skill_names]]

            evidence_list = []
            for s in profile.get("skills", []):
                if s["status"] in ["verified", "explicit"] and any(ts.lower() == s["name"].lower() for ts in all_target_skills):
                    evidence_list.append(f"{s['name']} — {s.get('evidence_text') or 'verified from project'}")
            for p in profile.get("projects", []):
                evidence_list.append(f"Project '{p['name']}' ({p.get('role', 'Member')}) — demonstrated {', '.join(p.get('skills_used', [])[:3])}")
            for c in profile.get("certifications", []):
                evidence_list.append(f"Certification '{c['name']}' from {c.get('issuer', 'Vendor')}")

            return {
                "employee_id": emp_id,
                "full_name": full_name,
                "email": email,
                "current_role": current_role,
                "department": department,
                "fit_score": fit_score,
                "readiness_score": readiness_score,
                "fit_breakdown": fit_breakdown,
                "readiness_breakdown": readiness_breakdown,
                "top_skills": matched_direct[:4] if matched_direct else emp_skill_names[:4],
                "transferable_skills": [
                    f"{t['source_skill']} → {t['target_skill']} ({t['bridge_capability']})"
                    for t in transferable[:3]
                ],
                "evidence_refs": evidence_list[:4],
                "raw_profile": profile,
                "similarity": round(similarity, 3),
            }

    emp_tuples = [
        (emp.id, emp.full_name, emp.email, emp.current_role, emp.department, emp.embedding)
        for emp in candidate_pool
    ]

    scored_candidates = []
    # Multi-threaded parallel candidate evaluation across 6 worker threads
    with ThreadPoolExecutor(max_workers=6, thread_name_prefix="RoleFlowMatchWorker") as executor:
        futures = [executor.submit(_evaluate_single, item) for item in emp_tuples]
        for f in as_completed(futures):
            try:
                res = f.result()
                if res:
                    scored_candidates.append(res)
            except Exception as err:
                pass

    # Sort deterministically by Fit (descending) then Readiness (descending)
    scored_candidates.sort(key=lambda c: (c["fit_score"], c["readiness_score"]), reverse=True)
    top_candidates = scored_candidates[:top_k]

    # 5. Concurrent LLM Grounded Explanations for Top Candidates
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="RoleFlowExplainWorker") as executor:
        future_to_cand = {
            executor.submit(_generate_grounded_explanation, cand, role_profile): cand
            for cand in top_candidates[:5]
        }
        for f in as_completed(future_to_cand):
            cand = future_to_cand[f]
            try:
                cand["ai_explanation"] = f.result()
            except Exception:
                cand["ai_explanation"] = _fallback_explanation(cand, role_profile)

    for cand in top_candidates[5:]:
        cand["ai_explanation"] = _fallback_explanation(cand, role_profile)

    return top_candidates


def _generate_grounded_explanation(candidate: Dict[str, Any], role_profile: Dict[str, Any]) -> str:
    """Ask LLM to draft evidence-backed match explanation grounded strictly in candidate records."""
    schema_hint = '{"explanation": "Two-paragraph grounded explanation citing specific projects and skills."}'
    prompt = f"""Draft a concise, grounded explanation for why this internal candidate matches the role of '{role_profile['title']}'.
Strict Rule: Cite only the actual projects, skills, and certifications provided below. Do not invent any facts.

Candidate:
Name: {candidate['full_name']}
Current Role: {candidate['current_role']} ({candidate['department']})
Fit Score: {candidate['fit_score']}% | Readiness: {candidate['readiness_score']}%
Top Skills: {', '.join(candidate['top_skills'])}
Transferable: {', '.join(candidate['transferable_skills'])}
Evidence: {json.dumps(candidate['evidence_refs'])}
Readiness Note: {candidate['readiness_breakdown'].get('deduction_reason', '')}
"""
    raw = generate_structured(prompt, schema_hint)
    if raw:
        try:
            parsed = json.loads(raw)
            if "explanation" in parsed and len(parsed["explanation"]) > 30:
                return parsed["explanation"]
        except Exception:
            pass

    return _fallback_explanation(candidate, role_profile)


def _fallback_explanation(candidate: Dict[str, Any], role_profile: Dict[str, Any]) -> str:
    role_title = role_profile.get("title", "the role")
    skills_str = ", ".join(candidate["top_skills"][:3]) or "relevant domain experience"
    transfer_str = candidate["transferable_skills"][0] if candidate["transferable_skills"] else "adjacent problem-solving capabilities"
    curr_proj_note = candidate["readiness_breakdown"].get("deduction_reason", "")

    return (
        f"{candidate['full_name']} demonstrates strong technical alignment for {role_title} with {candidate['fit_score']}% Fit. "
        f"Key qualifications include verified proficiency in {skills_str}, bolstered by transferable capability via {transfer_str}. "
        f"Readiness is at {candidate['readiness_score']}%, influenced by: {curr_proj_note}."
    )
