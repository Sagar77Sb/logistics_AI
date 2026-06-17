from flask import Blueprint, request, jsonify
from services.ai_chat_service import ai_chat
from services.response_utils import error_response

ai_chat_bp = Blueprint("ai_chat", __name__)


def _get_request_param(name, data, default=None):
    if request.args.get(name) is not None:
        return request.args.get(name)
    return data.get(name, default)


@ai_chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message")

    if not message or not str(message).strip():
        payload, status_code = error_response(
            message="Validation failed.",
            code="VALIDATION_ERROR",
            details="message is required",
            status_code=400,
        )
        return jsonify(payload), status_code

    page = _get_request_param("page", data, 1)
    limit = _get_request_param("limit", data, 10)
    debug = bool(_get_request_param("debug", data, False))

    payload, status_code = ai_chat(
        message=str(message).strip(),
        page=page,
        limit=limit,
        debug=debug,
    )
    return jsonify(payload), status_code
