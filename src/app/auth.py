"""
SENTINELA - Módulo de Autenticação
Gerencia usuários, login/logout e sessão via Flask-Login.
Armazena usuários na tabela 'usuarios' do PostgreSQL.
"""

import os
import hashlib
import secrets
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import psycopg2
from psycopg2.extras import RealDictCursor


# ─── Modelo de Usuário ──────────────────────────────────────────────────

class User(UserMixin):
    """Representa um usuário autenticado."""

    def __init__(self, id, nome, email, cargo, ativo=True):
        self.id = id
        self.nome = nome
        self.email = email
        self.cargo = cargo
        self.ativo = ativo

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return self.ativo


# ─── Helpers de Banco ────────────────────────────────────────────────────

def _get_db_conn():
    """Cria conexão com o banco SENTINELA (separado do e-SUS)."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname="sentinela_app",
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def _hash_password(password: str, salt: str = None) -> tuple:
    """Gera hash SHA-256 com salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return hashed, salt


def _verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verifica senha contra hash."""
    check, _ = _hash_password(password, salt)
    return check == hashed


# ─── Criar tabela (idempotente) ──────────────────────────────────────────

def init_auth_tables():
    """Verifica que as tabelas de auth existem no banco sentinela_app."""
    conn = _get_db_conn()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.usuarios')")
            if cur.fetchone()[0] is None:
                raise RuntimeError(
                    "Tabela 'usuarios' não existe no banco sentinela_app. "
                    "Execute: python _setup_sentinela_db.py"
                )
    finally:
        conn.close()


def init_alertas_table():
    """Verifica que a tabela de alertas existe no banco sentinela_app."""
    conn = _get_db_conn()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('public.alertas')")
            if cur.fetchone()[0] is None:
                raise RuntimeError(
                    "Tabela 'alertas' não existe no banco sentinela_app. "
                    "Execute: python _setup_sentinela_db.py"
                )
    finally:
        conn.close()


# ─── Funções de Usuário ──────────────────────────────────────────────────

def get_user_by_id(user_id):
    conn = _get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, nome, email, cargo, ativo FROM usuarios WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if row:
                return User(**row)
    finally:
        conn.close()
    return None


def authenticate(email, password):
    """Tenta autenticar. Retorna User ou None."""
    conn = _get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, nome, email, cargo, ativo, senha_hash, senha_salt FROM usuarios WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()
            if row and _verify_password(password, row["senha_hash"], row["senha_salt"]):
                # Atualizar ultimo_login
                cur.execute("UPDATE usuarios SET ultimo_login = CURRENT_TIMESTAMP WHERE id = %s", (row["id"],))
                conn.commit()
                return User(id=row["id"], nome=row["nome"], email=row["email"],
                            cargo=row["cargo"], ativo=row["ativo"])
    finally:
        conn.close()
    return None


# ─── Funções de Alertas ──────────────────────────────────────────────────

def get_alertas_nao_lidos(limite=20):
    """Retorna alertas não lidos."""
    conn = _get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, paciente_id, codigo_anonimo, tipo, mensagem, urgencia, criado_em
                FROM alertas WHERE lido = FALSE
                ORDER BY
                    CASE urgencia WHEN 'critica' THEN 1 WHEN 'alta' THEN 2 WHEN 'media' THEN 3 ELSE 4 END,
                    criado_em DESC
                LIMIT %s
            """, (limite,))
            return cur.fetchall()
    finally:
        conn.close()


def contar_alertas_nao_lidos():
    conn = _get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM alertas WHERE lido = FALSE")
            return cur.fetchone()[0]
    finally:
        conn.close()


def marcar_alerta_lido(alerta_id):
    conn = _get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE alertas SET lido = TRUE WHERE id = %s", (alerta_id,))
            conn.commit()
    finally:
        conn.close()


def marcar_todos_lidos():
    conn = _get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("UPDATE alertas SET lido = TRUE WHERE lido = FALSE")
            conn.commit()
    finally:
        conn.close()


def gerar_alertas_automaticos(backend_url="http://127.0.0.1:8000"):
    """
    Gera alertas automáticos baseados nos dados de pacientes.
    Chamado periodicamente ou manualmente.
    """
    import requests as req
    conn = _get_db_conn()
    try:
        # Buscar pacientes prioritários
        r = req.get(f"{backend_url}/api/v1/pacientes/buscar", params={"limite": 500}, timeout=15)
        if not r.ok:
            return 0

        pacientes = r.json()
        novos = 0

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            for p in pacientes:
                pid = p.get("id")
                cod = p.get("codigo_anonimo", "")

                # Alerta: Risco Crítico
                if p.get("nivel_risco") == "Critico":
                    cur.execute(
                        "SELECT 1 FROM alertas WHERE paciente_id=%s AND tipo='risco_critico' AND lido=FALSE",
                        (pid,)
                    )
                    if not cur.fetchone():
                        cur.execute("""
                            INSERT INTO alertas (paciente_id, codigo_anonimo, tipo, mensagem, urgencia)
                            VALUES (%s, %s, 'risco_critico', %s, 'critica')
                        """, (pid, cod, f"Paciente {cod[:8]}... com score de risco CRÍTICO ({p.get('score_risco', 0)})."))
                        novos += 1

                # Alerta: Sem visita há mais de 1 ano
                dias = p.get("dias_sem_visita") or 0
                if dias > 365:
                    cur.execute(
                        "SELECT 1 FROM alertas WHERE paciente_id=%s AND tipo='sem_visita' AND lido=FALSE",
                        (pid,)
                    )
                    if not cur.fetchone():
                        cur.execute("""
                            INSERT INTO alertas (paciente_id, codigo_anonimo, tipo, mensagem, urgencia)
                            VALUES (%s, %s, 'sem_visita', %s, 'alta')
                        """, (pid, cod, f"Paciente {cod[:8]}... sem visita domiciliar há {dias} dias."))
                        novos += 1

            conn.commit()
        return novos
    except Exception:
        return 0
    finally:
        conn.close()


# ─── Blueprint de Autenticação ───────────────────────────────────────────

auth_bp = Blueprint("auth", __name__, template_folder="templates")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "")
        user = authenticate(email, senha)
        if user:
            login_user(user, remember=True)
            next_page = request.args.get("next", "/")
            return redirect(next_page)
        else:
            flash("Email ou senha incorretos.", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


# ─── Setup Flask-Login ───────────────────────────────────────────────────

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para acessar o SENTINELA."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))
