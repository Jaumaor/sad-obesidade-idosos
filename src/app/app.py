"""Aplicação Flask para o frontend do dashboard SAD."""

import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request
import requests

# Ajuste do Path para imports do projeto
# Isso garante que o Python encontre o arquivo 'config'
root_path = Path(__file__).resolve().parent.parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

try:
    from config import ClinicalConfig
except ImportError:
    # Fallback caso o arquivo config não seja encontrado durante o desenvolvimento
    class ClinicalConfig:
        pass

def create_app(backend_url: str = "http://127.0.0.1:8000"):
    """Factory para criar a aplicação Flask."""
    
    app = Flask(
        __name__,
        template_folder=Path(__file__).parent / "templates",
        static_folder=Path(__file__).parent / "static",
        static_url_path="/static"
    )
    
    app.config["BACKEND_URL"] = backend_url

    # ===== ROTAS DE PÁGINA =====

    @app.get("/")
    @app.get("/dashboard")
    def index():
        """Serve a página principal do dashboard."""
        return render_template("index.html")

    @app.get("/pacientes")
    def pacientes_page():
        # Dica: No futuro, você pode criar um 'pacientes.html'
        return render_template("index.html")

    @app.get("/mapa")
    def mapa_page():
        return render_template("index.html")

    # ===== ROTAS DE API (Proxy para o backend) =====
    # Estas rotas chamam o seu backend Python que processa o ML e o PostGIS

    @app.get("/api/v1/kpis")
    def get_kpis():
        try:
            response = requests.get(f"{app.config['BACKEND_URL']}/api/v1/kpis", timeout=5)
            response.raise_for_status()
            return jsonify(response.json()), 200
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erro ao obter KPIs: {e}")
            return jsonify({"error": "Backend indisponível"}), 503

    @app.get("/api/v1/pacientes")
    def get_pacientes():
        limite = request.args.get("limite", default=50, type=int)
        try:
            response = requests.get(
                f"{app.config['BACKEND_URL']}/api/v1/pacientes",
                params={"limite": limite},
                timeout=5
            )
            response.raise_for_status()
            return jsonify(response.json()), 200
        except requests.exceptions.RequestException:
            return jsonify({"error": "Erro ao listar pacientes"}), 503

    @app.get("/api/v1/distribuicao/risco")
    def get_distribuicao_risco():
        try:
            response = requests.get(
                f"{app.config['BACKEND_URL']}/api/v1/distribuicao/risco",
                timeout=5
            )
            response.raise_for_status()
            return jsonify(response.json()), 200
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erro ao obter distribuição de risco: {e}")
            return jsonify({"error": "Erro ao buscar distribuição de risco"}), 503

    @app.get("/api/v1/distribuicao/grau")
    def get_distribuicao_grau():
        try:
            response = requests.get(
                f"{app.config['BACKEND_URL']}/api/v1/distribuicao/grau",
                timeout=5
            )
            response.raise_for_status()
            return jsonify(response.json()), 200
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erro ao obter distribuição de grau: {e}")
            return jsonify({"error": "Erro ao buscar distribuição de grau"}), 503

    @app.post("/api/v1/materialized-views/refresh")
    def refresh_materialized_views():
        try:
            response = requests.post(
                f"{app.config['BACKEND_URL']}/api/v1/materialized-views/refresh",
                timeout=5
            )
            response.raise_for_status()
            return jsonify(response.json()), 200
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erro ao atualizar materialized views: {e}")
            return jsonify({"error": "Erro ao atualizar views"}), 503

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "sad-frontend",
            "backend_url": app.config["BACKEND_URL"]
        }), 200

    return app

if __name__ == "__main__":
    # Inicializa a aplicação na porta 5000
    application = create_app()
    application.run(host="127.0.0.1", port=5000, debug=True)