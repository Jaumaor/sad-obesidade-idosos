"""
SENTINELA - Envio de Emails (Gmail SMTP)
Configuração via Flask-Mail para alertas urgentes.
"""

import os
import psycopg2
from flask import current_app
from flask_mail import Mail, Message
from datetime import datetime
import logging

log = logging.getLogger(__name__)

# Inicialização global (será configurada no app.py)
mail = Mail()

def init_mail(app):
    """Inicializa Flask-Mail com variáveis do .env."""
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
    mail.init_app(app)


def enviar_alerta_por_email(alerta, paciente_codigo=None):
    """
    Envia email para alertas urgentes (critica/alta).
    Retorna True se enviado com sucesso.
    """
    try:
        # Só envia se urgência for crítica ou alta
        if alerta.get("urgencia") not in ("critica", "alta"):
            return False

        # Destinatário (pode ser configurado no futuro para múltiplos)
        destinatario = current_app.config.get("MAIL_USERNAME")
        if not destinatario:
            log.warning("MAIL_USERNAME não configurado. Pulando envio de email.")
            return False

        # Montar assunto e corpo
        urg_icon = "🔴" if alerta["urgencia"] == "critica" else "🟠"
        assunto = f"{urg_icon} SENTINELA - Alerta {alerta['urgencia'].title()}: {alerta['tipo'].replace('_', ' ').title()}"

        corpo_html = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Inter, sans-serif; line-height: 1.6; color: #1e293b; }}
              .header {{ background: #2c684a; color: white; padding: 20px; text-align: center; }}
              .content {{ padding: 24px; background: #f8fafc; border-radius: 8px; margin: 20px 0; }}
              .footer {{ font-size: 12px; color: #64748b; text-align: center; padding-top: 20px; }}
              .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; font-weight: bold; }}
              .critica {{ background: #ef4444; }}
              .alta {{ background: #f97316; }}
            </style>
          </head>
          <body>
            <div class="header">
              <h1 style="margin:0; font-size:24px;">SENTINELA</h1>
              <p style="margin:4px 0 0; font-size:14px; opacity:0.9;">Sistema de Apoio à Decisão — Monitoramento de Obesidade em Idosos</p>
            </div>

            <div class="content">
              <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
              <p><strong>Paciente:</strong> {paciente_codigo or alerta.get('codigo_anonimo', 'N/A')}</p>
              <p><strong>Tipo:</strong> {alerta['tipo'].replace('_', ' ').title()}</p>
              <p><strong>Urgência:</strong> <span class="badge {alerta['urgencia']}">{alerta['urgencia'].title()}</span></p>
              <hr style="border:0; border-top:1px solid #e2e8f0; margin:16px 0;">
              <p><strong>Mensagem:</strong></p>
              <p style="background:white; padding:12px; border-left:4px solid #2c684a; border-radius:4px;">
                {alerta['mensagem']}
              </p>
              <hr style="border:0; border-top:1px solid #e2e8f0; margin:16px 0;">
              <p style="font-size:14px; color:#475569;">
                <em>Este é um alerta automático do SENTINELA. Verifique o sistema para mais detalhes.</em>
              </p>
            </div>

            <div class="footer">
              <p>SENTINELA v1.0 • Secretaria Municipal de Saúde • Vitória da Conquista - BA</p>
              <p style="margin-top:4px; font-size:10px;">Este email foi gerado automaticamente. Não responda.</p>
            </div>
          </body>
        </html>
        """

        msg = Message(
            subject=assunto,
            recipients=[destinatario],
            html=corpo_html,
            sender=current_app.config.get("MAIL_DEFAULT_SENDER")
        )

        mail.send(msg)
        log.info(f"Email enviado para {destinatario}: {assunto}")
        return True

    except Exception as e:
        log.error(f"Falha ao enviar email de alerta: {e}")
        return False


def marcar_email_enviado(alerta_id):
    """Marca no banco que o email foi enviado (evita reenvio)."""
    from src.app.auth import _get_db_conn
    conn = _get_db_conn()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE alertas SET email_enviado = TRUE WHERE id = %s",
                (alerta_id,)
            )
    finally:
        conn.close()


def enviar_pendentes(backend_url="http://127.0.0.1:8000"):
    """
    Varre alertas não enviados e envia emails.
    Pode ser chamado periodicamente ou manualmente.
    """
    from src.app.auth import _get_db_conn
    conn = _get_db_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, paciente_id, codigo_anonimo, tipo, mensagem, urgencia "
                "FROM alertas WHERE email_enviado = FALSE AND urgencia IN ('critica', 'alta') "
                "ORDER BY criado_em ASC LIMIT 20"
            )
            pendentes = cur.fetchall()

        if not pendentes:
            return {"enviados": 0, "erros": 0, "mensagem": "Nenhum alerta pendente."}

        enviados = 0
        erros = 0
        for a in pendentes:
            if enviar_alerta_por_email(dict(a), paciente_codigo=a.get("codigo_anonimo")):
                marcar_email_enviado(a["id"])
                enviados += 1
            else:
                erros += 1

        return {
            "enviados": enviados,
            "erros": erros,
            "mensagem": f"Enviados {enviados} emails, {erros} falhas."
        }

    except Exception as e:
        log.error(f"Erro ao enviar emails pendentes: {e}")
        return {"enviados": 0, "erros": 1, "mensagem": str(e)}
    finally:
        conn.close()
