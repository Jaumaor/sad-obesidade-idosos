"""Atualiza materialized views usadas pelo dashboard."""

import sys
from pathlib import Path

# Permite importar modulos do projeto quando o script e executado diretamente
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.database.connection import DatabaseConnection


def refresh_materialized_views():
    db = DatabaseConnection()
    db.connect_psycopg2()

    try:
        db.execute_query(
            "REFRESH MATERIALIZED VIEW mv_estatisticas_territorio;",
            fetch=False,
        )
        print("[OK] Materialized view atualizada: mv_estatisticas_territorio")
    finally:
        db.close()


if __name__ == "__main__":
    refresh_materialized_views()
