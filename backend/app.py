"""
app.py

Application entry point. Uses the Flask "app factory" pattern so the
app can be created fresh for testing, WSGI servers (gunicorn), or the
local dev server without import-order surprises.

Run locally with:
    python app.py

Run in production with (see Phase 10 for full deployment steps):
    gunicorn app:app
"""

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Importing firebase_config here (before routes) guarantees the Firebase
# Admin SDK is initialized exactly once, before any blueprint that
# depends on `db`/`auth_client`/`bucket` gets imported.
import firebase_config  # noqa: F401

from routes.health_routes import health_bp
from routes.auth_routes import auth_bp
from routes.products_routes import products_bp
from routes.qr_routes import qr_bp
from routes.dashboard_routes import dashboard_bp
from routes.analytics_routes import analytics_bp
from routes.reports_routes import reports_bp
from routes.ai_assistant_routes import ai_assistant_bp
from routes.vendors_routes import vendors_bp

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    # CORS: only allow the frontend origins listed in .env. During local
    # dev this is typically http://localhost:5500 (Live Server / http.server).
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    # Register blueprints. Each one owns a single feature area, matching
    # the frontend/js/services structure on the other side of the API.
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(qr_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(ai_assistant_bp)
    app.register_blueprint(vendors_bp)

    @app.errorhandler(404)
    def not_found(e):
        return {"success": False, "error": "Endpoint not found"}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"success": False, "error": "Internal server error"}, 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
