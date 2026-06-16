from flask import Flask
from flask_cors import CORS
from routes.rag_routes import rag_bp
from routes.mcp_routes import mcp_bp
from routes.ai_chat_routes import ai_chat_bp

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:3000",
    "http://localhost:5173"
])

app.register_blueprint(rag_bp, url_prefix="/api/rag")
app.register_blueprint(mcp_bp, url_prefix="/api/mcp")
app.register_blueprint(ai_chat_bp, url_prefix="/api/ai")

@app.route("/")
def home():
    return {
        "message": "Logistics AI RAG backend running"
    }

if __name__ == "__main__":
    app.run(debug=True, port=5000)