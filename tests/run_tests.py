"""
SENTINELA - Suite de Testes Técnicos
Valida integridade de dados, consistência do modelo e funcionamento da API.
"""

import sys
import os
import json
import time
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DatabaseConfig
import psycopg2
from psycopg2.extras import RealDictCursor

# Configurações
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5000"
RESULTS = {"passados": 0, "falharam": 0, "detalhes": []}

def log_test(nome, resultado, detalhes=""):
    status = "✅ PASS" if resultado else "❌ FAIL"
    print(f"{status} {nome}")
    if detalhes:
        print(f"    {detalhes}")
    RESULTS["detalhes"].append({"teste": nome, "resultado": resultado, "detalhes": detalhes})
    if resultado:
        RESULTS["passados"] += 1
    else:
        RESULTS["falharam"] += 1

def get_db_connection(dbname="esus"):
    return psycopg2.connect(
        dbname=dbname,
        user=DatabaseConfig.USER,
        password=DatabaseConfig.PASSWORD,
        host=DatabaseConfig.HOST,
        port=DatabaseConfig.PORT
    )

# ─── TESTE 1: Integridade dos Dados ────────────────────────────────────────

def test_integridade_dados():
    """Verifica se dados brutos e processados estão consistentes."""
    print("\n=== TESTE 1: Integridade dos Dados ===")
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verificar se materialized views existem
            with conn.cursor() as cur2:
                cur2.execute("SELECT to_regclass('public.mv_idosos_obesos_atual')")
                mv = cur2.fetchone()[0]
            log_test("Materialized view mv_idosos_obesos_atual existe", mv is not None)
            
            if mv:
                # Contar registros
                cur.execute("SELECT COUNT(*) as total FROM mv_idosos_obesos_atual")
                total = cur.fetchone()["total"]
                log_test(f"Registros na view: {total}", total > 0, f"Encontrados {total} idosos com obesidade grau II+")
                
                # Verificar campos essenciais não nulos
                cur.execute("""
                    SELECT COUNT(*) as nulos 
                    FROM mv_idosos_obesos_atual 
                    WHERE co_seq_cidadao IS NULL OR idade IS NULL OR imc_atual IS NULL
                """)
                nulos = cur.fetchone()["nulos"]
                log_test("Campos essenciais não nulos", nulos == 0, f"{nulos} registros com campos nulos")
                
                # Verificar idade plausível
                cur.execute("SELECT MIN(idade) as min_idade, MAX(idade) as max_idade FROM mv_idosos_obesos_atual")
                idade = cur.fetchone()
                log_test("Idade plausível (60-110)", 60 <= idade["min_idade"] <= idade["max_idade"] <= 110,
                         f"Idade: {idade['min_idade']} - {idade['max_idade']}")
                
                # Verificar IMC plausível
                cur.execute("SELECT MIN(imc_atual) as min_imc, MAX(imc_atual) as max_imc FROM mv_idosos_obesos_atual")
                imc = cur.fetchone()
                log_test("IMC plausível (30-70)", 30 <= imc["min_imc"] <= imc["max_imc"] <= 70,
                         f"IMC: {imc['min_imc']:.1f} - {imc['max_imc']:.1f}")
    finally:
        conn.close()

# ─── TESTE 2: Consistência do Modelo ML ───────────────────────────────────

def test_consistencia_modelo():
    """Verifica scores de risco e consistência do modelo."""
    print("\n=== TESTE 2: Consistência do Modelo ML ===")
    
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verificar se tabela de risco existe
            with conn.cursor() as cur2:
                cur2.execute("SELECT to_regclass('public.risco_estratificado')")
                tabela = cur2.fetchone()[0]
            log_test("Tabela risco_estratificado existe", tabela is not None)
            
            if tabela:
                # Verificar scores na faixa [0,100]
                cur.execute("SELECT MIN(score_risco) as min_score, MAX(score_risco) as max_score FROM risco_estratificado")
                scores = cur.fetchone()
                log_test("Scores em [0,100]", 0 <= scores["min_score"] <= scores["max_score"] <= 100,
                         f"Score: {scores['min_score']:.1f} - {scores['max_score']:.1f}")
                
                # Verificar distribuição de níveis de risco
                cur.execute("""
                    SELECT nivel_risco, COUNT(*) as count 
                    FROM risco_estratificado 
                    GROUP BY nivel_risco 
                    ORDER BY count DESC
                """)
                dist = cur.fetchall()
                log_test("Distribuição de risco não vazia", len(dist) > 0,
                         f"Níveis: {', '.join([f'{d['nivel_risco']}({d['count']})' for d in dist])}")
                
                # Verificar data de cálculo recente
                cur.execute("""
                    SELECT MAX(data_calculo) as ultima 
                    FROM risco_estratificado 
                    WHERE data_calculo IS NOT NULL
                """)
                ultima = cur.fetchone()["ultima"]
                if ultima:
                    if isinstance(ultima, str):
                        ultima = datetime.strptime(ultima, "%Y-%m-%d").date()
                    elif hasattr(ultima, "date"):
                        ultima = ultima.date()
                    dias_atraso = (datetime.now().date() - ultima).days
                    log_test("Cálculo de risco recente (<30 dias)", dias_atraso < 30,
                             f"Último cálculo: {ultima} ({dias_atraso} dias atrás)")
                else:
                    log_test("Cálculo de risco recente", False, "Nenhuma data de cálculo encontrada")
    finally:
        conn.close()

