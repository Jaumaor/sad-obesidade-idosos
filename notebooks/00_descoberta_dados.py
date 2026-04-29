"""
Fase 1: Descoberta e Auditoria do Schema
Executar ANTES de qualquer ML - descobre o que temos no banco
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.database.connection import DatabaseConnection
import pandas as pd
import json
from datetime import datetime

def auditar_schema():
    """
    Descobre tabelas, colunas, volumes e qualidade dos dados
    """
    db = DatabaseConnection()
    
    print("=" * 60)
    print("AUDITORIA DO BANCO DE DADOS e-SUS")
    print("=" * 60)
    
    # 1. Listar todas as tabelas
    print("\nTABELAS DISPONÍVEIS:")
    tabelas = db.execute_query("""
        SELECT table_name, table_schema
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pgagent')
        AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name;
    """)
    
    for t in tabelas:
        print(f"  - {t['table_schema']}.{t['table_name']}")
    
    # 2. Para cada tabela relevante, contar registros
    print("\nVOLUMETRIA:")
    tabelas_relevantes = [
        'tb_cidadao', 'tb_atendimento', 'tb_problema', 'tb_medicamento',
        'tb_exame', 'tb_vacinacao', 'tb_conduta', 'tb_avaliacao_elegibilidade'
    ]
    
    stats = {}
    for tabela in tabelas_relevantes:
        try:
            count = db.execute_query(f"SELECT COUNT(*) as total FROM {tabela}")[0]['total']
            stats[tabela] = count
            print(f"  {tabela}: {count:,} registros")
        except Exception as e:
            print(f"  {tabela}: ERRO - {e}")
    
    # 3. Schema das colunas principais
    print("\nCOLUNAS DA TABELA tb_cidadao (provável tabela de pacientes):")
    try:
        colunas = db.execute_query("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'tb_cidadao'
            ORDER BY ordinal_position;
        """)
        for c in colunas:
            nullable = "NULL" if c['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  - {c['column_name']}: {c['data_type']} ({nullable})")
    except Exception as e:
        print(f"  Erro: {e}")
    
    # 4. Verificar campos de identificador (CPF, CNS, etc)
    print("\nCAMPOS DE IDENTIFICAÇÃO (para anonimização):")
    campos_id = db.execute_query("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE column_name ILIKE '%cpf%' 
           OR column_name ILIKE '%cns%'
           OR column_name ILIKE '%nome%'
           OR column_name ILIKE '%identidade%'
        ORDER BY table_name, column_name;
    """)
    for c in campos_id:
        print(f"  {c['table_name']}.{c['column_name']}")
    
    # 5. Amostra pequena para entender os dados
    print("\nAMOSTRA DE 5 REGISTROS (tb_cidadao):")
    try:
        amostra = db.execute_query("""
            SELECT * FROM tb_cidadao 
            WHERE dt_nascimento IS NOT NULL
            LIMIT 5;
        """)
        print(pd.DataFrame(amostra).to_string())
    except Exception as e:
        print(f"  Erro: {e}")
    
    db.close()
    
    # Salvar relatório
    relatorio = {
        'data_auditoria': datetime.now().isoformat(),
        'tabelas_encontradas': len(tabelas),
        'volumetria': stats
    }
    
    with open('auditoria_schema.json', 'w') as f:
        json.dump(relatorio, f, indent=2)
    
    print("\nAuditoria salva em auditoria_schema.json")

if __name__ == "__main__":
    auditar_schema()
