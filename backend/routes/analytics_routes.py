"""
analytics_routes.py

Analytics endpoints powering the Chart.js visualizations on the
Analytics page:
  - GET /api/analytics/category-distribution
  - GET /api/analytics/monthly-growth
  - GET /api/analytics/stock-value
  - GET /api/analytics/most-active-products (approximate "most sold")
"""

from flask import Blueprint, request
from utils.auth_middleware import require_auth
from utils.responses import success_response, error_response
from services.analytics_service import (
    get_category_distribution, get_monthly_growth,
    get_stock_value_breakdown, get_most_active_products,
)

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/api/analytics/category-distribution", methods=["GET"])
@require_auth
def category_distribution():
    try:
        return success_response(data=get_category_distribution())
    except Exception as exc:  # noqa: BLE001
        return error_response(f"Couldn't load category distribution: {str(exc)}", status_code=500)


@analytics_bp.route("/api/analytics/monthly-growth", methods=["GET"])
@require_auth
def monthly_growth():
    try:
        return success_response(data=get_monthly_growth())
    except Exception as exc:  # noqa: BLE001
        return error_response(f"Couldn't load monthly growth: {str(exc)}", status_code=500)


@analytics_bp.route("/api/analytics/stock-value", methods=["GET"])
@require_auth
def stock_value():
    try:
        return success_response(data=get_stock_value_breakdown())
    except Exception as exc:  # noqa: BLE001
        return error_response(f"Couldn't load stock value breakdown: {str(exc)}", status_code=500)


@analytics_bp.route("/api/analytics/most-active-products", methods=["GET"])
@require_auth
def most_active_products():
    limit = request.args.get("limit", default=5, type=int)
    try:
        data = get_most_active_products(limit=limit)
        return success_response(
            data=data,
            message="Approximated from recorded stock decreases, not verified point-of-sale data.",
        )
    except Exception as exc:  # noqa: BLE001
        return error_response(f"Couldn't load most-active products: {str(exc)}", status_code=500)
