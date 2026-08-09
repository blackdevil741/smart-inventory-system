"""
dashboard_service.py

Aggregates product + log data from Firestore into the summary the
Dashboard page needs: total products, low/out-of-stock counts,
category count, total stock value, and a recent activity feed.

Kept separate from analytics_service.py (chart-specific breakdowns,
built in a later phase) -- this one is about the at-a-glance summary
cards and activity list.
"""

from firebase_config import db

PRODUCTS_COLLECTION = "products"
LOGS_COLLECTION = "logs"


def get_dashboard_summary():
    products = [doc.to_dict() for doc in db.collection(PRODUCTS_COLLECTION).stream()]

    total_products = len(products)
    low_stock_count = sum(
        1 for p in products
        if 0 < p.get("quantity", 0) <= p.get("min_quantity_threshold", 5)
    )
    out_of_stock_count = sum(1 for p in products if p.get("quantity", 0) <= 0)
    categories = {p.get("category", "").strip() for p in products if p.get("category", "").strip()}

    total_stock_value = sum(
        p.get("quantity", 0) * p.get("cost_price", 0) for p in products
    )

    low_stock_items = [
        {"id": p.get("id"), "name": p.get("name"), "quantity": p.get("quantity", 0),
         "min_quantity_threshold": p.get("min_quantity_threshold", 5)}
        for p in products
        if p.get("quantity", 0) <= p.get("min_quantity_threshold", 5)
    ]
    # Sort worst-first (lowest quantity relative to threshold)
    low_stock_items.sort(key=lambda p: p["quantity"])

    return {
        "total_products": total_products,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "category_count": len(categories),
        "total_stock_value": round(total_stock_value, 2),
        "low_stock_items": low_stock_items[:10],
    }


def get_recent_activity(limit=15):
    """Fetch the most recent inventory log entries for the Activity feed."""
    query = (
        db.collection(LOGS_COLLECTION)
        .order_by("timestamp", direction="DESCENDING")
        .limit(limit)
    )
    logs = []
    for doc in query.stream():
        entry = doc.to_dict()
        entry["id"] = doc.id
        logs.append(entry)
    return logs
