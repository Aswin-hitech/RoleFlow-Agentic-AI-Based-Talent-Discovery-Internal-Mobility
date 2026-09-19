"""Unit tests for RoleFlow deterministic Fit and Readiness scoring engines.

Requirements:
- Deterministic mathematical calculation (Python core, LLM never calculates numeric score).
- Fit weights: Skills (30%), Experience (25%), Projects (15%), Certifications (10%), Transferable (10%), Domain (10%).
- Readiness axis: Open to transfer (30), Career interest (25), Availability (20), Project status (15), Learning commitment (10).
- Pure reproducibility across repeated evaluations.
"""

import pytest
from core.agents.scoring import calculate_fit_score, calculate_readiness_score


@pytest.fixture
def base_role():
    return {
        "title": "Senior AI Platform Engineer",
        "domain": "AI / ML Engineering",
        "mandatory_skills": ["Python", "PyTorch", "Kubernetes"],
        "preferred_skills": ["FastAPI", "Docker", "MLflow"],
        "minimum_experience": 4.0,
        "certifications": ["AWS Certified Machine Learning", "CKA"],
    }


@pytest.fixture
def strong_employee():
    return {
        "id": "emp_01",
        "name": "Alex Chen",
        "current_role": "Machine Learning Engineer",
        "department": "Data & AI Platform",
        "experience_years": 5.0,
        "skills": [
            {"name": "Python", "proficiency": 4},
            {"name": "PyTorch", "proficiency": 4},
            {"name": "Kubernetes", "proficiency": 4},
            {"name": "FastAPI", "proficiency": 4},
            {"name": "Docker", "proficiency": 4},
            {"name": "MLflow", "proficiency": 4},
        ],
        "projects": [
            {"name": "Realtime AI Pipeline", "skills_used": ["Python", "PyTorch", "Kubernetes"]},
            {"name": "Model Serving Framework", "skills_used": ["FastAPI", "Docker", "MLflow"]},
        ],
        "certifications": [
            {"name": "AWS Certified Machine Learning Specialty"},
            {"name": "Certified Kubernetes Administrator (CKA)"},
        ],
        "open_to_transfer": True,
        "career_interests": ["AI Platform", "Distributed Systems"],
        "availability_days": 14,
        "current_project": {
            "name": "Legacy LLM Migration",
            "completion_percentage": 90,
            "remaining_weeks": 1,
        },
    }


def test_calculate_fit_score_strong_candidate(base_role, strong_employee):
    """Test that a highly qualified candidate achieves an elite fit score."""
    transferable_skills = [{"source_skill": "PyTorch", "target_skill": "TensorFlow", "strength": 0.9}]
    fit_score, breakdown = calculate_fit_score(strong_employee, base_role, transferable_skills)

    assert 90 <= fit_score <= 99
    assert breakdown["skills"]["score"] == 30
    assert breakdown["skills"]["max"] == 30
    assert breakdown["experience"]["score"] >= 20
    assert breakdown["projects"]["score"] >= 14
    assert breakdown["certifications"]["score"] == 10
    assert breakdown["domain"]["score"] == 10


def test_calculate_fit_score_mandatory_weighting(base_role):
    """Test that mandatory skills carry 2x the weight of preferred skills."""
    emp_only_mandatory = {
        "experience_years": 4.0,
        "department": "Data & AI Platform",
        "skills": [
            {"name": "Python", "proficiency": 4},
            {"name": "PyTorch", "proficiency": 4},
            {"name": "Kubernetes", "proficiency": 4},
        ],
        "projects": [],
        "certifications": [],
    }
    emp_only_preferred = {
        "experience_years": 4.0,
        "department": "Data & AI Platform",
        "skills": [
            {"name": "FastAPI", "proficiency": 4},
            {"name": "Docker", "proficiency": 4},
            {"name": "MLflow", "proficiency": 4},
        ],
        "projects": [],
        "certifications": [],
    }

    score_mand, b_mand = calculate_fit_score(emp_only_mandatory, base_role, [])
    score_pref, b_pref = calculate_fit_score(emp_only_preferred, base_role, [])

    # Mandatory skills weighted 2x of preferred (6 pts weight vs 3 pts weight out of 9 total)
    assert b_mand["skills"]["score"] > b_pref["skills"]["score"]
    assert score_mand > score_pref


