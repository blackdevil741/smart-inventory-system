"""
health_routes.py

Simple health-check endpoint used to verify the server is running and
that Firebase Admin initialized correctly. Useful for Render's health
checks after deployment (Phase 10).
"""

from flask import Blueprint
from firebase_config import db
from utils.responses import success_response, error_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health_check():
    firebase_status = "connected"
    try:
        # Cheap call that proves the Firestore client + credentials work.
        list(db.collections())
    except Exception as exc:  # noqa: BLE001
        firebase_status = f"error: {str(exc)}"

    return success_response(
        data={
            "status": "ok",
            "service": "Smart Inventory System API",
            "firebase": firebase_status,
        }
    )
