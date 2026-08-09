"""
user_model.py

Defines the shape of a user profile document stored in Firestore at
`users/{uid}`, layered on top of the Firebase Auth account (which
handles the actual credentials -- we never store passwords ourselves).

Firestore has no enforced schema, so this module is the single source
of truth for what fields a user document should have, and provides a
small factory + validator so routes/services don't duplicate this logic.
"""

from datetime import datetime, timezone

ALLOWED_ROLES = ("admin", "staff")


def new_user_profile(uid, email, shop_name, role="admin"):
    """Build a new user profile dict ready to write to Firestore.

    The first user to sign up for a shop is made "admin" by default
    (role-based auth for inviting staff accounts is a bonus feature
    for a later phase).
    """
    if role not in ALLOWED_ROLES:
        role = "admin"

    now = datetime.now(timezone.utc).isoformat()

    return {
        "uid": uid,
        "email": email,
        "shop_name": shop_name.strip(),
        "role": role,
        "created_at": now,
        "last_login_at": now,
    }


def validate_signup_payload(data):
    """Return an error message string if the signup payload is invalid, else None."""
    if not isinstance(data, dict):
        return "Invalid request body."

    shop_name = data.get("shop_name", "")
    uid = data.get("uid", "")
    email = data.get("email", "")

    if not uid or not isinstance(uid, str):
        return "Missing user ID."
    if not email or "@" not in email:
        return "A valid email is required."
    if not shop_name or len(shop_name.strip()) < 2:
        return "Shop/vendor name must be at least 2 characters."

    return None
