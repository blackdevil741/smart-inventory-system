"""
firebase_config.py

Initializes the Firebase Admin SDK exactly once per process and exposes
shared handles (Firestore client, Auth module, Storage bucket) for the
rest of the backend to import.

Why this file exists on its own:
- Firebase Admin must only be initialized a single time per process,
  otherwise it raises a "default app already exists" error.
- Every route/service needs Firestore + Auth + Storage, so we centralize
  the wiring here instead of repeating it everywhere.

Two ways to supply credentials, checked in this order:
1. FIREBASE_SERVICE_ACCOUNT_JSON -- the *entire contents* of the service
   account JSON file, pasted as a single environment variable value.
   Used on deployment platforms like Render, where uploading a file
   isn't convenient but setting an env var is.
2. FIREBASE_SERVICE_ACCOUNT_PATH -- a path to the JSON file on disk.
   Used for local development (see PHASE2_SETUP.md).
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from dotenv import load_dotenv

load_dotenv()

_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
_SERVICE_ACCOUNT_PATH = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH", "./firebase-service-account.json"
)
_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

_firebase_app = None


def init_firebase():
    """Initialize the Firebase Admin app if it hasn't been already.

    Returns the app instance. Safe to call multiple times.
    """
    global _firebase_app

    if firebase_admin._apps:
        # Already initialized (e.g. reloaded by Flask's debug reloader)
        _firebase_app = firebase_admin.get_app()
        return _firebase_app

    if _SERVICE_ACCOUNT_JSON:
        try:
            service_account_info = json.loads(_SERVICE_ACCOUNT_JSON)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "FIREBASE_SERVICE_ACCOUNT_JSON is set but isn't valid JSON. "
                "Make sure you pasted the entire contents of the service "
                "account file, including the surrounding { } braces."
            ) from exc
        cred = credentials.Certificate(service_account_info)
    else:
        if not os.path.exists(_SERVICE_ACCOUNT_PATH):
            raise FileNotFoundError(
                f"Firebase service account key not found at '{_SERVICE_ACCOUNT_PATH}', "
                "and FIREBASE_SERVICE_ACCOUNT_JSON is not set.\n"
                "For local development: download the key from Firebase Console -> "
                "Project Settings -> Service Accounts -> Generate New Private Key, "
                "then set FIREBASE_SERVICE_ACCOUNT_PATH in your .env file.\n"
                "For deployment: set FIREBASE_SERVICE_ACCOUNT_JSON to the full "
                "contents of that same file instead."
            )
        cred = credentials.Certificate(_SERVICE_ACCOUNT_PATH)

    options = {}
    if _STORAGE_BUCKET:
        options["storageBucket"] = _STORAGE_BUCKET

    _firebase_app = firebase_admin.initialize_app(cred, options)
    return _firebase_app


# Initialize immediately on import so `db`, `auth_client`, and `bucket`
# below are ready to use anywhere they're imported.
init_firebase()

db = firestore.client()
auth_client = auth
bucket = storage.bucket() if _STORAGE_BUCKET else None
