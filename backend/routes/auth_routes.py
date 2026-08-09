"""
auth_routes.py

Auth-related API endpoints. Important: Firebase Auth itself (sign-in,
sign-up, password reset) happens on the FRONTEND via the Firebase
client SDK -- that's the standard, recommended way to use Firebase
Auth, and the backend never sees passwords.

This blueprint covers what the backend IS responsible for:
  - POST /api/auth/register-profile
      Called right after a successful client-side signup, to create
      the matching Firestore user profile (shop name, role).
  - GET /api/auth/me
      Returns the caller's profile, given a valid ID token. Also used
      by the frontend to confirm a token is still valid after reload.
"""

from flask import Blueprint, request
from firebase_admin import auth as firebase_auth
from utils.auth_middleware import require_auth
from utils.responses import success_response, error_response
from models.user_model import validate_signup_payload
from services.auth_service import create_user_profile, get_user_profile, touch_last_login

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/api/auth/register-profile", methods=["POST"])
@require_auth
def register_profile():
    """Create the Firestore profile doc for a just-signed-up user.

    Protected by @require_auth so only the legitimately-authenticated
    user (matching the token's uid) can create their own profile --
    the uid in the request body must match the token's uid.
    """
    data = request.get_json(silent=True) or {}

    token_uid = request.user.get("uid")
    data["uid"] = token_uid  # never trust a client-supplied uid; always use the token's
    data["email"] = data.get("email") or request.user.get("email", "")

    validation_error = validate_signup_payload(data)
    if validation_error:
        return error_response(validation_error, status_code=400)

    profile = create_user_profile(
        uid=token_uid,
        email=data["email"],
        shop_name=data["shop_name"],
    )
    return success_response(data=profile, message="Profile created.", status_code=201)


@auth_bp.route("/api/auth/me", methods=["GET"])
@require_auth
def get_me():
    """Return the current user's profile and touch their last-login timestamp."""
    uid = request.user.get("uid")
    profile = get_user_profile(uid)

    if profile is None:
        return error_response(
            "No profile found for this account. Please complete signup.",
            status_code=404,
        )

    touch_last_login(uid)
    return success_response(data=profile)


@auth_bp.route("/api/auth/verify", methods=["GET"])
@require_auth
def verify_token():
    """Lightweight endpoint the frontend can call to confirm a token is
    still valid (e.g. right after page load, before rendering a
    protected page)."""
    return success_response(data={"uid": request.user.get("uid"), "email": request.user.get("email")})
