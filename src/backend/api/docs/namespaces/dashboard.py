"""Namespace do modulo principal (dashboard)."""

from flask import request
from flask_restx import Namespace, Resource


def create_dashboard_namespace(deps, models):
    ns = Namespace("dashboard", path="/api/v1", description="Modulo principal de dashboard")

    @ns.route("/kpis")
    class KpisResource(Resource):
        @ns.doc("get_kpis")
        @ns.marshal_with(models["kpis"])
        def get(self):
            db, service = deps.build_dashboard_service()
            try:
                return service.get_kpis(), 200
            finally:
                db.close()

    @ns.route("/pacientes")
    class PacientesResource(Resource):
        @ns.doc(params={"limite": "Quantidade maxima de pacientes (1-500)"})
        @ns.marshal_list_with(models["paciente_resumo"])
        def get(self):
            limite = request.args.get("limite", default=50, type=int)
            limite = max(1, min(limite, 500))

            db, service = deps.build_dashboard_service()
            try:
                df = service.get_pacientes_dataframe(limite=limite)
                return df.to_dict(orient="records"), 200
            finally:
                db.close()

    @ns.route("/distribuicao/grau")
    class DistribuicaoGrauResource(Resource):
        @ns.doc("get_distribuicao_grau")
        @ns.marshal_list_with(models["distribuicao_grau"])
        def get(self):
            db, service = deps.build_dashboard_service()
            try:
                df = service.get_grau_distribuicao_dataframe()
                return df.to_dict(orient="records"), 200
            finally:
                db.close()

    @ns.route("/distribuicao/risco")
    class DistribuicaoRiscoResource(Resource):
        @ns.doc("get_distribuicao_risco")
        @ns.marshal_list_with(models["distribuicao_risco"])
        def get(self):
            db, service = deps.build_dashboard_service()
            try:
                df = service.get_risco_distribuicao_dataframe()
                return df.to_dict(orient="records"), 200
            finally:
                db.close()

    @ns.route("/materialized-views/refresh")
    class RefreshMaterializedViewsResource(Resource):
        @ns.doc("refresh_materialized_views")
        @ns.marshal_with(models["refresh"])
        def post(self):
            return deps.refresh_materialized_views(), 200

    return ns
