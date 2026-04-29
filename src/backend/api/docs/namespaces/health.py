"""Namespace de healthcheck da API."""

from flask_restx import Namespace, Resource


def create_health_namespace(models):
    ns = Namespace("health", path="", description="Saude e status da API")

    @ns.route("/health")
    class HealthResource(Resource):
        @ns.doc("health")
        @ns.marshal_with(models["health"])
        def get(self):
            return {"status": "ok", "service": "sad-backend-api"}, 200

    return ns
