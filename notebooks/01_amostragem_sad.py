"""
Fase 2 Simplificada: Extrair dados das tabelas customizadas do SAD
Usa as tabelas já estruturadas (pacientes, acompanhamentos, comorbidades)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.database.connection import DatabaseConnection
import pandas as pd
import json
from datetime import datetime

def extrair_dados_completos():
    """
    Extrai dados integrados das tabelas do SAD
    """
    db = DatabaseConnection()
    
    print("Extraindo dados integrados do SAD...")
    
    query = """
    WITH ultimo_acomp AS (
        SELECT DISTINCT ON (paciente_id)
            paciente_id,
            peso_kg, altura_m, imc, grau_obesidade,
            pressao_arterial_sistolica, pressao_arterial_diastolica,
            glicemia_mg_dl, data_registro
        FROM acompanhamentos
        ORDER BY paciente_id, data_registro DESC
    ),
    comorb AS (
        SELECT 
            paciente_id,
            COUNT(*) as total_comorbidades,
            jsonb_agg(condicao) as condicoes_ativas
        FROM comorbidades
        WHERE ativo = true
        GROUP BY paciente_id
    )
    SELECT 
        p.id as paciente_id,
        p.codigo_anonimo,
        p.data_nascimento,
        p.idade,
        p.sexo,
        p.data_ultima_visita,
        a.peso_kg, a.altura_m, a.imc, a.grau_obesidade,
        a.pressao_arterial_sistolica, a.pressao_arterial_diastolica,
        a.glicemia_mg_dl,
        a.data_registro as data_ultimo_acompanhamento,
        COALESCE(c.total_comorbidades, 0) as total_comorbidades,
        c.condicoes_ativas
    FROM pacientes p
    LEFT JOIN ultimo_acomp a ON p.id = a.paciente_id
    LEFT JOIN comorb c ON p.id = c.paciente_id
    WHERE p.em_acompanhamento = true
    """
    
    resultado = db.execute_query(query)
    df = pd.DataFrame(resultado)
    
    print(f"\nDataset obtido: {len(df):,} pacientes")
    print(f"\nColunas: {list(df.columns)}")
    print(f"\nDistribuição do IMC:")
    print(df['imc'].describe())
    
    # Calcular dias sem visita
    df['dias_sem_visita'] = (pd.Timestamp.now() - pd.to_datetime(df['data_ultima_visita'])).dt.days
    df['dias_sem_visita'] = df['dias_sem_visita'].fillna(0)
    
    # Extrair condições das comorbidades
    def extrair_condicoes(condicoes_json):
        if condicoes_json is None:
            return []
        try:
            if isinstance(condicoes_json, list):
                return [str(c) for c in condicoes_json]
            return []
        except:
            return []
    
    df['lista_comorbidades'] = df['condicoes_ativas'].apply(extrair_condicoes)
    
    # Flags de comorbidades específicas
    df['tem_diabetes'] = df['lista_comorbidades'].apply(
        lambda x: any('diabetes' in c.lower() for c in x)
    )
    df['tem_hipertensao'] = df['lista_comorbidades'].apply(
        lambda x: any('hipertens' in c.lower() for c in x)
    )
    df['tem_doenca_cardiaca'] = df['lista_comorbidades'].apply(
        lambda x: any('cardio' in c.lower() or 'cardía' in c.lower() for c in x)
    )
    
    print(f"\nDistribuição de comorbidades:")
    print(f"  Diabetes: {df['tem_diabetes'].sum()} ({df['tem_diabetes'].mean()*100:.1f}%)")
    print(f"  Hipertensão: {df['tem_hipertensao'].sum()} ({df['tem_hipertensao'].mean()*100:.1f}%)")
    print(f"  Doença cardíaca: {df['tem_doenca_cardiaca'].sum()} ({df['tem_doenca_cardiaca'].mean()*100:.1f}%)")
    
    # Salvar
    df.to_parquet('dados_sad_completos.parquet', index=False)
    print(f"\n💾 Salvo em: dados_sad_completos.parquet")
    
    db.close()
    return df

if __name__ == "__main__":
    df = extrair_dados_completos()
    print("\nPróximo passo: Executar 02_feature_engineering_sad.py")
