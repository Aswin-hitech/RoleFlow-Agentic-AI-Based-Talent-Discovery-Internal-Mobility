"""API Endpoint integration tests for RoleFlow.

Tests standard user workflows:
- Health check and provider inspection.
- Authentication and JWT token issuance.
- Manager role listing, candidate inspection with explanations.
- Employee profile retrieval and opportunity matches.
- Fairness audit report retrieval.
"""

import pytest


def test_health_check_endpoint(client):
    """Health check returns status, version, and LLM configuration."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert "llm_provider" in data
    assert "llm_model" in data


def test_auth_login_successful(client):
    """Logging in with demo credentials generates a valid JWT token."""
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "employee@roleflow.io", "password": "demo1234"},
    )
    assert res.status_code == 200
    data = res.get_json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["role"] == "employee"
    assert data["user"]["email"] == "employee@roleflow.io"


def test_manager_get_roles(client, manager_token):
    """Manager can retrieve open roles."""
    headers = {"Authorization": f"Bearer {manager_token}"}
    res = client.get("/api/v1/manager/roles", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "roles" in data
    roles = data["roles"]
    assert isinstance(roles, list)
    assert len(roles) > 0
    assert "title" in roles[0]
    assert "id" in roles[0]


def test_manager_get_candidates_with_explanations(client, manager_token):
    """Manager can retrieve ranked candidates with deterministic scores and explanations."""
    headers = {"Authorization": f"Bearer {manager_token}"}
    role_id = "role_rag_01"
    res = client.get(f"/api/v1/manager/roles/{role_id}/candidates", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "candidates" in data
    candidates = data["candidates"]
    assert isinstance(candidates, list)
    assert len(candidates) > 0
    first = candidates[0]
    assert "fit_score" in first
    assert "readiness_score" in first
    assert "ai_explanation" in first
    assert "fit_breakdown" in first


def test_employee_get_profile(client, employee_token):
    """Authenticated employee can fetch their profile."""
    headers = {"Authorization": f"Bearer {employee_token}"}
    res = client.get("/api/v1/employee/profile", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "profile" in data
    profile = data["profile"]
    assert profile.get("employee_id") == "emp_priya_01" or profile.get("id") == "emp_priya_01"
    assert "skills" in profile


def test_employee_get_matches(client, employee_token):
    """Authenticated employee can fetch their top internal matches."""
    headers = {"Authorization": f"Bearer {employee_token}"}
    res = client.get("/api/v1/employee/opportunities", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "opportunities" in data
    opps = data["opportunities"]
    assert isinstance(opps, list)
    assert len(opps) > 0
    assert "fit_score" in opps[0]


def test_manager_fairness_audit_endpoint(client, manager_token):
    """Manager can view EEOC fairness audit for a role."""
    headers = {"Authorization": f"Bearer {manager_token}"}
    role_id = "role_rag_01"
    res = client.get(f"/api/v1/manager/roles/{role_id}/fairness-audit", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "audit" in data
    audit = data["audit"]
    assert "fairness_status" in audit
    assert "department_metrics" in audit
