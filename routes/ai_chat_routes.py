from flask import Blueprint, request, jsonify
from services.ai_chat_service import ai_chat

ai_chat_bp = Blueprint("ai_chat", __name__)

@ai_chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = data.get("message")

    if not message:
        return jsonify({"error": "message is required"}), 400

    result = ai_chat(message)
    return jsonify(result)