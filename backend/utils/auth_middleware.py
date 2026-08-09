"""
auth_middleware.py

Decorator that protects Flask routes by verifying the Firebase ID token
sent from the frontend in the `Authorization: Bearer <token>` header.

Usage:
    from utils.auth_middleware import require_auth

    @app.route("/api/products")
    @require_auth
    def list_products():
        # request.user is now available, e.g. request.user["uid"]
        ...
"""

from functools import wraps
from flask import request, jsonify
from firebase_admin import auth as firebase_auth


def require_auth(f):
    """Verify a Firebase ID token before allowing the request through.

    Attaches the decoded token (dict with uid, email, etc.) to
    `request.user` for use inside the route handler.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get("Authorization", "")

        if not header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed Authorization header"}), 401

        id_token = header.split("Bearer ", 1)[1].strip()

        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
        except firebase_auth.ExpiredIdTokenError:
            return jsonify({"error": "Session expired. Please log in again."}), 401
        except firebase_auth.InvalidIdTokenError:
            return jsonify({"error": "Invalid authentication token."}), 401
        except Exception as exc:  # noqa: BLE001 - surface auth errors as 401, not 500
            return jsonify({"error": f"Authentication failed: {str(exc)}"}), 401

        request.user = decoded_token
        return f(*args, **kwargs)

    return decorated
