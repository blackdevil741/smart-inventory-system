"""
dashboard_routes.py

Dashboard summary endpoints:
  - GET /api/dashboard/summary -- total products, low/out-of-stock
    counts, category count, total stock value, low-stock items list
  - GET /api/dashboard/activity -- recent inventory activity feed
"""

from flask import Blueprint, request
from utils.auth_middleware import require_auth
from utils.responses import success_response, error_response
from services.dashboard_service import get_dashboard_summary, get_recent_activity

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard/summary", methods=["GET"])
@require_auth
def dashboard_summary():
    try:
        summary = get_dashboard_summary()
        return success_response(data=summary)
    except Exception as exc:  # noqa: BLE001
        return error_response(f"Couldn't load dashboard summary: {str(exc)}", status_code=500)


@dashboard_bp.route("/api/dashboard/activity", methods=["GET"])
@require_auth
def dashboard_activity():
    limit = request.args.get("limit", default=15, type=int)
    try:
        activity = get_recent_activity(limit=limit)
        return success_response(data=activity)
    except Exception as exc:  # noqa: BLE001
        return error_response(f"Couldn't load activity feed: {str(exc)}", status_code=500)
