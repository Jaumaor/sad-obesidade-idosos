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
    WITH ultima_medicao AS (
        -- Última medição de cada cidadão idoso (via tb_medicao -> atend_prof -> atend -> prontuario -> cidadao)
        SELECT DISTINCT ON (c.co_seq_cidadao)
            c.co_seq_cidadao,
            c.dt_nascimento,
            c.no_sexo,
            c.no_bairro,
            DATE_PART('year', AGE(CURRENT_DATE, c.dt_nascimento)) as idade,
            CAST(m.nu_medicao_peso AS NUMERIC) as nu_peso,
            CAST(m.nu_medicao_altura AS NUMERIC) as nu_altura,
            CAST(m.nu_medicao_imc AS NUMERIC) as imc_calculado,
            m.nu_medicao_pressao_arterial,
            CAST(m.nu_medicao_glicemia AS NUMERIC) as nu_glicemia,
            m.dt_medicao,
            CURRENT_DATE - m.dt_medicao::date as dias_desde_visita
        FROM tb_medicao m
        JOIN tb_atend_prof ap ON m.co_atend_prof = ap.co_seq_atend_prof
        JOIN tb_atend a ON ap.co_seq_atend_prof = a.co_atend_prof
        JOIN tb_prontuario pr ON a.co_prontuario = pr.co_seq_prontuario
        JOIN tb_cidadao c ON pr.co_cidadao = c.co_seq_cidadao
        WHERE m.nu_medicao_peso IS NOT NULL
          AND m.nu_medicao_altura IS NOT NULL
          AND c.dt_nascimento <= CURRENT_DATE - INTERVAL '60 years'
          AND c.st_faleceu = 0
        ORDER BY c.co_seq_cidadao, m.dt_medicao DESC
    ),
    -- Filtrar apenas obesos (IMC >= 35)
    idosos_obesos AS (
        SELECT * FROM ultima_medicao
        WHERE imc_calculado >= 35
    ),
    -- Contar comorbidades ativas por cidadão (join com tb_cid10 para obter código textual)
    comorbidades AS (
        SELECT
            pr.co_cidadao as co_seq_cidadao,
            COUNT(*) as total_comorbidades,
            array_agg(DISTINCT cid.nu_cid10) as cids
        FROM tb_problema p
        JOIN tb_prontuario pr ON p.co_prontuario = pr.co_seq_prontuario
        LEFT JOIN tb_cid10 cid ON p.co_cid10 = cid.co_cid10
        GROUP BY pr.co_cidadao
    )
    SELECT
        io.co_seq_cidadao,
        io.dt_nascimento,
        io.no_sexo,
        io.no_bairro,
        io.idade,
        io.nu_peso,
        io.nu_altura,
        io.imc_calculado,
        io.nu_medicao_pressao_arterial,
        io.nu_glicemia,
        io.dt_medicao,
        io.dias_desde_visita,
        COALESCE(co.total_comorbidades, 0) as total_comorbidades,
        co.cids
    FROM idosos_obesos io
    LEFT JOIN comorbidades co ON io.co_seq_cidadao = co.co_seq_cidadao
    ORDER BY io.imc_calculado DESC
    LIMIT %s
    """
    
    # Executar em chunks para não sobrecarregar memória
    print("Executando query (pode levar alguns minutos)...")
    
    # Para grandes volumes, usar cursor server-side
    resultado = db.execute_query(query, params=(tamanho_amostra,))
    
    df = pd.DataFrame(resultado)
    
    print(f"\n✅ Amostra obtida: {len(df):,} registros")
    print(f"Colunas: {list(df.columns)}")
    
    if len(df) == 0:
        print("⚠️ Nenhum registro encontrado!")
        db.close()
        return df
    
    # Separar pressão arterial (vem como "146/90")
    pa_split = df['nu_medicao_pressao_arterial'].str.split('/', expand=True)
    df['nu_pressao_arterial_maxima'] = pd.to_numeric(pa_split[0], errors='coerce')
    df['nu_pressao_arterial_minima'] = pd.to_numeric(pa_split[1], errors='coerce') if pa_split.shape[1] > 1 else np.nan
    df.drop(columns=['nu_medicao_pressao_arterial'], inplace=True)
    
    # Converter tipos numéricos
    for col in ['nu_peso', 'nu_altura', 'imc_calculado', 'nu_glicemia']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
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
