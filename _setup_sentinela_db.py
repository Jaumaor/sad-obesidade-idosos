"""Script para criar o banco sentinela_app e suas tabelas."""
import sys
sys.path.insert(0, ".")
from config import DatabaseConfig as D
import psycopg2

def main():
    # 1) Conectar ao postgres para criar o banco
    conn = psycopg2.connect(
        dbname="postgres", user=D.USER, password=D.PASSWORD,
        host=D.HOST, port=D.PORT
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'sentinela_app'")
    if cur.fetchone():
        print("[OK] Banco sentinela_app já existe")
    else:
        cur.execute("CREATE DATABASE sentinela_app")
        print("[OK] Banco sentinela_app criado")
    conn.close()

    # 2) Conectar ao sentinela_app para criar tabelas
    conn = psycopg2.connect(
        dbname="sentinela_app", user=D.USER, password=D.PASSWORD,
        host=D.HOST, port=D.PORT
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Tabela de usuários
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(200) NOT NULL,
            email VARCHAR(200) UNIQUE NOT NULL,
            senha_hash VARCHAR(64) NOT NULL,
            senha_salt VARCHAR(32) NOT NULL,
            cargo VARCHAR(100) DEFAULT 'Profissional de Saúde',
            ativo BOOLEAN DEFAULT TRUE,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultimo_login TIMESTAMP
        )
    """)
    print("[OK] Tabela 'usuarios' criada")

    # Tabela de alertas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alertas (
            id SERIAL PRIMARY KEY,
            paciente_id INTEGER,
            codigo_anonimo VARCHAR(200),
            tipo VARCHAR(50) NOT NULL,
            mensagem TEXT NOT NULL,
            urgencia VARCHAR(20) DEFAULT 'media',
            lido BOOLEAN DEFAULT FALSE,
            email_enviado BOOLEAN DEFAULT FALSE,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alertas_lido ON alertas(lido)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alertas_urgencia ON alertas(urgencia)")
    print("[OK] Tabela 'alertas' criada")

    # Inserir usuário admin padrão
    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        import hashlib, secrets
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256(f"{salt}sentinela2025".encode()).hexdigest()
        cur.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, senha_salt, cargo) VALUES (%s,%s,%s,%s,%s)",
            ("Administrador", "admin@sentinela.local", hashed, salt, "Administrador")
        )
        print("[OK] Usuário admin criado: admin@sentinela.local / sentinela2025")
    else:
        print("[OK] Usuários já existem, pulando seed")

    conn.close()
    print("\n=== Setup SENTINELA concluído! ===")

if __name__ == "__main__":
    main()
