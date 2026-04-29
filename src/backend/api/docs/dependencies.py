"""Dependencias compartilhadas entre namespaces da API."""

from config import ClinicalConfig
from src.backend.services.dashboard_service import DashboardService
from src.database.connection import DatabaseConnection


class ApiDependencies:
    """Factory de dependencias para resources da API."""

    def build_dashboard_service(self):
        db = DatabaseConnection()
        db.connect_psycopg2()
        service = DashboardService(db, dias_abandono=ClinicalConfig.DIAS_ABANDONO)
        return db, service

    def refresh_materialized_views(self):
        db = DatabaseConnection()
        db.connect_psycopg2()
        try:
            db.execute_query(
                "REFRESH MATERIALIZED VIEW mv_estatisticas_territorio;",
                fetch=False,
            )
            return {"status": "ok", "refreshed": ["mv_estatisticas_territorio"]}
        finally:
            db.close()
