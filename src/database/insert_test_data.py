"""
Script para Inserir Dados de Teste no Banco de Dados

IMPORTANTE: Este script insere dados FICTÍCIOS apenas para testar o sistema.
Os dados reais devem vir do e-SUS após anonimização adequada.
"""

from src.database.connection import DatabaseConnection
import sys
from pathlib import Path
from datetime import date, timedelta
import random
import hashlib

# Adicionar caminho para importar módulos
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))


def gerar_codigo_anonimo(id_paciente):
    """Gera um código hash para simular anonimização"""
    return hashlib.sha256(f"paciente_{id_paciente}".encode()).hexdigest()[:16]


def inserir_territorios(db):
    """Insere territórios/bairros de Vitória da Conquista"""
    print("\n[Territórios] Inserindo territórios...")

    territorios = [
        ("Centro", 2933307, 15000, 2.5),
        ("Candeias", 2933307, 12000, 3.2),
        ("Brasil", 2933307, 18000, 4.1),
        ("Recreio", 2933307, 10000, 2.8),
        ("Ibirapuera", 2933307, 9000, 2.1),
    ]

    for nome, codigo_ibge, populacao, area in territorios:
        try:
            db.execute_query("""
                INSERT INTO territorios (nome, codigo_ibge, populacao_estimada, area_km2)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (nome) DO NOTHING
            """, (nome, codigo_ibge, populacao, area), fetch=False)
            print(f"  [OK] {nome}")
        except Exception as e:
            print(f"  [ERRO] Erro ao inserir {nome}: {e}")

    print("[OK] Territórios inseridos com sucesso!")


def inserir_unidades_saude(db):
    """Insere unidades de saúde"""
    print("\n[Unidades] Inserindo unidades de saúde...")

    # Primeiro, obter os IDs dos territórios
    territorios = db.execute_query("SELECT id, nome FROM territorios")
    territorio_map = {t['nome']: t['id'] for t in territorios}

    unidades = [
        ("1234567", "USF Centro", "Rua Principal, 100", "Centro", -40.8350, -14.8550),
        ("1234568", "USF Candeias", "Av. Candeias, 250",
         "Candeias", -40.8400, -14.8600),
        ("1234569", "USF Brasil", "Rua Brasil, 350", "Brasil", -40.8300, -14.8500),
    ]

    for cnes, nome, endereco, territorio_nome, lng, lat in unidades:
        territorio_id = territorio_map.get(territorio_nome)

        if territorio_id:
            try:
                db.execute_query("""
                    INSERT INTO unidades_saude 
                    (cnes, nome, endereco, territorio_id, localizacao)
                    VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                    ON CONFLICT (cnes) DO NOTHING
                """, (cnes, nome, endereco, territorio_id, lng, lat), fetch=False)
                print(f"  [OK] {nome}")
            except Exception as e:
                print(f"  [ERRO] Erro ao inserir {nome}: {e}")

    print("[OK] Unidades de saúde inseridas com sucesso!")


def inserir_pacientes_teste(db, quantidade=30):
    """Insere pacientes fictícios para teste"""
    print(f"\n[Pacientes] Inserindo {quantidade} pacientes de teste...")

    # Obter territórios e unidades
    territorios = db.execute_query("SELECT id FROM territorios")
    unidades = db.execute_query("SELECT id FROM unidades_saude")

    if not territorios or not unidades:
        print("[ERRO] Insira territórios e unidades primeiro!")
        return

    territorio_ids = [t['id'] for t in territorios]
    unidade_ids = [u['id'] for u in unidades]

    pacientes_inseridos = 0

    for i in range(1, quantidade + 1):
        codigo_anonimo = gerar_codigo_anonimo(i)
        idade = random.randint(60, 90)
        sexo = random.choice(['M', 'F'])
        data_nascimento = date.today() - timedelta(days=idade*365)
        territorio_id = random.choice(territorio_ids)
        unidade_id = random.choice(unidade_ids)

        # Coordenada aproximada (área de Vitória da Conquista)
        lng = -40.8400 + random.uniform(-0.05, 0.05)
        lat = -14.8600 + random.uniform(-0.05, 0.05)

        data_cadastro = date.today() - timedelta(days=random.randint(30, 365))
        dias_sem_visita = random.randint(0, 120)
        data_ultima_visita = date.today() - timedelta(days=dias_sem_visita)

        try:
            db.execute_query("""
                INSERT INTO pacientes 
                (codigo_anonimo, idade, sexo, data_nascimento, territorio_id, 
                 unidade_saude_id, localizacao_residencia, data_cadastro, data_ultima_visita)
                VALUES (%s, %s, %s, %s, %s, %s, 
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s)
            """, (codigo_anonimo, idade, sexo, data_nascimento, territorio_id,
                  unidade_id, lng, lat, data_cadastro, data_ultima_visita),
                fetch=False)

            pacientes_inseridos += 1

            if pacientes_inseridos % 10 == 0:
                print(f"  [OK] {pacientes_inseridos} pacientes inseridos...")

        except Exception as e:
            print(f"  [ERRO] Erro ao inserir paciente {i}: {e}")

    print(f"[OK] {pacientes_inseridos} pacientes inseridos com sucesso!")


