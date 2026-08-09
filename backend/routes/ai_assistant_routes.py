"""
ai_assistant_routes.py

The AI Inventory Assistant chat endpoint. Rule-based, grounded in live
Firestore data (see services/ai_assistant_service.py for why).
"""

from flask import Blueprint, request
from utils.auth_middleware import require_auth
from utils.responses import success_response, error_response
from services.ai_assistant_service import answer_question

ai_assistant_bp = Blueprint("ai_assistant", __name__)


@ai_assistant_bp.route("/api/ai-assistant/ask", methods=["POST"])
@require_auth
def ask_assistant():
    data = request.get_json(silent=True) or {}
    question = str(data.get("question", "")).strip()

    if not question:
        return error_response("Please provide a question.", status_code=400)

    try:
        answer = answer_question(question)
        return success_response(data={"question": question, "answer": answer})
    except Exception as exc:  # noqa: BLE001
        return error_response(f"Couldn't process that question: {str(exc)}", status_code=500)
