"""
qr_routes.py

QR-related endpoints:
  - GET /api/qr/<product_id> -- generate a QR code image for a product
  - GET /api/qr/resolve/<product_id> -- look up a product by the ID
    encoded in a scanned QR code, so the scanner page can show its
    details and offer stock adjustment buttons.

Decoding the QR code itself happens entirely in the browser (via the
html5-qrcode library) -- this backend never receives the image, only
the product ID that was already decoded client-side.
"""

from flask import Blueprint, request
from utils.auth_middleware import require_auth
from utils.responses import success_response, error_response
from services.qr_service import generate_qr_code_data_url
from services.product_service import get_product

qr_bp = Blueprint("qr", __name__)


@qr_bp.route("/api/qr/<product_id>", methods=["GET"])
@require_auth
def get_product_qr_code(product_id):
    product = get_product(product_id)
    if product is None:
        return error_response("Product not found.", status_code=404)

    qr_data_url = generate_qr_code_data_url(product_id)
    return success_response(data={"product_id": product_id, "qr_image": qr_data_url})


@qr_bp.route("/api/qr/resolve/<product_id>", methods=["GET"])
@require_auth
def resolve_scanned_product(product_id):
    """Called right after a QR code is scanned and decoded in the
    browser. Confirms the product still exists and returns its current
    data so the scanner page can display it and offer stock actions."""
    product = get_product(product_id)
    if product is None:
        return error_response(
            "This QR code doesn't match any product in your inventory. "
            "It may have been deleted.",
            status_code=404,
        )
    return success_response(data=product)
