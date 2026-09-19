import os
import sys
import pytest

# Ensure backend directory is in sys.path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from core import create_app
from core.config import Config
from core.extensions import db
from core.security.rate_limiter import rate_limiter
from flask_jwt_extended import create_access_token


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    JWT_SECRET_KEY = "test-jwt-secret-key-for-unit-testing-only"
    ROLEFLOW_ENV = "test"
    ALLOW_DEMO_USERS = True
    RATE_LIMIT_ENABLED = True
    API_PREFIX = "/api/v1"


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset the in-memory rate limiter before every test."""
    rate_limiter.reset()
    yield
    rate_limiter.reset()


from core.models.schema import User, Employee, Role, RoleCandidate
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Create and configure a Flask application for testing with seeded data."""
    test_app = create_app(TestConfig)
    with test_app.app_context():
        db.create_all()

        # Seed sample role, employee, and role candidate
        role = Role(
            id="role_rag_01",
            title="Senior AI Platform Engineer",
            department="Engineering",
            domain="Engineering",
            minimum_experience=4.0,
            mandatory_skills=["Python", "PyTorch"],
            preferred_skills=["Docker"],
        )
        emp = Employee(
            id="emp_priya_01",
            full_name="Priya Sharma",
            email="priya.sharma@roleflow.internal",
            current_role="ML Engineer",
            department="Engineering",
            experience_years=5.0,
            open_to_transfer=True,
            availability_days=14,
        )
        cand = RoleCandidate(
            id="cand_01",
            role_id="role_rag_01",
            employee_id="emp_priya_01",
            fit_score=94,
            readiness_score=88,
            fit_breakdown={"skills": {"score": 28, "max": 30}},
            readiness_breakdown={"open_to_transfer": {"score": 30, "max": 30}},
            ai_explanation="Strong domain match and high skill proficiency.",
        )
        user_mgr = User(
            id="usr-mgr-01",
            email="manager@roleflow.io",
            full_name="Marcus Vance",
            role="manager",
            employee_id="EMP-0001",
            password_hash=generate_password_hash("demo1234"),
        )
        user_emp = User(
            id="usr-emp-01",
            email="employee@roleflow.io",
            full_name="Priya Sharma",
            role="employee",
            employee_id="emp_priya_01",
            password_hash=generate_password_hash("demo1234"),
        )
        db.session.add_all([role, emp, cand, user_mgr, user_emp])
        db.session.commit()

        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def employee_token(app):
    """Generate a valid JWT token for an employee."""
    with app.app_context():
        return create_access_token(
            identity="employee@roleflow.io",
            additional_claims={
                "role": "employee",
                "name": "Priya Sharma",
                "employee_id": "emp_priya_01",
            },
        )


@pytest.fixture
def manager_token(app):
    """Generate a valid JWT token for a manager."""
    with app.app_context():
        return create_access_token(
            identity="manager@roleflow.io",
            additional_claims={
                "role": "manager",
                "name": "Marcus Vance",
                "employee_id": "EMP-0001",
            },
        )


@pytest.fixture
def hr_token(app):
    """Generate a valid JWT token for HR."""
    with app.app_context():
        return create_access_token(
            identity="hr@roleflow.io",
            additional_claims={
                "role": "hr",
                "name": "Sarah Jenkins",
                "employee_id": "EMP-0002",
            },
        )
