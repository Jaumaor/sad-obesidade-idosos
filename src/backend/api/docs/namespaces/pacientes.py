"""Namespace do modulo de pacientes com endpoints funcionais."""

from flask import request
from flask_restx import Namespace, Resource


def create_pacientes_namespace(deps, models):
    ns = Namespace("pacientes", path="/api/v1", description="Modulo de pacientes")

    @ns.route("/pacientes/buscar")
    class PacientesBuscarResource(Resource):
        @ns.doc(
            "buscar_pacientes",
            params={
                "territorio_ids": "IDs de territórios (ex: 1,2,3)",
                "unidade_saude_ids": "IDs de unidades de saúde (ex: 1,2)",
                "idade_minima": "Idade mínima",
                "idade_maxima": "Idade máxima",
                "em_acompanhamento": "Filtrar por acompanhamento (true/false)",
                "limite": "Máximo de resultados (padrão: 100)",
            }
        )
        @ns.marshal_list_with(models["paciente_busca_resultado"])
        def get(self):
            """Busca pacientes com filtros avançados"""
            territorio_ids = request.args.get("territorio_ids", default=None, type=str)
            unidade_saude_ids = request.args.get("unidade_saude_ids", default=None, type=str)
            idade_minima = request.args.get("idade_minima", default=None, type=int)
            idade_maxima = request.args.get("idade_maxima", default=None, type=int)
            em_acompanhamento = request.args.get("em_acompanhamento", default=None, type=lambda x: x.lower() == 'true')
            limite = request.args.get("limite", default=100, type=int)
            limite = max(1, min(limite, 500))

            # Parse arrays de IDs
            terr_array = None
            if territorio_ids:
                try:
                    terr_array = [int(x.strip()) for x in territorio_ids.split(',')]
                except ValueError:
                    return {"error": "territorio_ids inválido"}, 400

            unid_array = None
            if unidade_saude_ids:
                try:
                    unid_array = [int(x.strip()) for x in unidade_saude_ids.split(',')]
                except ValueError:
                    return {"error": "unidade_saude_ids inválido"}, 400

            db, service = deps.build_dashboard_service()
            try:
                repo = service.repo
                pacientes = repo.buscar_pacientes(
                    territorio_ids=terr_array,
                    unidade_saude_ids=unid_array,
                    idade_minima=idade_minima,
                    idade_maxima=idade_maxima,
                    em_acompanhamento=em_acompanhamento,
                    limite=limite
                )
                return pacientes, 200
            finally:
                db.close()

    @ns.route("/pacientes/<paciente_id>/acompanhamentos")
    class PacienteAcompanhamentosResource(Resource):
        @ns.doc(
            "get_paciente_acompanhamentos",
            params={"limite": "Máximo de registros (padrão: 50)"}
        )
        @ns.marshal_list_with(models["acompanhamento"])
        def get(self, paciente_id):
            """Retorna histórico de acompanhamentos (visitas/consultas)"""
            limite = request.args.get("limite", default=50, type=int)
            limite = max(1, min(limite, 500))

            db, service = deps.build_dashboard_service()
            try:
                repo = service.repo
                acompanhamentos = repo.get_paciente_acompanhamentos(paciente_id, limite=limite)
                return acompanhamentos, 200
            finally:
                db.close()

    @ns.route("/pacientes/<paciente_id>/comorbidades")
    class PacienteComorbidadesResource(Resource):
        @ns.doc("get_paciente_comorbidades")
        @ns.marshal_list_with(models["comorbidade"])
        def get(self, paciente_id):
            """Retorna condições crônicas (comorbidades) do paciente"""
            db, service = deps.build_dashboard_service()
            try:
                repo = service.repo
                comorbidades = repo.get_paciente_comorbidades(paciente_id)
                return comorbidades, 200
            finally:
                db.close()

    @ns.route("/pacientes/<paciente_id>/alertas")
    class PacienteAlertasResource(Resource):
        @ns.doc(
            "get_paciente_alertas",
            params={"limite": "Máximo de alertas (padrão: 50)"}
        )
        @ns.marshal_list_with(models["alerta"])
        def get(self, paciente_id):
            """Retorna alertas gerados para o paciente"""
            limite = request.args.get("limite", default=50, type=int)
            limite = max(1, min(limite, 500))

            db, service = deps.build_dashboard_service()
            try:
                repo = service.repo
                alertas = repo.get_paciente_alertas(paciente_id, limite=limite)
                return alertas, 200
            finally:
                db.close()

    @ns.route("/pacientes/modulo-status")
    class PacientesStatusResource(Resource):
        @ns.doc("pacientes_modulo_status")
        @ns.marshal_with(models["module_status"])
        def get(self):
            """Status do módulo de pacientes"""
            return {
                "modulo": "pacientes",
                "status": "ativo",
                "mensagem": "Módulo funcional com busca, detalhes, histórico e alertas.",
            }, 200

    @ns.route("/pacientes/<paciente_id>")
    class PacienteDetalheResource(Resource):
        @ns.doc("get_paciente_detalhes")
        @ns.marshal_with(models["paciente_detalhes"])
        def get(self, paciente_id):
            """Retorna detalhes completos de um paciente"""
            db, service = deps.build_dashboard_service()
            try:
                repo = service.repo
                paciente = repo.get_paciente_detalhes(paciente_id)
                if not paciente:
                    return {"error": "Paciente não encontrado"}, 404
                return paciente, 200
            finally:
                db.close()


    return ns
