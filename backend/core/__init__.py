from flask import Flask, jsonify
from flask_cors import CORS

from .api import api_bp
from .config import Config
from .extensions import db, jwt


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(app, origins=[app.config["FRONTEND_ORIGIN"], "http://localhost:5173", "http://127.0.0.1:5173"], supports_credentials=True)
    db.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        try:
            db.create_all()
        except Exception:
            pass

    app.register_blueprint(api_bp, url_prefix=app.config["API_PREFIX"])

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify(error="not_found", message="The requested resource does not exist."), 404

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify(error="internal_error", message="Something went wrong."), 500

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return jsonify(error="token_expired", message="Your session has expired."), 401

    @jwt.invalid_token_loader
    def invalid_token(_reason):
        return jsonify(error="token_invalid", message="Authentication token is invalid."), 401

    @jwt.unauthorized_loader
    def missing_token(_reason):
        return jsonify(error="token_missing", message="Authorization header is missing."), 401

    return app
