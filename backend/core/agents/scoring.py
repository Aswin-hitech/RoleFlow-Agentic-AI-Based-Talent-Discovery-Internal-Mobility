"""Deterministic Fit and Readiness Scoring Engine.

Requirements §12, §13:
Fit Weights:
- Skill Match: 30%
- Experience: 25%
- Projects: 15%
- Certifications: 10%
- Transferable Skills: 10%
- Domain: 10%
Computed entirely in Python; LLM never sets the numeric score.

Readiness:
Separate axis considering:
- Open to transfer
- Career interest
- Availability
- Current project status / remaining weeks
- Learning commitment
"""

from typing import Any, Dict, List, Tuple


def calculate_fit_score(
    employee_profile: Dict[str, Any],
    role_profile: Dict[str, Any],
    transferable_skills: List[Dict[str, Any]],
) -> Tuple[int, Dict[str, Any]]:
    """Compute deterministic Fit Score and component breakdown."""
    mandatory_skills = [s.lower() for s in role_profile.get("mandatory_skills", [])]
    preferred_skills = [s.lower() for s in role_profile.get("preferred_skills", [])]
    all_target_skills = mandatory_skills + preferred_skills

    emp_skills = {s["name"].lower(): s for s in employee_profile.get("skills", [])}

    # 1. Skill Match (30 pts)
    # Mandatory skills weighted 2x of preferred skills
    skill_pts = 0.0
    total_skill_weight = 0.0

    for s in mandatory_skills:
        total_skill_weight += 2.0
        if s in emp_skills:
            prof = emp_skills[s].get("proficiency", 3)
            skill_pts += 2.0 * min(1.0, prof / 4.0)

    for s in preferred_skills:
        total_skill_weight += 1.0
        if s in emp_skills:
            prof = emp_skills[s].get("proficiency", 3)
            skill_pts += 1.0 * min(1.0, prof / 4.0)

    skill_ratio = (skill_pts / total_skill_weight) if total_skill_weight > 0 else 0.8
    skills_score = round(skill_ratio * 30.0, 1)

    # 2. Experience (25 pts)
    min_exp = float(role_profile.get("minimum_experience", 2.0))
    emp_exp = float(employee_profile.get("experience_years", 3.0))
    if emp_exp >= min_exp:
        # Full score if meets or exceeds, extra cushion
        exp_ratio = min(1.0, 0.8 + 0.2 * ((emp_exp - min_exp) / max(1.0, min_exp)))
    else:
        exp_ratio = max(0.2, emp_exp / max(1.0, min_exp))
    experience_score = round(exp_ratio * 25.0, 1)

    # 3. Projects (15 pts)
    # Completed projects demonstrating target or related skills
    projects = employee_profile.get("projects", [])
    relevant_projects = 0
    for p in projects:
        p_skills = [s.lower() for s in p.get("skills_used", [])]
        if any(ts in p_skills for ts in all_target_skills) or any(
            any(ts in s for ts in all_target_skills) for s in p_skills
        ):
            relevant_projects += 1

    if relevant_projects >= 2:
        project_ratio = 0.95
    elif relevant_projects == 1:
        project_ratio = 0.80
    elif len(projects) > 0:
        project_ratio = 0.60
    else:
        project_ratio = 0.30
    projects_score = round(project_ratio * 15.0, 1)

    # 4. Certifications (10 pts)
    role_certs = [c.lower() for c in role_profile.get("certifications", [])]
    emp_certs = employee_profile.get("certifications", [])
    if role_certs:
        matched_certs = sum(
            1 for ec in emp_certs if any(rc in ec.get("name", "").lower() for rc in role_certs)
        )
        cert_ratio = 1.0 if matched_certs > 0 else (0.6 if len(emp_certs) > 0 else 0.4)
    else:
        cert_ratio = 0.9 if len(emp_certs) > 0 else 0.7
    certifications_score = round(cert_ratio * 10.0, 1)

    # 5. Transferable Skills (10 pts)
    if transferable_skills:
        avg_strength = sum(t.get("strength", 0.8) for t in transferable_skills) / len(transferable_skills)
        transfer_ratio = min(1.0, 0.7 + (0.3 * avg_strength))
    else:
        # If already possesses direct skills, give solid credit
        transfer_ratio = 0.75 if skill_ratio > 0.7 else 0.5
    transferable_score = round(transfer_ratio * 10.0, 1)

    # 6. Domain (10 pts)
    role_domain = role_profile.get("domain", "").lower()
    emp_dept = employee_profile.get("department", "").lower()
    emp_role = employee_profile.get("current_role", "").lower()

    if (
        ("ai" in role_domain and ("data" in emp_dept or "ai" in emp_dept))
        or ("engineering" in role_domain and "engineering" in emp_dept)
        or ("data" in role_domain and ("data" in emp_dept or "analyst" in emp_role))
    ):
        domain_ratio = 0.95
    else:
        domain_ratio = 0.75
    domain_score = round(domain_ratio * 10.0, 1)

    # Total Fit Score
    total_fit = int(round(skills_score + experience_score + projects_score + certifications_score + transferable_score + domain_score))
    total_fit = max(10, min(99, total_fit))

    breakdown = {
        "skills": {"score": round(skills_score), "max": 30},
        "experience": {"score": round(experience_score), "max": 25},
        "projects": {"score": round(projects_score), "max": 15},
        "certifications": {"score": round(certifications_score), "max": 10},
        "transferable": {"score": round(transferable_score), "max": 10},
        "domain": {"score": round(domain_score), "max": 10},
    }

    return total_fit, breakdown


