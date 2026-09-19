from flask import Blueprint

from .auth import auth_bp
from .health import health_bp
from .manager import manager_bp
from .employee import employee_bp
from .hr import hr_bp
from .ai import ai_bp
from .crawler import crawler_bp

api_bp = Blueprint("api", __name__)
api_bp.register_blueprint(health_bp, url_prefix="/health")
api_bp.register_blueprint(auth_bp, url_prefix="/auth")
api_bp.register_blueprint(manager_bp, url_prefix="/manager")
api_bp.register_blueprint(employee_bp, url_prefix="/me")
api_bp.register_blueprint(employee_bp, url_prefix="/employee", name="employee_alias")
api_bp.register_blueprint(hr_bp, url_prefix="/hr")
api_bp.register_blueprint(crawler_bp, url_prefix="/crawler")
api_bp.register_blueprint(ai_bp, url_prefix="")


@api_bp.get("/privacy-policy")
def api_privacy_policy():
    from flask import jsonify
    from ..services.responsible_ai import get_privacy_policy_statement
    return jsonify(get_privacy_policy_statement())
