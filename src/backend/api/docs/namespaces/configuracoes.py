"""Namespace do modulo de configuracoes (stub inicial)."""

from flask_restx import Namespace, Resource


def create_configuracoes_namespace(models):
    ns = Namespace("configuracoes", path="/api/v1", description="Modulo de configuracoes")

    @ns.route("/configuracoes/modulo-status")
    class ConfiguracoesStatusResource(Resource):
        @ns.doc("configuracoes_modulo_status")
        @ns.marshal_with(models["module_status"])
        def get(self):
            return {
                "modulo": "configuracoes",
                "status": "planejado",
                "mensagem": "Modulo em desenvolvimento incremental.",
            }, 200

    return ns
