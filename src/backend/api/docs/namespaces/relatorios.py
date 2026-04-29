"""Namespace do modulo de relatorios (stub inicial)."""

from flask_restx import Namespace, Resource


def create_relatorios_namespace(models):
    ns = Namespace("relatorios", path="/api/v1", description="Modulo de relatorios")

    @ns.route("/relatorios/modulo-status")
    class RelatoriosStatusResource(Resource):
        @ns.doc("relatorios_modulo_status")
        @ns.marshal_with(models["module_status"])
        def get(self):
            return {
                "modulo": "relatorios",
                "status": "planejado",
                "mensagem": "Modulo em desenvolvimento incremental.",
            }, 200

    return ns
