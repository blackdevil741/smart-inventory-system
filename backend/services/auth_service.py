"""
auth_service.py

Firestore business logic for user profiles. The actual sign-in/sign-up
credential check is handled by Firebase Auth on the frontend (that's
how Firebase is designed to work) -- this service is responsible for
the parts Firebase Auth doesn't cover: storing shop/vendor profile
data (shop name, role) alongside the auth account, keyed by uid.
"""

from datetime import datetime, timezone
from firebase_config import db
from models.user_model import new_user_profile

USERS_COLLECTION = "users"


def create_user_profile(uid, email, shop_name, role="admin"):
    """Create a Firestore profile doc for a newly-signed-up user.

    Idempotent: if a profile already exists for this uid, it's returned
    as-is instead of being overwritten (protects against duplicate
    signup calls, e.g. from a double form submission).
    """
    doc_ref = db.collection(USERS_COLLECTION).document(uid)
    existing = doc_ref.get()

    if existing.exists:
        return existing.to_dict()

    profile = new_user_profile(uid, email, shop_name, role)
    doc_ref.set(profile)
    return profile


def get_user_profile(uid):
    """Fetch a user's profile document. Returns None if it doesn't exist."""
    doc = db.collection(USERS_COLLECTION).document(uid).get()
    return doc.to_dict() if doc.exists else None


def touch_last_login(uid):
    """Update last_login_at on the user's profile. Called after a successful login."""
    doc_ref = db.collection(USERS_COLLECTION).document(uid)
    doc_ref.set(
        {"last_login_at": datetime.now(timezone.utc).isoformat()},
        merge=True,
    )
