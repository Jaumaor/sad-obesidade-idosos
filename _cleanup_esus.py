"""Remove tabelas do SENTINELA que foram criadas por engano no banco do e-SUS."""
import sys
sys.path.insert(0, ".")
from config import DatabaseConfig as D
import psycopg2

conn = psycopg2.connect(
    dbname=D.DATABASE, user=D.USER, password=D.PASSWORD,
    host=D.HOST, port=D.PORT
)
conn.autocommit = True
cur = conn.cursor()
for t in ["alertas", "usuarios"]:
    cur.execute(f"SELECT to_regclass('public.{t}')")
    if cur.fetchone()[0]:
        cur.execute(f"DROP TABLE {t} CASCADE")
        print(f"[OK] Removida tabela '{t}' do banco e-SUS ({D.DATABASE})")
    else:
        print(f"[--] Tabela '{t}' não existe no e-SUS (ok)")
conn.close()
print("Limpeza concluída.")
