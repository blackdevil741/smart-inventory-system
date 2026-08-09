"""
log_model.py

Defines the Inventory Log / Activity entry schema. Every create, edit,
delete, or stock adjustment writes one of these, powering the Activity
Timeline / Recent Updates features and enabling "Undo Last Update"
later, since each log entry keeps a snapshot of the product's state
before the change.
"""

from datetime import datetime, timezone

ACTION_TYPES = ("created", "updated", "deleted", "stock_increased", "stock_decreased")


def new_log_entry(product_id, product_name, action_type, actor_uid, before=None, after=None, note=None):
    if action_type not in ACTION_TYPES:
        action_type = "updated"

    return {
        "product_id": product_id,
        "product_name": product_name,
        "action_type": action_type,
        "actor_uid": actor_uid,
        "before": before,
        "after": after,
        "note": note,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
