"""
Fase 2b: Limpeza, Normalização e Auditoria dos Dados
Garante qualidade dos dados antes do Feature Engineering.

Etapas:
  1. Carregamento e inspeção inicial
  2. Normalização de unidades (altura cm/m, peso)
  3. Recálculo do IMC
  4. Remoção de outliers com critérios clínicos
  5. Tratamento de missing values
  6. Parsing e validação de pressão arterial e glicemia
  7. Validação de comorbidades (CIDs)
  8. Anonimização final
  9. Relatório de auditoria pós-limpeza
  10. Exportação do dataset limpo
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import json
from datetime import datetime

# ============================================================
# 1. CARREGAMENTO
# ============================================================
print("=" * 70)
print("LIMPEZA E NORMALIZAÇÃO DOS DADOS")
print("=" * 70)

df = pd.read_parquet('amostra_idosos_obesidade.parquet')
n_inicial = len(df)
print(f"\nRegistros carregados: {n_inicial:,}")
print(f"Colunas: {list(df.columns)}")
print(f"Tipos:\n{df.dtypes}\n")

log_etapas = []

def log(msg, removidos=0):
    print(msg)
    log_etapas.append({'etapa': msg, 'removidos': removidos, 'restantes': len(df)})

# ============================================================
# 2. NORMALIZAÇÃO DE ALTURA (cm vs metros)
# ============================================================
print("\n" + "=" * 70)
print("ETAPA 2: NORMALIZAÇÃO DE ALTURA")
print("=" * 70)

df['nu_altura'] = pd.to_numeric(df['nu_altura'], errors='coerce')
df['nu_peso'] = pd.to_numeric(df['nu_peso'], errors='coerce')

# Diagnóstico antes da correção
print(f"\nAltura - min: {df['nu_altura'].min()}, max: {df['nu_altura'].max()}, median: {df['nu_altura'].median()}")

# Regra: se altura < 3, está em metros -> converter para cm
mask_metros = df['nu_altura'] < 3
n_metros = mask_metros.sum()
df.loc[mask_metros, 'nu_altura'] = df.loc[mask_metros, 'nu_altura'] * 100
log(f"  Alturas convertidas de metros para cm: {n_metros}")

# Regra: se altura > 250 ou < 100, provavelmente erro de digitação
mask_altura_invalida = (df['nu_altura'] < 100) | (df['nu_altura'] > 250)
n_alt_inv = mask_altura_invalida.sum()
print(f"  Alturas ainda inválidas após correção: {n_alt_inv}")

# Tentar corrigir alturas que parecem estar em mm (ex: 1570 -> 157)
mask_mm = df['nu_altura'] > 250
n_mm = mask_mm.sum()
df.loc[mask_mm, 'nu_altura'] = df.loc[mask_mm, 'nu_altura'] / 10
log(f"  Alturas convertidas de mm para cm: {n_mm}")

# Remover alturas ainda inválidas
mask_final_alt = (df['nu_altura'] < 100) | (df['nu_altura'] > 220)
n_drop_alt = mask_final_alt.sum()
df = df[~mask_final_alt].copy()
log(f"  Removidos por altura inválida (<100 ou >220cm): {n_drop_alt}", n_drop_alt)

print(f"\n  Altura pós-limpeza - min: {df['nu_altura'].min():.1f}, max: {df['nu_altura'].max():.1f}, median: {df['nu_altura'].median():.1f}")

# ============================================================
# 3. NORMALIZAÇÃO DE PESO
# ============================================================
print("\n" + "=" * 70)
print("ETAPA 3: NORMALIZAÇÃO DE PESO")
print("=" * 70)

print(f"\n  Peso - min: {df['nu_peso'].min()}, max: {df['nu_peso'].max()}, median: {df['nu_peso'].median()}")

# Limites clínicos razoáveis para idosos obesos: 40kg a 250kg
mask_peso_inv = (df['nu_peso'] < 40) | (df['nu_peso'] > 250)
n_drop_peso = mask_peso_inv.sum()
df = df[~mask_peso_inv].copy()
log(f"  Removidos por peso inválido (<40 ou >250kg): {n_drop_peso}", n_drop_peso)

print(f"  Peso pós-limpeza - min: {df['nu_peso'].min():.1f}, max: {df['nu_peso'].max():.1f}, median: {df['nu_peso'].median():.1f}")

# ============================================================
# 4. RECÁLCULO DO IMC
# ============================================================
print("\n" + "=" * 70)
print("ETAPA 4: RECÁLCULO DO IMC")
print("=" * 70)

# Recalcular IMC com dados limpos (altura em cm -> converter para m)
df['imc_calculado'] = df['nu_peso'] / ((df['nu_altura'] / 100) ** 2)
df['imc_calculado'] = df['imc_calculado'].round(2)

print(f"\n  IMC recalculado:")
print(f"    min: {df['imc_calculado'].min():.2f}")
print(f"    max: {df['imc_calculado'].max():.2f}")
print(f"    median: {df['imc_calculado'].median():.2f}")
print(f"    mean: {df['imc_calculado'].mean():.2f}")

# Filtrar apenas IMC >= 35 (obesidade grau II/III) e IMC razoável (< 80)
mask_imc = (df['imc_calculado'] < 35) | (df['imc_calculado'] > 80)
n_drop_imc = mask_imc.sum()
df = df[~mask_imc].copy()
log(f"  Removidos por IMC fora da faixa (< 35 ou > 80): {n_drop_imc}", n_drop_imc)

# Classificar grau de obesidade
df['grau_obesidade'] = pd.cut(
    df['imc_calculado'],
    bins=[0, 39.99, 49.99, 80],
    labels=['Grau II', 'Grau III', 'Super Obesidade']
)

print(f"\n  Distribuição do grau de obesidade:")
print(df['grau_obesidade'].value_counts().to_string())

# ============================================================
# 5. VALIDAÇÃO DE IDADE
# ============================================================
print("\n" + "=" * 70)
print("ETAPA 5: VALIDAÇÃO DE IDADE")
print("=" * 70)

df['idade'] = pd.to_numeric(df['idade'], errors='coerce')
print(f"\n  Idade - min: {df['idade'].min()}, max: {df['idade'].max()}, median: {df['idade'].median()}")

# Remover idades impossíveis (< 60 não deveria estar aqui, > 120 é erro)
mask_idade = (df['idade'] < 60) | (df['idade'] > 120)
n_drop_idade = mask_idade.sum()
df = df[~mask_idade].copy()
log(f"  Removidos por idade inválida: {n_drop_idade}", n_drop_idade)

# Faixa etária
df['faixa_etaria'] = pd.cut(
    df['idade'],
    bins=[59, 65, 70, 75, 80, 120],
    labels=['60-65', '66-70', '71-75', '76-80', '80+']
)
print(f"\n  Distribuição por faixa etária:")
print(df['faixa_etaria'].value_counts().sort_index().to_string())

# ============================================================
# 6. PRESSÃO ARTERIAL
# ============================================================
print("\n" + "=" * 70)
print("ETAPA 6: VALIDAÇÃO DE PRESSÃO ARTERIAL")
print("=" * 70)

pa_max = df['nu_pressao_arterial_maxima']
pa_min = df['nu_pressao_arterial_minima']

print(f"\n  Missing PA sistólica: {pa_max.isna().sum()} ({pa_max.isna().mean()*100:.1f}%)")
print(f"  Missing PA diastólica: {pa_min.isna().sum()} ({pa_min.isna().mean()*100:.1f}%)")

# Limites clínicos: sistólica 60-300, diastólica 30-200
mask_pa_inv = (
    (pa_max.notna() & ((pa_max < 60) | (pa_max > 300))) |
    (pa_min.notna() & ((pa_min < 30) | (pa_min > 200))) |
    (pa_max.notna() & pa_min.notna() & (pa_min >= pa_max))  # diastólica >= sistólica é erro
)
n_pa_inv = mask_pa_inv.sum()
df.loc[mask_pa_inv, ['nu_pressao_arterial_maxima', 'nu_pressao_arterial_minima']] = np.nan
log(f"  PA invalidadas (limites clínicos ou diastólica >= sistólica): {n_pa_inv}")

# Categorizar PA (para quem tem dados)
def categorizar_pa(sistolica):
    if pd.isna(sistolica):
        return 'Sem registro'
    if sistolica < 120:
        return 'Normal'
    elif sistolica < 140:
        return 'Elevada'
    elif sistolica < 160:
        return 'Hipertensão Estágio 1'
    else:
        return 'Hipertensão Estágio 2'

df['categoria_pa'] = df['nu_pressao_arterial_maxima'].apply(categorizar_pa)
print(f"\n  Distribuição PA:")
print(df['categoria_pa'].value_counts().to_string())

# ============================================================
# 7. GLICEMIA
# ============================================================
print("\n" + "=" * 70)
print("ETAPA 7: VALIDAÇÃO DE GLICEMIA")
print("=" * 70)

df['nu_glicemia'] = pd.to_numeric(df['nu_glicemia'], errors='coerce')
print(f"\n  Missing glicemia: {df['nu_glicemia'].isna().sum()} ({df['nu_glicemia'].isna().mean()*100:.1f}%)")

# Limites clínicos: 20-600 mg/dL
mask_glic_inv = df['nu_glicemia'].notna() & ((df['nu_glicemia'] < 20) | (df['nu_glicemia'] > 600))
n_glic_inv = mask_glic_inv.sum()
df.loc[mask_glic_inv, 'nu_glicemia'] = np.nan
log(f"  Glicemias invalidadas (fora de 20-600 mg/dL): {n_glic_inv}")

def categorizar_glicemia(glic):
    if pd.isna(glic):
        return 'Sem registro'
    if glic < 100:
        return 'Normal'
    elif glic < 126:
        return 'Pré-diabetes'
    else:
        return 'Diabetes'

df['categoria_glicemia'] = df['nu_glicemia'].apply(categorizar_glicemia)
print(f"\n  Distribuição glicemia:")
print(df['categoria_glicemia'].value_counts().to_string())

# ============================================================
# 8. COMORBIDADES (CIDs)
# ============================================================
print("\n" + "=" * 70)
print("ETAPA 8: PARSING DE COMORBIDADES (CID-10)")
print("=" * 70)

df['total_comorbidades'] = pd.to_numeric(df['total_comorbidades'], errors='coerce').fillna(0).astype(int)

def parse_cids(cids_raw):
    """Converte array de CIDs (numpy array ou lista) para lista Python"""
    if cids_raw is None:
        return []
    try:
        if hasattr(cids_raw, '__iter__') and not isinstance(cids_raw, str):
            return [str(c) for c in cids_raw if c is not None and str(c) != 'nan']
        if isinstance(cids_raw, float) and pd.isna(cids_raw):
            return []
    except (TypeError, ValueError):
        pass
    return []

df['cids_lista'] = df['cids'].apply(parse_cids)

# Mapear CIDs para condições clínicas relevantes
cid_map = {
    'tem_diabetes': ['E10', 'E11', 'E12', 'E13', 'E14'],
    'tem_hipertensao': ['I10', 'I11', 'I12', 'I13', 'I14', 'I15'],
    'tem_doenca_cardiaca': ['I20', 'I21', 'I22', 'I25', 'I50', 'I48', 'I49'],
    'tem_dislipidemia': ['E78'],
    'tem_irc': ['N18', 'N19'],
    'tem_depressao': ['F32', 'F33'],
    'tem_artrose': ['M15', 'M16', 'M17', 'M19'],
}

def tem_condicao(cids_lista, prefixos):
    return any(
        any(str(cid).startswith(p) for p in prefixos)
        for cid in cids_lista
    )

for condicao, prefixos in cid_map.items():
    df[condicao] = df['cids_lista'].apply(lambda x: tem_condicao(x, prefixos))

# Score de comorbidades ponderado
pesos_comorb = {
    'tem_diabetes': 2,
    'tem_hipertensao': 1,
    'tem_doenca_cardiaca': 3,
    'tem_dislipidemia': 1,
    'tem_irc': 3,
    'tem_depressao': 1,
    'tem_artrose': 1,
}
df['score_comorbidades'] = sum(df[col].astype(int) * peso for col, peso in pesos_comorb.items())

print(f"\n  Comorbidades identificadas:")
for cond in cid_map:
    n = df[cond].sum()
    print(f"    {cond}: {n} ({n/len(df)*100:.1f}%)")

print(f"\n  Score comorbidades - mean: {df['score_comorbidades'].mean():.2f}, max: {df['score_comorbidades'].max()}")

# ============================================================
# 9. DIAS SEM VISITA
# ============================================================
print("\n" + "=" * 70)
print("ETAPA 9: DIAS SEM VISITA")
print("=" * 70)

df['dias_desde_visita'] = pd.to_numeric(df['dias_desde_visita'], errors='coerce').fillna(0).astype(int)
print(f"\n  Dias desde última visita:")
print(f"    min: {df['dias_desde_visita'].min()}")
print(f"    max: {df['dias_desde_visita'].max()}")
print(f"    median: {df['dias_desde_visita'].median()}")

df['risco_abandono'] = pd.cut(
    df['dias_desde_visita'],
    bins=[-1, 30, 60, 90, 99999],
    labels=['Regular', 'Atenção', 'Alerta', 'Abandono']
)
print(f"\n  Distribuição risco de abandono:")
print(df['risco_abandono'].value_counts().sort_index().to_string())

# ============================================================
# 10. ANONIMIZAÇÃO
# ============================================================
print("\n" + "=" * 70)
print("ETAPA 10: ANONIMIZAÇÃO E SELEÇÃO FINAL")
print("=" * 70)

# Remover colunas sensíveis e intermediárias
colunas_remover = ['cids', 'cids_lista', 'dt_nascimento', 'no_bairro']
df.drop(columns=[c for c in colunas_remover if c in df.columns], inplace=True)

# Sexo: normalizar
df['no_sexo'] = df['no_sexo'].str.strip().str.upper()
df['sexo'] = df['no_sexo'].map({'MASCULINO': 'M', 'FEMININO': 'F'}).fillna('NI')
df.drop(columns=['no_sexo'], inplace=True)

print(f"\n  Sexo:")
print(df['sexo'].value_counts().to_string())

# ============================================================
# 11. RELATÓRIO FINAL
# ============================================================
print("\n" + "=" * 70)
print("RELATÓRIO FINAL DE AUDITORIA")
print("=" * 70)

n_final = len(df)
print(f"\n  Registros iniciais: {n_inicial:,}")
print(f"  Registros finais:   {n_final:,}")
print(f"  Removidos:          {n_inicial - n_final:,} ({(n_inicial - n_final)/n_inicial*100:.1f}%)")

print(f"\n  Colunas finais ({len(df.columns)}):")
for col in df.columns:
    missing = df[col].isna().sum()
    pct = missing / len(df) * 100
    print(f"    {col}: {df[col].dtype} | missing: {missing} ({pct:.1f}%)")

print(f"\n  Distribuição do IMC final:")
print(df['imc_calculado'].describe().to_string())

# Salvar dataset limpo
output_path = Path(__file__).parent / 'dados_limpos.parquet'
df.to_parquet(output_path, index=False)
print(f"\n💾 Dataset limpo salvo em: {output_path}")

# Salvar relatório de auditoria
relatorio = {
    'data_limpeza': datetime.now().isoformat(),
    'registros_iniciais': n_inicial,
    'registros_finais': n_final,
    'removidos': n_inicial - n_final,
    'pct_removidos': round((n_inicial - n_final) / n_inicial * 100, 2),
    'colunas_finais': list(df.columns),
    'etapas': log_etapas,
    'distribuicao_imc': {
        'mean': round(df['imc_calculado'].mean(), 2),
        'std': round(df['imc_calculado'].std(), 2),
        'min': round(df['imc_calculado'].min(), 2),
        'max': round(df['imc_calculado'].max(), 2),
    },
    'distribuicao_sexo': df['sexo'].value_counts().to_dict(),
    'distribuicao_grau_obesidade': df['grau_obesidade'].value_counts().to_dict(),
}

relatorio_path = Path(__file__).parent / 'relatorio_limpeza.json'
with open(relatorio_path, 'w', encoding='utf-8') as f:
    json.dump(relatorio, f, indent=2, ensure_ascii=False, default=str)

print(f"📋 Relatório salvo em: {relatorio_path}")
print("\n✅ LIMPEZA CONCLUÍDA. Próximo passo: 02_feature_engineering.py")