def inserir_acompanhamentos_teste(db):
    """Insere registros de acompanhamento para os pacientes"""
    print("\n[Acompanhamentos] Inserindo registros de acompanhamento...")

    # Obter IDs dos pacientes
    pacientes = db.execute_query("SELECT id FROM pacientes")

    if not pacientes:
        print("[ERRO] Insira pacientes primeiro!")
        return

    total_acompanhamentos = 0

    for paciente in pacientes:
        paciente_id = paciente['id']

        # Cada paciente terá de 1 a 5 consultas
        num_consultas = random.randint(1, 5)

        for j in range(num_consultas):
            data_registro = date.today() - timedelta(days=random.randint(0, 180))
            peso = random.uniform(90, 140)  # kg
            altura = random.uniform(1.50, 1.80)  # m
            imc = peso / (altura ** 2)

            grau_obesidade = 'Grau III' if imc >= 40 else 'Grau II'

            circunf_abdominal = random.uniform(100, 135)
            pa_sistolica = random.randint(110, 170)
            pa_diastolica = random.randint(70, 110)
            glicemia = random.randint(80, 200)

            tipo_atendimento = random.choice(
                ['Consulta UBS', 'Visita Domiciliar', 'Teleatendimento'])

            try:
                db.execute_query("""
                    INSERT INTO acompanhamentos
                    (paciente_id, data_registro, peso_kg, altura_m, 
                     circunferencia_abdominal_cm, grau_obesidade,
                     pressao_arterial_sistolica, pressao_arterial_diastolica,
                     glicemia_mg_dl, tipo_atendimento)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (paciente_id, data_registro, peso, altura,
                      circunf_abdominal, grau_obesidade,
                      pa_sistolica, pa_diastolica, glicemia, tipo_atendimento),
                    fetch=False)

                total_acompanhamentos += 1

            except Exception as e:
                print(f"  [ERRO] Erro ao inserir acompanhamento: {e}")

    print(f"[OK] {total_acompanhamentos} registros de acompanhamento inseridos!")


def inserir_comorbidades_teste(db):
    """Insere comorbidades aleatórias para os pacientes"""
    print("\n[Comorbidades] Inserindo comorbidades...")

    pacientes = db.execute_query("SELECT id FROM pacientes")

    if not pacientes:
        print("[ERRO] Insira pacientes primeiro!")
        return

    comorbidades_disponiveis = [
        'Diabetes Mellitus Tipo 2',
        'Hipertensão Arterial',
        'Dislipidemia',
        'Doença Cardiovascular',
        'Osteoartrite'
    ]

    total_comorbidades = 0

    for paciente in pacientes:
        paciente_id = paciente['id']

        # Cada paciente terá de 0 a 3 comorbidades
        num_comorbidades = random.randint(0, 3)
        comorbidades_paciente = random.sample(
            comorbidades_disponiveis, num_comorbidades)

        for comorbidade in comorbidades_paciente:
            data_diagnostico = date.today() - timedelta(days=random.randint(180, 1825))
            ativo = random.choice([True, True, False])  # 66% ativo

            try:
                db.execute_query("""
                    INSERT INTO comorbidades
                    (paciente_id, condicao, data_diagnostico, ativo)
                    VALUES (%s, %s, %s, %s)
                """, (paciente_id, comorbidade, data_diagnostico, ativo),
                    fetch=False)

                total_comorbidades += 1

            except Exception as e:
                # Ignorar duplicatas (constraint UNIQUE)
                pass

    print(f"[OK] {total_comorbidades} comorbidades inseridas!")


def inserir_riscos_teste(db):
    """Insere scores de risco fictícios"""
    print("\n[Riscos] Inserindo scores de risco...")

    pacientes = db.execute_query("SELECT id FROM pacientes")

    if not pacientes:
        print("[ERRO] Insira pacientes primeiro!")
        return

    total_riscos = 0

    for paciente in pacientes:
        paciente_id = paciente['id']

        score_risco = random.uniform(0, 100)

        # Classificar nível de risco
        if score_risco < 30:
            nivel_risco = 'Baixo'
        elif score_risco < 60:
            nivel_risco = 'Moderado'
        elif score_risco < 80:
            nivel_risco = 'Alto'
        else:
            nivel_risco = 'Crítico'

        fatores = {
            "imc": random.uniform(35, 50),
            "dias_sem_visita": random.randint(0, 120),
            "comorbidades": random.randint(0, 3)
        }

        try:
            db.execute_query("""
                INSERT INTO risco_estratificado
                (paciente_id, score_risco, nivel_risco, fatores_risco, versao_modelo)
                VALUES (%s, %s, %s, %s::jsonb, %s)
            """, (paciente_id, score_risco, nivel_risco, str(fatores).replace("'", '"'), "1.0.0"),
                fetch=False)

            total_riscos += 1

        except Exception as e:
            print(f"  [ERRO] Erro: {e}")

    print(f"[OK] {total_riscos} scores de risco inseridos!")


def main():
    """Função principal"""
    print("=" * 70)
    print("SAD - Inserção de Dados de Teste")
    print("=" * 70)
    print("\nATENÇÃO: Este script insere dados FICTÍCIOS apenas para teste!")
    print("Os dados reais devem vir do e-SUS após anonimização.\n")

    resposta = input("Deseja continuar? (s/n): ")

    if resposta.lower() != 's':
        print("[CANCELADO] Operação cancelada.")
        return

    try:
        # Conectar ao banco
        db = DatabaseConnection()
        db.connect_psycopg2()

        # Inserir dados em ordem
        inserir_territorios(db)
        inserir_unidades_saude(db)
        inserir_pacientes_teste(db, quantidade=30)
        inserir_acompanhamentos_teste(db)
        inserir_comorbidades_teste(db)
        inserir_riscos_teste(db)

        print("\n" + "=" * 70)
        print("[SUCESSO] TODOS OS DADOS DE TESTE FORAM INSERIDOS COM SUCESSO!")
        print("=" * 70)

        # Exibir estatísticas
        stats = db.execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM territorios) as territorios,
                (SELECT COUNT(*) FROM unidades_saude) as unidades,
                (SELECT COUNT(*) FROM pacientes) as pacientes,
                (SELECT COUNT(*) FROM acompanhamentos) as acompanhamentos,
                (SELECT COUNT(*) FROM comorbidades) as comorbidades,
                (SELECT COUNT(*) FROM risco_estratificado) as riscos
        """)

        if stats:
            st = stats[0]
            print(f"\nEstatísticas do Banco:")
            print(f"  - Territórios: {st['territorios']}")
            print(f"  - Unidades de Saúde: {st['unidades']}")
            print(f"  - Pacientes: {st['pacientes']}")
            print(f"  - Acompanhamentos: {st['acompanhamentos']}")
            print(f"  - Comorbidades: {st['comorbidades']}")
            print(f"  - Scores de Risco: {st['riscos']}")

        print("\nAgora você pode executar o dashboard:")
        print("   streamlit run src/app/app.py")

    except Exception as e:
        print(f"\n[ERRO] {e}")
        print("\nVerifique:")
        print("  1. PostgreSQL está rodando?")
        print("  2. O schema foi executado? (src/database/schema.sql)")
        print("  3. O arquivo .env está configurado corretamente?")

    finally:
        if db:
            db.close()

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
