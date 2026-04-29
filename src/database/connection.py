"""
Utilitário de Conexão com PostgreSQL/PostGIS

Este módulo fornece funções para conectar ao banco de dados
e executar queries de forma segura.
"""

import logging
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text

# Adicionar o diretório raiz ao path para importar config
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from config import DatabaseConfig


logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Gerenciador de conexão com o banco de dados"""

    def __init__(self):
        self.conn = None
        self.engine = None

    def connect_psycopg2(self):
        """
        Conexão usando psycopg2 (para queries SQL diretas)

        Returns:
            psycopg2.connection: Objeto de conexão
        """
        try:
            self.conn = psycopg2.connect(
                DatabaseConfig.get_connection_string()
            )
            logger.info("Conexão psycopg2 estabelecida com sucesso")
            return self.conn
        except psycopg2.Error as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def connect_sqlalchemy(self):
        """
        Conexão usando SQLAlchemy (para ORM)

        Returns:
            sqlalchemy.engine.Engine: Engine do SQLAlchemy
        """
        try:
            self.engine = create_engine(
                DatabaseConfig.SQLALCHEMY_DATABASE_URI,
                echo=False  # Mudar para True para debug
            )
            # Testar conexão
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            logger.info("Engine SQLAlchemy criada com sucesso")
            return self.engine
        except Exception as e:
            logger.error(f"Erro ao criar engine SQLAlchemy: {e}")
            raise

    def execute_query(self, query, params=None, fetch=True):
        """
        Executa uma query SQL

        Args:
            query (str): Query SQL
            params (tuple, optional): Parâmetros da query
            fetch (bool): Se True, retorna resultados (SELECT). Se False, apenas executa (INSERT/UPDATE)

        Returns:
            list: Resultados da query (se fetch=True)
        """
        if not self.conn:
            self.connect_psycopg2()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)

                if fetch:
                    results = cursor.fetchall()
                    return results
                else:
                    self.conn.commit()
                    return cursor.rowcount
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Erro ao executar query: {e}")
            raise

    def test_connection(self):
        """
        Testa a conexão com o banco de dados e verifica o PostGIS

        Returns:
            dict: Informações sobre o banco de dados
        """
        if not self.conn:
            self.connect_psycopg2()

        info = {}

        # Versão do PostgreSQL
        result = self.execute_query("SELECT version();")
        info['postgres_version'] = result[0]['version']

        # Versão do PostGIS
        result = self.execute_query("SELECT PostGIS_Version();")
        info['postgis_version'] = result[0]['postgis_version']

        # Contar tabelas
        result = self.execute_query("""
            SELECT COUNT(*) as total 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        info['total_tables'] = result[0]['total']

        return info

    def close(self):
        """Fecha a conexão com o banco de dados"""
        if self.conn:
            self.conn.close()
            logger.info("Conexão psycopg2 fechada")

        if self.engine:
            self.engine.dispose()
            logger.info("Engine SQLAlchemy fechada")


# ===== FUNÇÕES AUXILIARES =====

def get_db_connection():
    """
    Retorna uma nova conexão com o banco de dados
    Usar em contexts managers: with get_db_connection() as conn: ...
    """
    return psycopg2.connect(DatabaseConfig.get_connection_string())


def get_sqlalchemy_engine():
    """Retorna um engine SQLAlchemy"""
    return create_engine(DatabaseConfig.SQLALCHEMY_DATABASE_URI)


# ===== EXEMPLO DE USO =====

if __name__ == "__main__":
    print("=" * 70)
    print("SAD - Teste de Conexão com Banco de Dados")
    print("=" * 70)

    db = DatabaseConnection()

    try:
        # Conectar
        db.connect_psycopg2()

        # Testar conexão
        info = db.test_connection()

        print("\n[OK] CONEXÃO BEM-SUCEDIDA!\n")
        print(f"PostgreSQL: {info['postgres_version']}")
        print(f"PostGIS: {info['postgis_version']}")
        print(f"Total de tabelas: {info['total_tables']}")

        # Exemplo de query
        print("\n--- Exemplo de Query ---")
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """
        tables = db.execute_query(query)

        if tables:
            print("\nTabelas encontradas:")
            for table in tables:
                print(f"  - {table['table_name']}")
        else:
            print(
                "\n[AVISO] Nenhuma tabela encontrada. Execute o schema.sql primeiro:")
            print("     psql -U postgres -d sad_obesidade -f src/database/schema.sql")

    except Exception as e:
        print(f"\n[ERRO] {e}")
        print("\nVerifique:")
        print("  1. PostgreSQL está rodando?")
        print("  2. O banco 'sad_obesidade' foi criado?")
        print("  3. As credenciais no .env estão corretas?")

    finally:
        db.close()

    print("\n" + "=" * 70)