# ─── TESTE 3: API Endpoints ────────────────────────────────────────────────

def test_api_endpoints():
    """Testa endpoints do backend e frontend."""
    print("\n=== TESTE 3: API Endpoints ===")
    
    # Backend
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/kpis", timeout=5)
        data = r.json()
        log_test("Backend: /api/v1/kpis", r.ok, f"Status {r.status_code}")
        if r.ok:
            log_test("KPIs contém campos obrigatórios", 
                    all(k in data for k in ["total_pacientes", "pacientes_ativos", "pacientes_faltosos"]))
    except Exception as e:
        log_test("Backend: /api/v1/kpis", False, str(e))
    
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/pacientes?limite=5", timeout=5)
        data = r.json()
        log_test("Backend: /api/v1/pacientes", r.ok, f"Retornados {len(data)} pacientes")
        if r.ok and data:
            log_test("Paciente tem campos essenciais", 
                    all(k in data[0] for k in ["id", "codigo_anonimo", "idade", "nivel_risco"]))
    except Exception as e:
        log_test("Backend: /api/v1/pacientes", False, str(e))
    
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/mapa/calor", timeout=10)
        data = r.json()
        log_test("Backend: /api/v1/mapa/calor", r.ok, f"{len(data)} pontos de calor")
    except Exception as e:
        log_test("Backend: /api/v1/mapa/calor", False, str(e))
    
    # Frontend (proxy)
    try:
        r = requests.get(f"{FRONTEND_URL}/api/v1/kpis", timeout=5)
        log_test("Frontend proxy: /api/v1/kpis", r.ok, f"Status {r.status_code}")
    except Exception as e:
        log_test("Frontend proxy: /api/v1/kpis", False, str(e))

# ─── TESTE 4: Autenticação e Autorização ───────────────────────────────────

def test_autenticacao():
    """Testa login e proteção de rotas."""
    print("\n=== TESTE 4: Autenticação e Autorização ===")
    
    session = requests.Session()
    
    # Tentar acessar página protegida sem login
    try:
        r = session.get(FRONTEND_URL, allow_redirects=False)
        log_test("Redirecionamento para login sem autenticação", 
                r.status_code == 302 and "login" in r.headers.get("Location", ""))
    except Exception as e:
        log_test("Redirecionamento para login sem autenticação", False, str(e))
    
    # Login com credenciais corretas
    try:
        r = session.post(f"{FRONTEND_URL}/login", 
                        data={"email": "admin@sentinela.local", "senha": "sentinela2025"})
        log_test("Login com credenciais corretas", r.status_code == 302)
    except Exception as e:
        log_test("Login com credenciais corretas", False, str(e))
    
    # Acessar página após login
    try:
        r = session.get(FRONTEND_URL)
        log_test("Acesso ao dashboard após login", r.status_code == 200 and "SENTINELA" in r.text)
    except Exception as e:
        log_test("Acesso ao dashboard após login", False, str(e))
    
    # Tentar login com senha errada
    try:
        r2 = requests.post(f"{FRONTEND_URL}/login", 
                           data={"email": "admin@sentinela.local", "senha": "senha_errada"})
        log_test("Login com senha errada falha", r2.status_code == 200 and "incorretos" in r2.text.lower())
    except Exception as e:
        log_test("Login com senha errada falha", False, str(e))

# ─── TESTE 5: Alertas e Emails ───────────────────────────────────────────────