def calculate_readiness_score(
    employee_profile: Dict[str, Any],
    role_profile: Dict[str, Any],
) -> Tuple[int, Dict[str, Any]]:
    """Compute separate Readiness score and reason for any deduction."""
    # 1. Open to transfer (30 pts)
    open_to_transfer = employee_profile.get("open_to_transfer", True)
    transfer_pts = 30 if open_to_transfer else 5

    # 2. Career interest match (25 pts)
    role_title = role_profile.get("title", "").lower()
    role_domain = role_profile.get("domain", "").lower()
    interests = [i.lower() for i in employee_profile.get("career_interests", [])]

    matched_interest = any(
        i in role_title or role_title in i or i in role_domain or role_domain in i
        for i in interests
    )
    if matched_interest:
        interest_pts = 25
    elif len(interests) > 0:
        interest_pts = 18
    else:
        interest_pts = 14

    # 3. Availability (20 pts)
    avail_days = employee_profile.get("availability_days", 30)
    if avail_days <= 14:
        avail_pts = 20
    elif avail_days <= 30:
        avail_pts = 17
    elif avail_days <= 60:
        avail_pts = 12
    else:
        avail_pts = 6

    # 4. Current project commitment (15 pts)
    curr_proj = employee_profile.get("current_project")
    deduction_reasons = []

    if curr_proj:
        completion = curr_proj.get("completion_percentage", 50)
        remaining_weeks = curr_proj.get("remaining_weeks", 4)
        if completion >= 85 or remaining_weeks <= 1:
            project_pts = 14
        elif completion >= 60 or remaining_weeks <= 3:
            project_pts = 9
            deduction_reasons.append(
                f"Currently committed to '{curr_proj['name']}' ({completion}% complete) with {remaining_weeks} weeks remaining"
            )
        else:
            project_pts = 4
            deduction_reasons.append(
                f"Early in active project '{curr_proj['name']}' ({completion}% complete, {remaining_weeks} weeks remaining)"
            )
    else:
        project_pts = 15

    # 5. Learning commitment (10 pts)
    learning_pts = 9

    total_readiness = transfer_pts + interest_pts + avail_pts + project_pts + learning_pts
    total_readiness = max(15, min(99, total_readiness))

    if not open_to_transfer:
        deduction_reasons.append("Employee has not marked open to transfer")
    if avail_days > 45:
        deduction_reasons.append(f"Availability period is {avail_days} days")

    explanation = (
        "; ".join(deduction_reasons)
        if deduction_reasons
        else "High availability and strong alignment with career interests"
    )

    breakdown = {
        "open_to_transfer": {"score": transfer_pts, "max": 30},
        "career_interest": {"score": interest_pts, "max": 25},
        "availability": {"score": avail_pts, "max": 20},
        "current_project": {"score": project_pts, "max": 15},
        "learning_commitment": {"score": learning_pts, "max": 10},
        "deduction_reason": explanation,
    }

    return total_readiness, breakdown
