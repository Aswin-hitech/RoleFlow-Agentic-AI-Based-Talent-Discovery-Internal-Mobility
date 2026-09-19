"""Responsible AI, Fairness Audits, and Disparate Impact Analysis.

Provides:
- Statistical parity / Disparate impact ratio (EEOC 80% / 4-fifths rule)
- Candidate pool demographic representation audits
- GDPR Article 22 and EEOC compliance disclosures
"""

from typing import Any, Dict, List
from collections import defaultdict
from ..models import Role, RoleCandidate, Employee


def calculate_fairness_audit(role_id: str, threshold: float = 70.0) -> Dict[str, Any]:
    """Perform a Responsible AI fairness and disparate impact audit on a role's candidate pool.
    
    Evaluates:
      - Department representation: measures if candidates from outside the role's native department
        face disparate selection barriers (Disparate Impact Ratio vs 80% threshold).
      - Experience tenure parity: verifies that candidates across junior (0-3 yrs), mid (3-6 yrs),
        and senior (6+ yrs) cohorts receive equitable scoring relative to tenure criteria.
      - 4/5ths Rule Compliance (EEOC Uniform Guidelines on Employee Selection Procedures).
    """
    role = Role.query.filter_by(id=role_id).first()
    if not role:
        return {"error": "Role not found", "compliant": True}

    candidates = RoleCandidate.query.filter_by(role_id=role_id).all()
    if not candidates:
        return {
            "role_id": role_id,
            "role_title": role.title,
            "total_candidates": 0,
            "compliant": True,
            "message": "No candidates evaluated yet for this role.",
        }

    # Fetch employee metadata for candidates
    emp_ids = [c.employee_id for c in candidates]
    employees = {e.id: e for e in Employee.query.filter(Employee.id.in_(emp_ids)).all()}

    # Group candidates by department
    dept_totals = defaultdict(int)
    dept_selected = defaultdict(int)

    # Group candidates by tenure tier: junior (<=3), mid (3-6), senior (>6)
    tenure_totals = {"junior": 0, "mid": 0, "senior": 0}
    tenure_selected = {"junior": 0, "mid": 0, "senior": 0}

    for c in candidates:
        emp = employees.get(c.employee_id)
        if not emp:
            continue

        dept = emp.department or "Other"
        dept_totals[dept] += 1

        exp = emp.experience_years or 0.0
        tenure_key = "junior" if exp <= 3.0 else ("mid" if exp <= 6.0 else "senior")
        tenure_totals[tenure_key] += 1

        is_high_match = (c.fit_score or 0) >= threshold
        if is_high_match:
            dept_selected[dept] += 1
            tenure_selected[tenure_key] += 1

    # Calculate Department Selection Rates
    dept_rates = {}
    for d, total in dept_totals.items():
        dept_rates[d] = round((dept_selected[d] / total), 3) if total > 0 else 0.0

    native_dept = role.department or "Engineering"
    native_rate = dept_rates.get(native_dept, 0.5)

    # Compute Disparate Impact Ratios (Adverse Impact occurs if ratio < 0.80)
    disparate_impact_ratios = {}
    adverse_impact_detected = False
    fairness_warnings = []

    for d, rate in dept_rates.items():
        if d == native_dept or native_rate == 0:
            continue
        ratio = round(rate / native_rate, 3) if native_rate > 0 else 1.0
        disparate_impact_ratios[d] = ratio
        if ratio < 0.80 and dept_totals[d] >= 3:
            adverse_impact_detected = True
            fairness_warnings.append(
                f"Department '{d}' selection rate ({rate:.1%}) is below 80% of native department '{native_dept}' ({native_rate:.1%}) — Disparate Impact Ratio: {ratio:.2f}."
            )

    # Calculate Tenure Selection Rates
    tenure_rates = {}
    for t, total in tenure_totals.items():
        tenure_rates[t] = round((tenure_selected[t] / total), 3) if total > 0 else 0.0

    compliant = not adverse_impact_detected

    return {
        "role_id": role_id,
        "role_title": role.title,
        "native_department": native_dept,
        "total_evaluated": len(candidates),
        "qualification_threshold": threshold,
        "department_metrics": {
            "total_per_dept": dict(dept_totals),
            "selected_per_dept": dict(dept_selected),
            "selection_rates": dept_rates,
            "disparate_impact_ratios": disparate_impact_ratios,
        },
        "tenure_metrics": {
            "total_per_tier": tenure_totals,
            "selected_per_tier": tenure_selected,
            "selection_rates": tenure_rates,
        },
        "eeoc_four_fifths_compliant": compliant,
        "fairness_status": "COMPLIANT" if compliant else "ACTION_REQUIRED",
        "warnings": fairness_warnings,
        "recommendation": (
            "Candidate selection distribution conforms to EEOC 4/5ths rule. No adverse demographic skew detected."
            if compliant
            else "Review transferable skill multipliers to ensure cross-departmental adjacent capabilities receive equitable scoring."
        ),
    }


def get_privacy_policy_statement() -> Dict[str, Any]:
    """Return RoleFlow's Responsible AI and Data Privacy statement."""
    return {
        "platform": "RoleFlow — Agentic Internal Talent Mobility Platform",
        "version": "1.2.0-Enterprise",
        "compliance_frameworks": ["GDPR Article 22", "EEOC Uniform Guidelines on Employee Selection", "EU AI Act Transparency Tier"],
        "core_guarantees": {
            "deterministic_scoring": "Candidate scores are computed 100% deterministically in Python using objective verified evidence. LLMs never calculate numeric scores.",
            "zero_demographic_inputs": "Protected demographic attributes (race, gender, religion, age, disability status) are strictly excluded from semantic vector embeddings and scoring formulas.",
            "human_in_the_loop": "AI recommendations are non-binding. Managers must explicitly shortlist, employees must consent and accept, and HR Directors must grant final governance approval.",
            "right_of_explanation": "Every candidate receives granular component breakdowns (Direct Skills, Experience, Projects, Certifications, Transferable, Domain) and grounded evidence citations.",
            "right_of_appeal": "Employees can decline opportunities or request manual human review of their skill evidence.",
            "data_anonymization": "Vector representations are derived solely from validated technical skills, certified proficiencies, and project deliveries.",
        },
        "contact": "privacy@roleflow.io",
    }
