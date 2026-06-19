"""Aplicacao Flask com endpoints de dados para o dashboard SAD."""

import sys
import json
import datetime
from decimal import Decimal
from pathlib import Path

from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from flask_restx import Api
from psycopg2.extras import RealDictRow


class SADJSONProvider(DefaultJSONProvider):
    """JSON provider que serializa Decimal, date, RealDictRow."""

    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        if isinstance(o, RealDictRow):
            return dict(o)
        return super().default(o)

# Permite imports absolutos do projeto quando executado diretamente
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from src.backend.api.docs import register_namespaces


def create_app():
    app = Flask(__name__)
    app.json_provider_class = SADJSONProvider
    app.json = SADJSONProvider(app)

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
