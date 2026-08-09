"""
products_routes.py

Product CRUD + search/filter/sort + stock adjustment endpoints.
Every route requires a valid Firebase ID token (@require_auth).
"""

from flask import Blueprint, request
from utils.auth_middleware import require_auth
from utils.responses import success_response, error_response
from models.product_model import validate_product_payload
from services.product_service import (
    create_product, get_product, list_products,
    update_product, delete_product, adjust_stock,
    export_products_csv, import_products_csv,
)

products_bp = Blueprint("products", __name__)


@products_bp.route("/api/products", methods=["GET"])
@require_auth
def get_products():
    """List products, with optional search/filter/sort/pagination via query params:
        ?search=milk
        ?category=Dairy
        ?stock_filter=low_stock | out_of_stock
        ?sort_by=name_asc | name_desc | quantity_asc | quantity_desc | price_asc | price_desc | newest
        ?page=1&page_size=20

    Filtering/sorting happens on the full result set (fine at this
    project's scale -- a single small shop's inventory), then the
    requested page is sliced out and returned alongside pagination
    metadata so the frontend can render page controls.
    """
    search = request.args.get("search")
    category = request.args.get("category")
    stock_filter = request.args.get("stock_filter")
    sort_by = request.args.get("sort_by", "newest")
    page = request.args.get("page", default=1, type=int)
    page_size = request.args.get("page_size", default=20, type=int)

    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    all_products = list_products(search=search, category=category, stock_filter=stock_filter, sort_by=sort_by)

    total_items = len(all_products)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    page = min(page, total_pages)

    start = (page - 1) * page_size
    end = start + page_size
    page_items = all_products[start:end]

    return success_response(data={
        "items": page_items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
        },
    })


@products_bp.route("/api/products/<product_id>", methods=["GET"])
@require_auth
def get_single_product(product_id):
    product = get_product(product_id)
    if product is None:
        return error_response("Product not found.", status_code=404)
    return success_response(data=product)


@products_bp.route("/api/products", methods=["POST"])
@require_auth
def add_product():
    data = request.get_json(silent=True) or {}

    validation_error = validate_product_payload(data)
    if validation_error:
        return error_response(validation_error, status_code=400)

    product = create_product(data, actor_uid=request.user.get("uid"))
    return success_response(data=product, message="Product added.", status_code=201)


@products_bp.route("/api/products/<product_id>", methods=["PUT", "PATCH"])
@require_auth
def edit_product(product_id):
    data = request.get_json(silent=True) or {}

    validation_error = validate_product_payload(data, partial=True)
    if validation_error:
        return error_response(validation_error, status_code=400)

    updated = update_product(product_id, data, actor_uid=request.user.get("uid"))
    if updated is None:
        return error_response("Product not found.", status_code=404)

    return success_response(data=updated, message="Product updated.")


@products_bp.route("/api/products/<product_id>", methods=["DELETE"])
@require_auth
def remove_product(product_id):
    deleted = delete_product(product_id, actor_uid=request.user.get("uid"))
    if not deleted:
        return error_response("Product not found.", status_code=404)

    return success_response(message="Product deleted.")


@products_bp.route("/api/products/<product_id>/adjust-stock", methods=["POST"])
@require_auth
def adjust_product_stock(product_id):
    """Body: { "delta": <int> }  e.g. +1, +5, +10, -1, -5, -10"""
    data = request.get_json(silent=True) or {}

    try:
        delta = int(data.get("delta", 0))
    except (ValueError, TypeError):
        return error_response("'delta' must be an integer.", status_code=400)

    if delta == 0:
        return error_response("'delta' cannot be zero.", status_code=400)

    updated = adjust_stock(product_id, delta, actor_uid=request.user.get("uid"))
    if updated is None:
        return error_response("Product not found.", status_code=404)

    return success_response(data=updated, message="Stock updated.")


@products_bp.route("/api/products/export", methods=["GET"])
@require_auth
def export_products():
    from flask import Response
    from datetime import datetime, timezone

    csv_bytes = export_products_csv()
    filename = f"products_export_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"

    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@products_bp.route("/api/products/import", methods=["POST"])
@require_auth
def import_products():
    if "file" not in request.files:
        return error_response("No file uploaded. Attach a CSV file under the 'file' field.", status_code=400)

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return error_response("No file selected.", status_code=400)

    try:
        file_bytes = uploaded_file.read()
        summary = import_products_csv(file_bytes, actor_uid=request.user.get("uid"))
    except Exception as exc:  # noqa: BLE001
        return error_response(f"Couldn't process the CSV file: {str(exc)}", status_code=400)

    message = f"Imported {summary['created']} product(s)."
    if summary["errors"]:
        message += f" {len(summary['errors'])} row(s) had errors."

    return success_response(data=summary, message=message)
