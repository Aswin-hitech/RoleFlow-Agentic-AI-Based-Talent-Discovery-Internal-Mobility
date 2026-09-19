"""Responsible AI, Fairness Auditing, Human Override, and Privacy Tests.

Requirements:
- Bias/fairness checks using EEOC 80% (four-fifths) rule.
- Disparate impact ratio reporting across departments and tenure tiers.
- Human-in-the-loop override requiring >= 10 character business justification.
- Immutable audit logging of transfer milestones and score adjustments.
- Public privacy policy statement adhering to GDPR, EEOC, and CCPA standards.
"""

import pytest
from core.services.responsible_ai import calculate_fairness_audit, get_privacy_policy_statement
from core.services.audit import record_audit_event, get_audit_logs


from core.extensions import db
from core.models.schema import Role, Employee, RoleCandidate


def test_fairness_audit_eeoc_four_fifths_rule(app):
    """Verify that EEOC 80% rule correctly computes disparate impact across departments."""
    with app.app_context():
        role = Role(
            id="role_eeoc_01",
            title="Senior AI Platform Engineer",
            department="Data & AI",
            minimum_experience=4.0,
        )
        db.session.add(role)

        # 3 candidates from native dept Data & AI (all fit_score >= 75 -> 100% selection rate)
        for i in range(3):
            e = Employee(
                id=f"emp_data_{i}",
                full_name=f"Data Eng {i}",
                email=f"data{i}@roleflow.internal",
                current_role="Data Engineer",
                department="Data & AI",
                experience_years=4.0,
            )
            c = RoleCandidate(
                id=f"cand_data_{i}",
                role_id="role_eeoc_01",
                employee_id=f"emp_data_{i}",
                fit_score=85,
                readiness_score=80,
            )
            db.session.add_all([e, c])

        # 3 candidates from Platform dept (all fit_score < 75 -> 0% rate -> adverse impact)
        for i in range(3):
            e = Employee(
                id=f"emp_plat_{i}",
                full_name=f"Plat Eng {i}",
                email=f"plat{i}@roleflow.internal",
                current_role="Platform Engineer",
                department="Platform",
                experience_years=4.0,
            )
            c = RoleCandidate(
                id=f"cand_plat_{i}",
                role_id="role_eeoc_01",
                employee_id=f"emp_plat_{i}",
                fit_score=60,
                readiness_score=60,
            )
            db.session.add_all([e, c])

        db.session.commit()

        audit = calculate_fairness_audit("role_eeoc_01", threshold=75.0)

        assert "department_metrics" in audit
        assert "tenure_metrics" in audit
        assert audit["eeoc_four_fifths_compliant"] is False
        assert audit["fairness_status"] == "ACTION_REQUIRED"
        assert len(audit["warnings"]) > 0
        assert audit["total_evaluated"] == 6


def test_human_in_the_loop_override_validation(client, manager_token):
    """Manager override must reject missing or trivially short justifications."""
    headers = {"Authorization": f"Bearer {manager_token}"}
    role_id = "role_rag_01"
    emp_id = "emp_priya_01"
    url = f"/api/v1/manager/roles/{role_id}/candidates/{emp_id}/override"

    # Missing justification
    res_no_just = client.post(url, json={"override_fit_score": 92}, headers=headers)
    assert res_no_just.status_code == 400
    assert "justification" in res_no_just.get_json()["message"]

    # Justification too short (< 10 chars)
    res_short = client.post(
        url,
        json={"override_fit_score": 92, "justification": "Good dev"},
        headers=headers,
    )
    assert res_short.status_code == 400
    assert "10 characters" in res_short.get_json()["message"]

    # Valid override with proper justification
    res_valid = client.post(
        url,
        json={
            "fit_score": 95,
            "readiness_score": 90,
            "justification": "Candidate has hands-on production experience leading similar RAG systems.",
        },
        headers=headers,
    )
    assert res_valid.status_code == 200
    data = res_valid.get_json()
    assert data["success"] is True
    assert data["candidate"]["fit_score"] == 95
    assert data["candidate"]["readiness_score"] == 90


def test_audit_trail_logging():
    """Verify that audit events are recorded and retrievable."""
    entry = record_audit_event(
        event_type="test_event",
        actor_id="test_user",
        actor_role="manager",
        role_id="role_test_01",
        employee_id="emp_test_01",
        action="test_verification",
    )
    assert entry is not None
    assert "timestamp" in entry

    logs = get_audit_logs(role_id="role_test_01", limit=10)
    assert len(logs) >= 1
    assert logs[0]["actor_id"] == "test_user"
    assert logs[0]["event_type"] == "test_event"


def test_privacy_policy_endpoint(client):
    """Verify that public privacy policy endpoint returns comprehensive AI compliance data."""
    res = client.get("/api/v1/privacy-policy")
    assert res.status_code == 200
    data = res.get_json()
    assert "compliance_frameworks" in data
    assert "core_guarantees" in data
    assert any("EEOC" in f for f in data["compliance_frameworks"])
    assert any("GDPR" in f for f in data["compliance_frameworks"])
