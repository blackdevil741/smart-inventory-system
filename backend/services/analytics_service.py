"""
analytics_service.py

Aggregates Firestore product + log data into the shapes Chart.js needs
on the Analytics page: category distribution (pie), monthly inventory
growth (bar/line), stock value breakdown, and a "most sold products"
list.

Note on "Most Sold Products": this app doesn't track point-of-sale
transactions (that's outside its scope -- it's an inventory tracker,
not a POS system), so "most sold" is approximated from stock DECREASES
recorded in the activity log (a decrease usually means something sold
or was used up). This is clearly labeled as an approximation in the
API response and on the frontend, rather than presented as exact sales
data.
"""

from collections import defaultdict
from datetime import datetime
from firebase_config import db

PRODUCTS_COLLECTION = "products"
LOGS_COLLECTION = "logs"


def get_category_distribution():
    """Count of products per category, and total quantity per category."""
    products = [doc.to_dict() for doc in db.collection(PRODUCTS_COLLECTION).stream()]

    by_category = defaultdict(lambda: {"product_count": 0, "total_quantity": 0})
    for p in products:
        cat = p.get("category", "Uncategorized").strip() or "Uncategorized"
        by_category[cat]["product_count"] += 1
        by_category[cat]["total_quantity"] += p.get("quantity", 0)

    return [
        {"category": cat, **stats}
        for cat, stats in sorted(by_category.items(), key=lambda kv: -kv[1]["total_quantity"])
    ]


def get_monthly_growth():
    """Number of products created per month, based on created_at.
    Returns the last 6 months (including empty months) so the chart
    has a consistent x-axis even early in a shop's usage."""
    products = [doc.to_dict() for doc in db.collection(PRODUCTS_COLLECTION).stream()]

    counts = defaultdict(int)
    for p in products:
        created_at = p.get("created_at", "")
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            key = dt.strftime("%Y-%m")
            counts[key] += 1
        except (ValueError, AttributeError):
            continue

    now = datetime.utcnow()
    months = []
    year, month = now.year, now.month
    for _ in range(6):
        key = f"{year:04d}-{month:02d}"
        months.append(key)
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    months.reverse()

    return [{"month": m, "products_added": counts.get(m, 0)} for m in months]


def get_stock_value_breakdown():
    """Total stock value (cost and potential revenue) per category."""
    products = [doc.to_dict() for doc in db.collection(PRODUCTS_COLLECTION).stream()]

    by_category = defaultdict(lambda: {"cost_value": 0.0, "potential_revenue": 0.0})
    total_cost = 0.0
    total_revenue = 0.0

    for p in products:
        cat = p.get("category", "Uncategorized").strip() or "Uncategorized"
        qty = p.get("quantity", 0)
        cost_value = qty * p.get("cost_price", 0)
        revenue_value = qty * p.get("selling_price", 0)

        by_category[cat]["cost_value"] += cost_value
        by_category[cat]["potential_revenue"] += revenue_value
        total_cost += cost_value
        total_revenue += revenue_value

    breakdown = [
        {"category": cat, "cost_value": round(v["cost_value"], 2), "potential_revenue": round(v["potential_revenue"], 2)}
        for cat, v in sorted(by_category.items(), key=lambda kv: -kv[1]["cost_value"])
    ]

    return {
        "by_category": breakdown,
        "total_cost_value": round(total_cost, 2),
        "total_potential_revenue": round(total_revenue, 2),
        "potential_profit": round(total_revenue - total_cost, 2),
    }


def get_most_active_products(limit=5):
    """Approximate 'most sold' by counting stock_decreased log entries
    per product. This is an approximation based on stock movement, not
    verified point-of-sale data -- labeled as such in the API response."""
    logs = [doc.to_dict() for doc in db.collection(LOGS_COLLECTION).where("action_type", "==", "stock_decreased").stream()]

    counts = defaultdict(lambda: {"product_name": "", "decrease_events": 0, "total_decreased": 0})
    for log in logs:
        pid = log.get("product_id")
        if not pid:
            continue
        counts[pid]["product_name"] = log.get("product_name", "Unknown product")
        counts[pid]["decrease_events"] += 1

        before = (log.get("before") or {}).get("quantity", 0)
        after = (log.get("after") or {}).get("quantity", 0)
        counts[pid]["total_decreased"] += max(0, before - after)

    ranked = sorted(counts.values(), key=lambda v: -v["total_decreased"])
    return ranked[:limit]
