"""Security, RBAC, and Rate Limiting Tests for RoleFlow.

Requirements:
- Strict role-based access checks (RBAC) on every protected endpoint.
- 401 Unauthorized for missing/invalid tokens.
- 403 Forbidden for insufficient privileges (e.g. employee accessing manager routes).
- In-memory sliding-window rate limiting returning 429 Too Many Requests.
- Production environment security enforcement (disabling demo users and weak secrets).
"""

import pytest
from core.config import validate_production_security
from core.security.rate_limiter import rate_limiter


def test_rbac_unauthenticated_request_rejected(client):
    """Unauthenticated requests to protected endpoints must return 401."""
    res_mgr = client.get("/api/v1/manager/roles")
    assert res_mgr.status_code == 401

    res_emp = client.get("/api/v1/employee/profile")
    assert res_emp.status_code == 401

    res_hr = client.get("/api/v1/hr/transfers")
    assert res_hr.status_code == 401


def test_rbac_insufficient_privileges_employee_to_manager(client, employee_token):
    """Employee tokens must be blocked from manager endpoints with 403."""
    headers = {"Authorization": f"Bearer {employee_token}"}
    res = client.get("/api/v1/manager/roles", headers=headers)
    assert res.status_code == 403
    data = res.get_json()
    assert data["error"] == "forbidden"
    assert "authorization required" in data["message"].lower() or "denied" in data["message"].lower()


def test_rbac_insufficient_privileges_manager_to_employee(client, manager_token):
    """Manager tokens must be blocked from employee endpoints with 403."""
    headers = {"Authorization": f"Bearer {manager_token}"}
    res = client.get("/api/v1/employee/profile", headers=headers)
    assert res.status_code == 403
    data = res.get_json()
    assert data["error"] == "forbidden"


def test_rbac_authorized_manager_access(client, manager_token):
    """Manager token should successfully access manager routes."""
    headers = {"Authorization": f"Bearer {manager_token}"}
    res = client.get("/api/v1/manager/roles", headers=headers)
    assert res.status_code == 200


def test_sliding_window_rate_limiter(client):
    """Rate limiter should trigger HTTP 429 when threshold is exceeded."""
    # Login endpoint is limited to 10 requests / 60 seconds
    url = "/api/v1/auth/login"
    payload = {"username": "wrong_user", "password": "wrong_password"}

    # Execute 10 requests (should return 401 due to bad credentials, but not 429)
    for _ in range(10):
        res = client.post(url, json=payload)
        assert res.status_code == 401

    # 11th request must be rate limited with HTTP 429
    res_limited = client.post(url, json=payload)
    assert res_limited.status_code == 429
    data = res_limited.get_json()
    assert data["error"] in ("rate_limited", "rate_limit_exceeded")
    assert "Retry-After" in res_limited.headers


def test_production_security_validation():
    """Production validator must detect and reject default dev secrets."""
    insecure_config = {
        "ROLEFLOW_ENV": "production",
        "JWT_SECRET_KEY": "roleflow-jwt-insecure-secret-key-change-in-prod",
        "ALLOW_DEMO_USERS": False,
    }
    with pytest.raises(RuntimeError) as exc_info:
        validate_production_security(insecure_config)
    assert "Insecure JWT_SECRET_KEY" in str(exc_info.value)


def test_production_demo_users_blocked_in_prod(client, monkeypatch):
    """Demo login accounts must be refused in production environment."""
    from core import config

    # Simulate production environment where demo users are disabled
    monkeypatch.setattr(config.Config, "ROLEFLOW_ENV", "production")
    monkeypatch.setattr(config.Config, "ALLOW_DEMO_USERS", False)

    res = client.post(
        "/api/v1/auth/login",
        json={"email": "employee@roleflow.io", "password": "demo1234"},
    )
    assert res.status_code == 403
    data = res.get_json()
    assert "Demo user accounts are disabled" in data["message"]
