"""
product_service.py

Firestore business logic for products: create, read, update, delete,
search/filter/sort, and stock adjustments. Kept separate from
routes/products_routes.py so route handlers stay thin (parse request
-> call service -> format response).
"""

from firebase_config import db
from models.product_model import new_product_doc, build_update_fields
from models.log_model import new_log_entry

PRODUCTS_COLLECTION = "products"
LOGS_COLLECTION = "logs"


def _write_log(product_id, product_name, action_type, actor_uid, before=None, after=None, note=None):
    entry = new_log_entry(product_id, product_name, action_type, actor_uid, before, after, note)
    db.collection(LOGS_COLLECTION).add(entry)


def create_product(data, actor_uid):
    """Create a new product document. Returns the created product
    (including its generated id)."""
    doc = new_product_doc(data, actor_uid)
    doc_ref = db.collection(PRODUCTS_COLLECTION).document()
    doc_ref.set(doc)

    doc["id"] = doc_ref.id
    _write_log(doc_ref.id, doc["name"], "created", actor_uid, after=doc)
    return doc


def get_product(product_id):
    """Fetch a single product by id. Returns None if not found."""
    doc = db.collection(PRODUCTS_COLLECTION).document(product_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def list_products(search=None, category=None, stock_filter=None, sort_by=None):
    """Fetch products from Firestore, then apply search/filter/sort in
    Python. Firestore's query capabilities are limited for combined
    text search + multiple filters, so for a dataset this size
    (a single small shop's inventory) filtering in-memory after one
    fetch is simpler and avoids needing composite indexes.
    """
    docs = db.collection(PRODUCTS_COLLECTION).stream()
    products = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        products.append(item)

    if search:
        term = search.strip().lower()
        products = [
            p for p in products
            if term in p.get("name", "").lower()
            or term in p.get("sku", "").lower()
            or term in p.get("vendor_name", "").lower()
            or term in p.get("category", "").lower()
        ]

    if category:
        products = [p for p in products if p.get("category", "").lower() == category.lower()]

    if stock_filter == "low_stock":
        products = [
            p for p in products
            if 0 < p.get("quantity", 0) <= p.get("min_quantity_threshold", 5)
        ]
    elif stock_filter == "out_of_stock":
        products = [p for p in products if p.get("quantity", 0) <= 0]

    sort_key_map = {
        "name_asc": (lambda p: p.get("name", "").lower(), False),
        "name_desc": (lambda p: p.get("name", "").lower(), True),
        "quantity_asc": (lambda p: p.get("quantity", 0), False),
        "quantity_desc": (lambda p: p.get("quantity", 0), True),
        "price_asc": (lambda p: p.get("selling_price", 0), False),
        "price_desc": (lambda p: p.get("selling_price", 0), True),
        "newest": (lambda p: p.get("created_at", ""), True),
    }
    key_func, reverse = sort_key_map.get(sort_by, sort_key_map["newest"])
    products.sort(key=key_func, reverse=reverse)

    return products


def update_product(product_id, data, actor_uid):
    """Update an existing product. Returns the updated product, or
    None if the product doesn't exist."""
    doc_ref = db.collection(PRODUCTS_COLLECTION).document(product_id)
    existing = doc_ref.get()
    if not existing.exists:
        return None

    before = existing.to_dict()
    update_fields = build_update_fields(data)
    doc_ref.set(update_fields, merge=True)

    after = {**before, **update_fields}
    _write_log(product_id, after.get("name", before.get("name", "")), "updated", actor_uid, before=before, after=after)

    after["id"] = product_id
    return after


def delete_product(product_id, actor_uid):
    """Delete a product. Returns True if deleted, False if it didn't exist."""
    doc_ref = db.collection(PRODUCTS_COLLECTION).document(product_id)
    existing = doc_ref.get()
    if not existing.exists:
        return False

    before = existing.to_dict()
    doc_ref.delete()
    _write_log(product_id, before.get("name", ""), "deleted", actor_uid, before=before)
    return True


def adjust_stock(product_id, delta, actor_uid):
    """Increase or decrease a product's quantity by `delta` (can be
    negative). Quantity is clamped at 0 (never goes negative).
    Returns the updated product, or None if not found."""
    doc_ref = db.collection(PRODUCTS_COLLECTION).document(product_id)
    existing = doc_ref.get()
    if not existing.exists:
        return None

    before = existing.to_dict()
    current_qty = before.get("quantity", 0)
    new_qty = max(0, current_qty + delta)

    from datetime import datetime, timezone
    doc_ref.set({"quantity": new_qty, "updated_at": datetime.now(timezone.utc).isoformat()}, merge=True)

    action = "stock_increased" if delta > 0 else "stock_decreased"
    _write_log(
        product_id, before.get("name", ""), action, actor_uid,
        before={"quantity": current_qty}, after={"quantity": new_qty},
        note=f"Adjusted by {delta:+d}",
    )

    after = {**before, "quantity": new_qty, "id": product_id}
    return after


def export_products_csv():
    """Export all products as CSV bytes, matching the fields a bulk
    import expects, so export->edit->import round-trips cleanly."""
    import csv
    import io

    products = list_products(sort_by="name_asc")
    headers = ["name", "sku", "category", "quantity", "cost_price", "selling_price", "vendor_name", "min_quantity_threshold"]

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers, extrasaction="ignore")
    writer.writeheader()
    for p in products:
        writer.writerow({k: p.get(k, "") for k in headers})

    return buffer.getvalue().encode("utf-8")


def import_products_csv(file_bytes, actor_uid):
    """Bulk-import products from CSV bytes. Each valid row is created
    as a new product (does not attempt to match/update existing SKUs --
    kept simple and predictable: import always creates new records).

    Returns a summary dict: {created: int, errors: [{row, message}]}.
    """
    import csv
    import io
    from models.product_model import validate_product_payload

    text = file_bytes.decode("utf-8-sig")  # handles Excel's BOM-prefixed CSVs
    reader = csv.DictReader(io.StringIO(text))

    created = 0
    errors = []

    required_columns = {"name", "sku", "category"}
    if not reader.fieldnames or not required_columns.issubset(set(reader.fieldnames)):
        return {
            "created": 0,
            "errors": [{"row": 0, "message": f"CSV must include columns: {', '.join(required_columns)}"}],
        }

    for i, row in enumerate(reader, start=2):  # start=2: row 1 is the header
        validation_error = validate_product_payload(row)
        if validation_error:
            errors.append({"row": i, "message": validation_error})
            continue

        try:
            create_product(row, actor_uid)
            created += 1
        except Exception as exc:  # noqa: BLE001
            errors.append({"row": i, "message": str(exc)})

    return {"created": created, "errors": errors}
