"""
vendors_routes.py

Blueprint placeholder for the vendors feature.
Implemented in a later phase of the build. Registered now so the
routing architecture (app.py -> blueprints) is visible from Phase 1
onward and the folder structure matches the final project layout.
"""

from flask import Blueprint
from utils.responses import error_response

vendors_bp = Blueprint("vendors", __name__)


@vendors_bp.route("/api/vendors/_status", methods=["GET"])
def vendors_status():
    return error_response(
        "This module is not implemented yet -- coming in a later phase.",
        status_code=501,
    )
