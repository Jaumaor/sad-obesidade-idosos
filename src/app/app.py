"""
SENTINELA - Sistema de Apoio à Decisão
Monitoramento de Obesidade em Idosos | SUS Vitória da Conquista
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_login import login_required, current_user
from dotenv import load_dotenv
import requests

# Carregar .env
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# Ajuste do Path para imports do projeto
root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

try:
    from config import ClinicalConfig
except ImportError:
    class ClinicalConfig:
        pass

from src.app.auth import (
    auth_bp, login_manager, init_auth_tables, init_alertas_table,
    contar_alertas_nao_lidos, get_alertas_nao_lidos,
    marcar_alerta_lido, marcar_todos_lidos, gerar_alertas_automaticos,
)
from src.app.mail import init_mail, enviar_pendentes


def create_app(backend_url: str = "http://127.0.0.1:8000"):
    """Factory para criar a aplicação Flask."""

    app = Flask(
        __name__,
        template_folder=Path(__file__).parent / "templates",
        static_folder=Path(__file__).parent / "static",
        static_url_path="/static"
    )

    app.config["BACKEND_URL"] = backend_url
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-troque-em-producao")

    # Flask-Login + Mail
    login_manager.init_app(app)
    app.register_blueprint(auth_bp)
    init_mail(app)

    # Criar tabelas de auth/alertas na inicialização
    with app.app_context():
        try:
            init_auth_tables()
            init_alertas_table()
        except Exception as e:
            app.logger.warning(f"Não foi possível inicializar tabelas de auth: {e}")

    # Injetar dados globais em todos os templates
    @app.context_processor
    def inject_globals():
        alertas_count = 0
        alertas = []
        if current_user.is_authenticated:
            try:
                alertas_count = contar_alertas_nao_lidos()
                alertas = get_alertas_nao_lidos(limite=5)
            except Exception:
                pass
        return dict(
            alertas_count=alertas_count,
            alertas_recentes=alertas,
            usuario=current_user if current_user.is_authenticated else None,
            sistema_nome="SENTINELA",
        )

    # ===== ROTAS DE PÁGINA =====

    @app.get("/")
    @app.get("/dashboard")
    @login_required
    def index():
        """Serve a página principal do dashboard."""
        return render_template("index.html", active_page="dashboard")

    @app.get("/pacientes")
    @login_required
    def pacientes_page():
        total = 0
        try:
            r = requests.get(f"{app.config['BACKEND_URL']}/api/v1/kpis", timeout=5)
            if r.ok:
                total = r.json().get("total_pacientes", 0)
        except Exception:
            pass
        return render_template("pacientes.html", active_page="pacientes", total_pacientes=total)

    @app.get("/pacientes/filtrar")
    @login_required
    def pacientes_filtrar():
        """Retorna fragmento HTML com linhas da tabela (HTMX)."""
        faixa = request.args.get("faixa_etaria", "")
        nivel_risco = request.args.get("nivel_risco", "")
        limite = request.args.get("limite", 50, type=int)

        params = {"limite": min(limite, 500)}
        if faixa == "60-69":
            params["idade_minima"] = 60
            params["idade_maxima"] = 69
        elif faixa == "70-79":
            params["idade_minima"] = 70
            params["idade_maxima"] = 79
        elif faixa == "80+":
            params["idade_minima"] = 80

        try:
            r = requests.get(
                f"{app.config['BACKEND_URL']}/api/v1/pacientes/buscar",
                params=params, timeout=10
            )
            r.raise_for_status()
            pacientes = r.json()
        except Exception as e:
            app.logger.error(f"Erro ao filtrar pacientes: {e}")
            pacientes = []

        if nivel_risco:
            pacientes = [p for p in pacientes if p.get("nivel_risco") == nivel_risco]

        return render_template("partials/pacientes_rows.html", pacientes=pacientes)

    @app.get("/pacientes/<paciente_id>/painel")
    @login_required
    def paciente_painel(paciente_id):
        """Retorna fragmento HTML do painel lateral (HTMX)."""
        try:
            r = requests.get(
                f"{app.config['BACKEND_URL']}/api/v1/pacientes/{paciente_id}",
                timeout=10
            )
            r.raise_for_status()
            p = r.json()
        except Exception as e:
            app.logger.error(f"Erro ao buscar paciente {paciente_id}: {e}")
            return "<p class='text-red-500 text-sm p-6'>Erro ao carregar detalhes</p>"

        return render_template("partials/paciente_painel.html", p=p)

    @app.get("/pacientes/<paciente_id>")
    @login_required
    def paciente_prontuario(paciente_id):
        """Página completa do prontuário individual."""
        try:
            r = requests.get(
                f"{app.config['BACKEND_URL']}/api/v1/pacientes/{paciente_id}",
                timeout=10
            )
            r.raise_for_status()
            p = r.json()
        except Exception as e:
            app.logger.error(f"Erro ao buscar prontuário {paciente_id}: {e}")
            p = None

        acompanhamentos = []
        comorbidades = []
        try:
            ra = requests.get(
                f"{app.config['BACKEND_URL']}/api/v1/pacientes/{paciente_id}/acompanhamentos",
                timeout=10
            )
            if ra.ok:
                acompanhamentos = ra.json()
            rc = requests.get(
                f"{app.config['BACKEND_URL']}/api/v1/pacientes/{paciente_id}/comorbidades",
                timeout=10
            )
            if rc.ok:
                comorbidades = rc.json()
        except Exception:
            pass

        return render_template(
            "prontuario.html",
            active_page="pacientes",
            p=p,
            acompanhamentos=acompanhamentos,
            comorbidades=comorbidades
        )

    @app.get("/mapa")
    @login_required
    def mapa_page():
        return render_template("mapa.html", active_page="mapa")

    @app.get("/relatorios")
    @login_required
    def relatorios_page():
        territorios = []
        risco_dist = []
        kpis = {}
        try:
            rt = requests.get(f"{app.config['BACKEND_URL']}/api/v1/territorio/estatisticas", timeout=10)
            if rt.ok:
                territorios = rt.json()
            rr = requests.get(f"{app.config['BACKEND_URL']}/api/v1/distribuicao/risco", timeout=5)
            if rr.ok:
                risco_dist = rr.json()
            rk = requests.get(f"{app.config['BACKEND_URL']}/api/v1/kpis", timeout=5)
            if rk.ok:
                kpis = rk.json()
        except Exception:
            pass
        return render_template("relatorios.html", active_page="relatorios",
                               territorios=territorios, risco_dist=risco_dist, kpis=kpis)

    @app.get("/configuracoes")
    @login_required
    def configuracoes_page():
        return render_template("configuracoes.html", active_page="configuracoes")

    # ===== ROTAS DE ALERTAS =====

    @app.post("/alertas/marcar-lido/<int:alerta_id>")
    @login_required
    def alerta_marcar_lido(alerta_id):
        marcar_alerta_lido(alerta_id)
        return "", 200

    @app.post("/alertas/marcar-todos-lidos")
    @login_required
    def alertas_marcar_todos():
        marcar_todos_lidos()
        return "", 200

    @app.post("/alertas/gerar")
    @login_required
    def alertas_gerar():
        novos = gerar_alertas_automaticos(app.config["BACKEND_URL"])
        # Tentar enviar emails pendentes
        resultado_email = enviar_pendentes(app.config["BACKEND_URL"])
        return jsonify({"novos_alertas": novos, "email": resultado_email}), 200

    @app.post("/alertas/enviar-emails")
    @login_required
    def alertas_enviar_emails():
        resultado = enviar_pendentes(app.config["BACKEND_URL"])
        return jsonify(resultado), 200

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

    @app.get("/api/v1/mapa/calor")
    def get_mapa_calor():
        try:
            response = requests.get(
                f"{app.config['BACKEND_URL']}/api/v1/mapa/calor",
                timeout=15
            )
            response.raise_for_status()
            return jsonify(response.json()), 200
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erro ao obter mapa de calor: {e}")
            return jsonify({"error": "Erro ao buscar dados do mapa"}), 503

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

    # ===== ROTAS DE API - RISCO (Proxy) =====

    @app.post("/api/v1/risco/predict")
    def predict_risco():
        try:
            response = requests.post(
                f"{app.config['BACKEND_URL']}/api/v1/risco/predict",
                json=request.get_json(),
                timeout=10
            )
            return jsonify(response.json()), response.status_code
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erro ao predizer risco: {e}")
            return jsonify({"error": "Backend indisponível"}), 503

    @app.post("/api/v1/risco/calcular/<paciente_id>")
    def calcular_risco(paciente_id):
        try:
            response = requests.post(
                f"{app.config['BACKEND_URL']}/api/v1/risco/calcular/{paciente_id}",
                timeout=10
            )
            return jsonify(response.json()), response.status_code
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erro ao calcular risco: {e}")
            return jsonify({"error": "Backend indisponível"}), 503

    @app.get("/api/v1/risco/modelo-info")
    def modelo_info():
        try:
            response = requests.get(
                f"{app.config['BACKEND_URL']}/api/v1/risco/modelo-info",
                timeout=5
            )
            return jsonify(response.json()), response.status_code
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erro ao obter info do modelo: {e}")
            return jsonify({"error": "Backend indisponível"}), 503

    @app.get("/api/v1/risco/pacientes-prioritarios")
    def pacientes_prioritarios():
        try:
            response = requests.get(
                f"{app.config['BACKEND_URL']}/api/v1/risco/pacientes-prioritarios",
                params=request.args,
                timeout=10
            )
            return jsonify(response.json()), response.status_code
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Erro ao obter prioritários: {e}")
            return jsonify({"error": "Backend indisponível"}), 503

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "sentinela-frontend",
            "backend_url": app.config["BACKEND_URL"]
        }), 200

    return app

if __name__ == "__main__":
    # Inicializa a aplicação na porta 5000
    application = create_app()
    application.run(host="127.0.0.1", port=5000, debug=True)