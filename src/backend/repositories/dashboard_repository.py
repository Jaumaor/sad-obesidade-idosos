from pathlib import Path


class DashboardRepository:
    """Repositorio para consultas usadas pelo dashboard."""

    def __init__(self, db_connection):
        self.db = db_connection
        self.sql_dir = Path(__file__).resolve().parent.parent.parent / "database" / "sql" / "queries"

    def _load_query(self, filename: str) -> str:
        query_path = self.sql_dir / filename
        return query_path.read_text(encoding="utf-8")

    def get_kpis(self, dias_abandono: int):
        query = self._load_query("kpis.sql")
        result = self.db.execute_query(query, params={"dias_abandono": dias_abandono})
        return result[0] if result else {}

    def get_pacientes_lista(self, limite: int = 50):
        query = self._load_query("pacientes_lista.sql")
        return self.db.execute_query(query, params={"limite": limite})

    def get_grau_distribuicao(self):
        query = self._load_query("grau_distribuicao.sql")
        return self.db.execute_query(query)

    def get_risco_distribuicao(self):
        query = self._load_query("risco_distribuicao.sql")
        return self.db.execute_query(query)

    def get_territorio_estatisticas(self):
        query = self._load_query("territorio_estatisticas.sql")
        return self.db.execute_query(query)

    def get_paciente_detalhes(self, paciente_id: str):
        """Retorna detalhes completos de um paciente específico"""
        query = self._load_query("paciente_detalhes.sql")
        result = self.db.execute_query(query, params={"paciente_id": paciente_id})
        return result[0] if result else None

    def get_paciente_acompanhamentos(self, paciente_id: str, limite: int = 50):
        """Retorna histórico de acompanhamentos (visitas/consultas) de um paciente"""
        query = self._load_query("paciente_acompanhamentos.sql")
        return self.db.execute_query(query, params={"paciente_id": paciente_id, "limite": limite})

    def get_paciente_comorbidades(self, paciente_id: str):
        """Retorna comorbidades (condições crônicas) de um paciente"""
        query = self._load_query("paciente_comorbidades.sql")
        return self.db.execute_query(query, params={"paciente_id": paciente_id})

    def get_paciente_alertas(self, paciente_id: str, limite: int = 50):
        """Retorna alertas gerados para um paciente"""
        query = self._load_query("paciente_alertas.sql")
        return self.db.execute_query(query, params={"paciente_id": paciente_id, "limite": limite})

    def buscar_pacientes(self, territorio_ids=None, unidade_saude_ids=None, 
                        idade_minima=None, idade_maxima=None, em_acompanhamento=None, limite=100):
        """Busca pacientes com filtros avançados"""
        query = self._load_query("pacientes_busca.sql")
        return self.db.execute_query(
            query,
            params={
                "territorio_ids": territorio_ids,
                "unidade_saude_ids": unidade_saude_ids,
                "idade_minima": idade_minima,
                "idade_maxima": idade_maxima,
                "em_acompanhamento": em_acompanhamento,
                "limite": limite
            }
        )
