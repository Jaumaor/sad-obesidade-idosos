"""Aplicacao Flask com endpoints de dados para o dashboard SAD."""

import sys
from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api

# Permite imports absolutos do projeto quando executado diretamente
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from src.backend.api.docs import register_namespaces


def create_app():
    app = Flask(__name__)

    # Habilita CORS para requisições do frontend
    CORS(app, origins=["http://127.0.0.1:5000", "http://localhost:5000"])

    api = Api(
        app,
        version="1.0",
        title="SAD Backend API",
        description="API de dados para o Sistema de Apoio a Decisao (SAD)",
        doc="/docs",
    )

    register_namespaces(api)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "sad-backend-api"}), 200

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="127.0.0.1", port=8000, debug=True)
