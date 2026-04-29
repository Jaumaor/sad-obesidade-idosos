import pandas as pd

from src.backend.repositories.dashboard_repository import DashboardRepository


class DashboardService:
    """Servico de agregacao para alimentar o dashboard."""

    def __init__(self, db_connection, dias_abandono: int):
        self.repo = DashboardRepository(db_connection)
        self.dias_abandono = dias_abandono

    def get_kpis(self):
        kpis = self.repo.get_kpis(self.dias_abandono)
        return {
            "total_pacientes": int(kpis.get("total_pacientes", 0)),
            "pacientes_ativos": int(kpis.get("pacientes_ativos", 0)),
            "pacientes_faltosos": int(kpis.get("pacientes_faltosos", 0)),
            "total_territorios": int(kpis.get("total_territorios", 0)),
        }

    def get_pacientes_dataframe(self, limite: int = 50) -> pd.DataFrame:
        pacientes = self.repo.get_pacientes_lista(limite=limite)
        if not pacientes:
            return pd.DataFrame()

        df = pd.DataFrame(pacientes)
        rename_map = {
            "codigo_anonimo": "Codigo",
            "idade": "Idade",
            "sexo": "Sexo",
            "imc_atual": "IMC",
            "grau_obesidade_atual": "Grau",
            "total_comorbidades": "Comorbidades",
            "dias_sem_visita": "Dias Sem Visita",
            "nivel_risco_atual": "Risco",
            "territorio": "Territorio",
        }
        return df.rename(columns=rename_map)

    def get_grau_distribuicao_dataframe(self) -> pd.DataFrame:
        rows = self.repo.get_grau_distribuicao()
        if not rows:
            return pd.DataFrame(columns=["Grau", "Quantidade"])
        df = pd.DataFrame(rows)
        return df.rename(columns={"grau": "Grau", "quantidade": "Quantidade"})

    def get_risco_distribuicao_dataframe(self) -> pd.DataFrame:
        rows = self.repo.get_risco_distribuicao()
        if not rows:
            return pd.DataFrame(columns=["Risco", "Quantidade"])
        df = pd.DataFrame(rows)
        return df.rename(columns={"risco": "Risco", "quantidade": "Quantidade"})

    def get_territorio_estatisticas_dataframe(self) -> pd.DataFrame:
        rows = self.repo.get_territorio_estatisticas()
        if not rows:
            return pd.DataFrame(
                columns=[
                    "Territorio",
                    "Total Pacientes",
                    "Pacientes Ativos",
                    "Pacientes Faltosos",
                    "Media Score Risco",
                ]
            )

        df = pd.DataFrame(rows)
        return df.rename(
            columns={
                "territorio": "Territorio",
                "total_pacientes": "Total Pacientes",
                "pacientes_ativos": "Pacientes Ativos",
                "pacientes_faltosos": "Pacientes Faltosos",
                "media_score_risco": "Media Score Risco",
            }
        )
