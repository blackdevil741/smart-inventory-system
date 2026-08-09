"""
product_model.py

Defines the Product schema used across the app, and validates incoming
data before it's written to Firestore (Firestore itself has no schema
enforcement, so this module is the single source of truth).

Fields:
    name              str, required
    sku               str, required, unique-ish (not enforced at DB level,
                       but checked on create to warn about duplicates)
    category          str, required
    quantity          int, >= 0
    cost_price        float, >= 0
    selling_price      float, >= 0
    vendor_name       str, optional
    min_quantity_threshold  int, >= 0 (used for low-stock alerts)
    created_at        ISO timestamp string, set server-side
    updated_at        ISO timestamp string, set server-side
    created_by        uid of the user who created it
"""

from datetime import datetime, timezone


REQUIRED_FIELDS = ("name", "sku", "category")


def validate_product_payload(data, partial=False):
    """Validate a product create/update payload.

    Returns an error message string if invalid, else None.
    If `partial` is True, missing fields are allowed (used for edits
    where only some fields are being changed).
    """
    if not isinstance(data, dict):
        return "Invalid request body."

    if not partial:
        for field in REQUIRED_FIELDS:
            if not str(data.get(field, "")).strip():
                return f"'{field}' is required."

    if "quantity" in data:
        try:
            qty = int(data["quantity"])
            if qty < 0:
                return "Quantity cannot be negative."
        except (ValueError, TypeError):
            return "Quantity must be a whole number."

    if "min_quantity_threshold" in data:
        try:
            threshold = int(data["min_quantity_threshold"])
            if threshold < 0:
                return "Minimum quantity threshold cannot be negative."
        except (ValueError, TypeError):
            return "Minimum quantity threshold must be a whole number."

    for price_field in ("cost_price", "selling_price"):
        if price_field in data:
            try:
                price = float(data[price_field])
                if price < 0:
                    return f"'{price_field}' cannot be negative."
            except (ValueError, TypeError):
                return f"'{price_field}' must be a number."

    return None


def new_product_doc(data, created_by_uid):
    """Build a Firestore-ready product document from validated input."""
    now = datetime.now(timezone.utc).isoformat()

    return {
        "name": str(data.get("name", "")).strip(),
        "sku": str(data.get("sku", "")).strip().upper(),
        "category": str(data.get("category", "")).strip(),
        "quantity": int(data.get("quantity", 0) or 0),
        "cost_price": float(data.get("cost_price", 0) or 0),
        "selling_price": float(data.get("selling_price", 0) or 0),
        "vendor_name": str(data.get("vendor_name", "")).strip(),
        "min_quantity_threshold": int(data.get("min_quantity_threshold", 5) or 5),
        "created_at": now,
        "updated_at": now,
        "created_by": created_by_uid,
    }


def build_update_fields(data):
    """Build a dict of only the fields present in `data`, ready for a
    Firestore merge-update. Always stamps `updated_at`."""
    updatable = (
        "name", "sku", "category", "quantity", "cost_price",
        "selling_price", "vendor_name", "min_quantity_threshold",
    )
    fields = {}
    for key in updatable:
        if key in data:
            if key == "sku":
                fields[key] = str(data[key]).strip().upper()
            elif key in ("name", "category", "vendor_name"):
                fields[key] = str(data[key]).strip()
            elif key in ("quantity", "min_quantity_threshold"):
                fields[key] = int(data[key])
            elif key in ("cost_price", "selling_price"):
                fields[key] = float(data[key])

    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    return fields
