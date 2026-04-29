"""Registro modular de namespaces da API."""

from src.backend.api.docs.dependencies import ApiDependencies
from src.backend.api.docs.models import register_models
from src.backend.api.docs.namespaces.configuracoes import create_configuracoes_namespace
from src.backend.api.docs.namespaces.dashboard import create_dashboard_namespace
from src.backend.api.docs.namespaces.health import create_health_namespace
from src.backend.api.docs.namespaces.mapa_risco import create_mapa_risco_namespace
from src.backend.api.docs.namespaces.pacientes import create_pacientes_namespace
from src.backend.api.docs.namespaces.relatorios import create_relatorios_namespace
from src.backend.api.docs.namespaces.risco import create_risco_namespace


def register_namespaces(api):
    """Registra todos os namespaces de forma centralizada."""
    models = register_models(api)
    deps = ApiDependencies()

    namespaces = [
        create_health_namespace(models),
        create_dashboard_namespace(deps, models),
        create_pacientes_namespace(deps, models),
        create_risco_namespace(deps, models),
        create_mapa_risco_namespace(models),
        create_relatorios_namespace(models),
        create_configuracoes_namespace(models),
    ]

    for namespace in namespaces:
        api.add_namespace(namespace)
