"""
responses.py

Small helpers so every API endpoint returns JSON in a consistent shape:

    { "success": true,  "data": ... }
    { "success": false, "error": "message" }

Keeping this consistent makes the frontend's fetch wrapper (js/services/api.js)
simple: it can always check `success` before reading `data` or `error`.
"""

from flask import jsonify


def success_response(data=None, message=None, status_code=200):
    payload = {"success": True}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code


def error_response(message, status_code=400, details=None):
    payload = {"success": False, "error": message}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status_code