def test_calculate_fit_score_experience_scaling(base_role):
    """Test experience score scales properly below and above minimum experience."""
    emp_junior = {
        "experience_years": 1.0,
        "department": "Engineering",
        "skills": [],
        "projects": [],
        "certifications": [],
    }
    emp_senior = {
        "experience_years": 8.0,
        "department": "Engineering",
        "skills": [],
        "projects": [],
        "certifications": [],
    }

    _, b_junior = calculate_fit_score(emp_junior, base_role, [])
    _, b_senior = calculate_fit_score(emp_senior, base_role, [])

    assert b_junior["experience"]["score"] < b_senior["experience"]["score"]
    assert b_senior["experience"]["score"] == 25


def test_calculate_fit_score_deterministic_reproducibility(base_role, strong_employee):
    """Test that calculating fit score 50 times yields identical values every time."""
    scores = [calculate_fit_score(strong_employee, base_role, [])[0] for _ in range(50)]
    assert len(set(scores)) == 1, "Deterministic scoring must produce identical outputs."


def test_calculate_readiness_score_open_to_transfer(base_role, strong_employee):
    """Test that open_to_transfer=False imposes a heavy deduction."""
    strong_employee["open_to_transfer"] = False
    readiness_score, breakdown = calculate_readiness_score(strong_employee, base_role)

    assert breakdown["open_to_transfer"]["score"] == 5
    assert "Employee has not marked open to transfer" in breakdown["deduction_reason"]


def test_calculate_readiness_score_availability_tiers(base_role, strong_employee):
    """Test availability point deductions across standard HR notice tiers."""
    strong_employee["availability_days"] = 10
    score_10, b_10 = calculate_readiness_score(strong_employee, base_role)

    strong_employee["availability_days"] = 28
    score_28, b_28 = calculate_readiness_score(strong_employee, base_role)

    strong_employee["availability_days"] = 55
    score_55, b_55 = calculate_readiness_score(strong_employee, base_role)

    strong_employee["availability_days"] = 90
    score_90, b_90 = calculate_readiness_score(strong_employee, base_role)

    assert b_10["availability"]["score"] == 20
    assert b_28["availability"]["score"] == 17
    assert b_55["availability"]["score"] == 12
    assert b_90["availability"]["score"] == 6
    assert score_10 > score_28 > score_55 > score_90


def test_calculate_readiness_score_project_commitment(base_role, strong_employee):
    """Test deduction for employees tied to active, uncompleted projects."""
    # Near completion
    strong_employee["current_project"] = {
        "name": "Phase 1 Rollout",
        "completion_percentage": 90,
        "remaining_weeks": 1,
    }
    _, b_near = calculate_readiness_score(strong_employee, base_role)

    # Mid progress
    strong_employee["current_project"] = {
        "name": "Phase 1 Rollout",
        "completion_percentage": 70,
        "remaining_weeks": 3,
    }
    _, b_mid = calculate_readiness_score(strong_employee, base_role)

    # Early in project
    strong_employee["current_project"] = {
        "name": "Phase 1 Rollout",
        "completion_percentage": 20,
        "remaining_weeks": 12,
    }
    _, b_early = calculate_readiness_score(strong_employee, base_role)

    assert b_near["current_project"]["score"] == 14
    assert b_mid["current_project"]["score"] == 9
    assert b_early["current_project"]["score"] == 4
    assert "Early in active project" in b_early["deduction_reason"]


def test_calculate_readiness_score_deterministic_reproducibility(base_role, strong_employee):
    """Test that calculating readiness score 50 times yields identical values."""
    scores = [calculate_readiness_score(strong_employee, base_role)[0] for _ in range(50)]
    assert len(set(scores)) == 1, "Deterministic readiness must produce identical outputs."
