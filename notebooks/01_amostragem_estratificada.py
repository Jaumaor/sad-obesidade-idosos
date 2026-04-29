"""
Fase 2: Amostragem Estratificada para Análise
Com 100GB+, trabalhamos com amostras representativas
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.database.connection import DatabaseConnection
import pandas as pd
import numpy as np

def extrair_amostra_idosos_obesidade(tamanho_amostra=10000):
    """
    Extrai amostra estratificada de idosos (60+) com potencial obesidade
    sem carregar tudo na memória
    """
    db = DatabaseConnection()
    
    print(f"Extraindo amostra de {tamanho_amostra:,} registros...")
    
    # Query otimizada - traz apenas o que precisamos
    # Usa TABLESAMPLE para amostragem aleatória do PostgreSQL
    query = """
    WITH cidadaos_amostra AS (
        -- Amostra aleatória sistemática + filtro de idade
        SELECT 
            co_seq_cidadao,
            no_cidadao,  -- será anonimizado
            nu_cpf,      -- será anonimizado
            dt_nascimento,
            ST_X(co_local_residencia) as longitude,
            ST_Y(co_local_residencia) as latitude,
            co_bairro,
            st_faleceu
        FROM tb_cidadao
        WHERE dt_nascimento <= CURRENT_DATE - INTERVAL '60 years'  -- Idosos
          AND st_faleceu = 0  -- Não falecidos
          AND co_local_residencia IS NOT NULL  -- Tem coordenadas
        TABLESAMPLE SYSTEM (1)  -- Amostra de 1% dos dados
        LIMIT %s
    ),
    -- Buscar últimas medições antropométricas
    ultimas_medicoes AS (
        SELECT DISTINCT ON (co_seq_cidadao)
            co_seq_cidadao,
            nu_peso,
            nu_altura,
            dt_registro as dt_medicao
        FROM tb_atendimento a
        JOIN tb_avaliacao_elegibilidade ae ON a.co_seq_avaliacao_elegibilidade = ae.co_seq_avaliacao_elegibilidade
        WHERE ae.nu_peso IS NOT NULL 
          AND ae.nu_altura IS NOT NULL
        ORDER BY co_seq_cidadao, dt_registro DESC
    ),
    -- Contar comorbidades
    comorbidades AS (
        SELECT 
            co_seq_cidadao,
            COUNT(*) as total_comorbidades,
            array_agg(co_cid_10 ORDER BY dt_registro DESC) as cids
        FROM tb_problema
        WHERE st_ativo = 1
        GROUP BY co_seq_cidadao
    ),
    -- Últimos exames (glicemia, pressão)
    ultimos_exames AS (
        SELECT DISTINCT ON (e.co_seq_cidadao)
            e.co_seq_cidadao,
            e.nu_glicemia,
            e.nu_pressao_arterial_maxima,
            e.nu_pressao_arterial_minima
        FROM tb_exame e
        WHERE e.dt_registro > CURRENT_DATE - INTERVAL '1 year'
        ORDER BY e.co_seq_cidadao, e.dt_registro DESC
    )
    SELECT 
        c.co_seq_cidadao,
        c.dt_nascimento,
        DATE_PART('year', AGE(CURRENT_DATE, c.dt_nascimento)) as idade,
        c.longitude,
        c.latitude,
        c.co_bairro,
        m.nu_peso,
        m.nu_altura,
        (m.nu_peso / (m.nu_altura/100 * m.nu_altura/100)) as imc_calculado,
        co.total_comorbidades,
        co.cids,
        e.nu_glicemia,
        e.nu_pressao_arterial_maxima,
        e.nu_pressao_arterial_minima,
        m.dt_medicao,
        CURRENT_DATE - m.dt_registro as dias_desde_visita
    FROM cidadaos_amostra c
    LEFT JOIN ultimas_medicoes m ON c.co_seq_cidadao = m.co_seq_cidadao
    LEFT JOIN comorbidades co ON c.co_seq_cidadao = co.co_seq_cidadao
    LEFT JOIN ultimos_exames e ON c.co_seq_cidadao = e.co_seq_cidadao
    WHERE m.nu_peso IS NOT NULL  -- Só com medições válidas
      AND (m.nu_peso / (m.nu_altura/100 * m.nu_altura/100)) >= 35  -- Obesidade II/III
    """
    
    # Executar em chunks para não sobrecarregar memória
    print("Executando query (pode levar alguns minutos)...")
    
    # Para grandes volumes, usar cursor server-side
    resultado = db.execute_query(query, params=(tamanho_amostra,))
    
    df = pd.DataFrame(resultado)
    
    print(f"\n✅ Amostra obtida: {len(df):,} registros")
    print(f"Colunas: {list(df.columns)}")
    print(f"\nDistribuição do IMC:")
    print(df['imc_calculado'].describe())
    
    # Salvar amostra para EDA
    df.to_parquet('amostra_idosos_obesidade.parquet', index=False)
    print("\n💾 Salvo em: amostra_idosos_obesidade.parquet")
    
    db.close()
    return df

def verificar_qualidade_dados(df):
    """
    Relatório de qualidade da amostra
    """
    print("\n" + "=" * 60)
    print("RELATÓRIO DE QUALIDADE DOS DADOS")
    print("=" * 60)
    
    # Missing values
    print("\n📊 VALORES AUSENTES:")
    missing = df.isnull().sum()
    for col in df.columns:
        pct = missing[col] / len(df) * 100
        status = "⚠️" if pct > 20 else "✅"
        print(f"  {status} {col}: {missing[col]:,} ({pct:.1f}%)")
    
    # Outliers
    print("\n📈 OUTLIERS (IQR method):")
    for col in ['nu_peso', 'nu_altura', 'imc_calculado', 'idade']:
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df[col] < Q1 - 1.5*IQR) | (df[col] > Q3 + 1.5*IQR)]
            print(f"  {col}: {len(outliers):,} outliers ({len(outliers)/len(df)*100:.1f}%)")
    
    # Consistência
    print("\n🔍 CHECAGENS DE CONSISTÊNCIA:")
    peso_invalido = df[(df['nu_peso'] < 30) | (df['nu_peso'] > 200)]
    altura_invalida = df[(df['nu_altura'] < 100) | (df['nu_altura'] > 220)]
    imc_invalido = df[(df['imc_calculado'] < 15) | (df['imc_calculado'] > 70)]
    
    print(f"  Pesos inválidos (<30 ou >200kg): {len(peso_invalido):,}")
    print(f"  Alturas inválidas (<100 ou >220cm): {len(altura_invalida):,}")
    print(f"  IMCs inválidos (<15 ou >70): {len(imc_invalido):,}")

if __name__ == "__main__":
    # Extrair amostra
    df = extrair_amostra_idosos_obesidade(tamanho_amostra=50000)  # Começar com 50k
    
    # Analisar qualidade
    verificar_qualidade_dados(df)
    
    print("\n✅ Próximo passo: Executar 02_eda.py para análise exploratória")
