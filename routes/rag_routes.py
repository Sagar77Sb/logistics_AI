from flask import Blueprint, request, jsonify
from services.ingest_service import ingest_documents, reset_collection
from services.rag_service import ask_rag

rag_bp = Blueprint("rag", __name__)

@rag_bp.route("/ingest", methods=["POST"])
def ingest():
    try:
        result = ingest_documents()
        print("result: ", result)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rag_bp.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        question = data.get("question")

        if not question:
            return jsonify({"error": "question is required"}), 400

        result = ask_rag(question)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rag_bp.route("/reset", methods=["DELETE"])
def reset():
    try:
        result = reset_collection()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500