def test_alertas():
    """Testa geração de alertas e envio de email."""
    print("\n=== TESTE 5: Alertas e Emails ===")
    
    session = requests.Session()
    session.post(f"{FRONTEND_URL}/login", 
                data={"email": "admin@sentinela.local", "senha": "sentinela2025"})
    
    # Gerar alertas
    try:
        r = session.post(f"{FRONTEND_URL}/alertas/gerar")
        data = r.json()
        log_test("Geração de alertas", r.ok, f"Novos: {data.get('novos_alertas', 0)}")
    except Exception as e:
        log_test("Geração de alertas", False, str(e))
    
    # Verificar alertas no banco
    conn = get_db_connection("sentinela_app")
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) as total FROM alertas WHERE lido = FALSE")
            total = cur.fetchone()["total"]
            log_test(f"Alertas não lidos no banco", total >= 0, f"Encontrados {total}")
    except Exception as e:
        log_test("Alertas não lidos no banco", False, str(e))
    finally:
        conn.close()
    
    # Marcar como lido
    try:
        r = session.post(f"{FRONTEND_URL}/alertas/marcar-todos-lidos")
        log_test("Marcar alertas como lidos", r.status_code == 200)
    except Exception as e:
        log_test("Marcar alertas como lidos", False, str(e))

# ─── TESTE 6: Carga Leve ───────────────────────────────────────────────────

def test_carga_leve():
    """Teste de carga leve com requisições simultâneas."""
    print("\n=== TESTE 6: Carga Leve ===")
    
    import threading
    import queue
    
    results = queue.Queue()
    
    def worker():
        try:
            start = time.time()
            r = requests.get(f"{BACKEND_URL}/api/v1/pacientes?limite=10", timeout=5)
            elapsed = time.time() - start
            results.put((r.ok, elapsed))
        except Exception as e:
            results.put((False, str(e)))
    
    # Disparar 10 requisições simultâneas
    threads = []
    for _ in range(10):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    # Analisar resultados
    success = 0
    times = []
    while not results.empty():
        ok, val = results.get()
        if ok:
            success += 1
            times.append(val)
    
    log_test("Taxa de sucesso em carga (10 req)", success >= 8, f"{success}/10 bem-sucedidas")
    if times:
        avg_time = sum(times) / len(times)
        log_test(f"Tempo médio de resposta <2s", avg_time < 2.0, f"{avg_time:.2f}s")

# ─── RELATÓRIO FINAL ───────────────────────────────────────────────────────

def gerar_relatorio():
    """Gera relatório HTML dos testes."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Relatório de Testes - SENTINELA</title>
        <style>
            body {{ font-family: Inter, sans-serif; margin: 40px; background: #f8fafc; }}
            .header {{ background: #2c684a; color: white; padding: 20px; border-radius: 8px; margin-bottom: 24px; }}
            .summary {{ display: flex; gap: 24px; margin-bottom: 32px; }}
            .card {{ background: white; padding: 24px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); flex: 1; }}
            .pass {{ color: #16a34a; font-weight: bold; }}
            .fail {{ color: #dc2626; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
            th {{ background: #f1f5f9; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>SENTINELA - Relatório de Testes Técnicos</h1>
            <p>Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h2>Total de Testes</h2>
                <p style="font-size: 2em; font-weight: bold;">{RESULTS['passados'] + RESULTS['falharam']}</p>
            </div>
            <div class="card">
                <h2>Passaram</h2>
                <p class="pass" style="font-size: 2em; font-weight: bold;">{RESULTS['passados']}</p>
            </div>
            <div class="card">
                <h2>Falharam</h2>
                <p class="fail" style="font-size: 2em; font-weight: bold;">{RESULTS['falharam']}</p>
            </div>
        </div>
        
        <table>
            <thead>
                <tr><th>Teste</th><th>Resultado</th><th>Detalhes</th></tr>
            </thead>
            <tbody>
    """
    
    for item in RESULTS["detalhes"]:
        status = "✅ Pass" if item["resultado"] else "❌ Fail"
        css_class = "pass" if item["resultado"] else "fail"
        html += f"""
                <tr>
                    <td>{item['teste']}</td>
                    <td class="{css_class}">{status}</td>
                    <td>{item['detalhes']}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </body>
    </html>
    """
    
    report_path = Path(__file__).parent / "relatorio_testes.html"
    report_path.write_text(html, encoding="utf-8")
    print(f"\n📄 Relatório salvo em: {report_path}")

# ─── EXECUÇÃO ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Iniciando suite de testes do SENTINELA...")
    print(f"Backend: {BACKEND_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    
    test_integridade_dados()
    test_consistencia_modelo()
    test_api_endpoints()
    test_autenticacao()
    test_alertas()
    test_carga_leve()
    
    print(f"\n=== RESUMO ===")
    print(f"✅ Passaram: {RESULTS['passados']}")
    print(f"❌ Falharam: {RESULTS['falharam']}")
    print(f"📊 Taxa de sucesso: {RESULTS['passados']/(RESULTS['passados']+RESULTS['falharam'])*100:.1f}%")
    
    gerar_relatorio()
    print("\n🏁 Testes concluídos!")
