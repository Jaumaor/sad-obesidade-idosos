"""Namespace do modulo de mapa de risco (stub inicial)."""

from flask_restx import Namespace, Resource


def create_mapa_risco_namespace(models):
    ns = Namespace("mapa-risco", path="/api/v1", description="Modulo de mapa de risco")

    @ns.route("/mapa-risco/modulo-status")
    class MapaRiscoStatusResource(Resource):
        @ns.doc("mapa_risco_modulo_status")
        @ns.marshal_with(models["module_status"])
        def get(self):
            return {
                "modulo": "mapa-risco",
                "status": "planejado",
                "mensagem": "Modulo em desenvolvimento incremental.",
            }, 200

    return ns
