"""
Fase 3: Feature Engineering
Usa dados_limpos.parquet (já auditado) para criar features numéricas para ML.

Features criadas:
  - Antropométricas: IMC normalizado, excesso de peso
  - Clínicas: PA, glicemia, comorbidades
  - Comportamentais: dias sem visita (log), risco abandono
  - Interações: IMC × comorbidades, idade × IMC
  - Target: score de risco composto (regressão) ou nível de risco (classificação)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
import json

def criar_features(df):
    """
    Cria features numéricas a partir do dataset limpo
    """
    print("=" * 70)
    print("FEATURE ENGINEERING")
    print("=" * 70)
    
    feat = pd.DataFrame(index=df.index)
    
    # ─── 1. FEATURES ANTROPOMÉTRICAS ────────────────────────────────────
    print("\n[1/6] Features antropométricas...")
    
    feat['imc'] = df['imc_calculado']
    feat['imc_z'] = (df['imc_calculado'] - df['imc_calculado'].mean()) / df['imc_calculado'].std()
    
    # Excesso de peso em kg (referência: IMC 24.9 = peso ideal)
    peso_ideal = 24.9 * ((df['nu_altura'] / 100) ** 2)
    feat['excesso_peso_kg'] = df['nu_peso'] - peso_ideal
    feat['excesso_peso_pct'] = (feat['excesso_peso_kg'] / peso_ideal) * 100
    
    # Grau de obesidade numérico
    feat['grau_obesidade_num'] = df['grau_obesidade'].astype(str).map({
        'Grau II': 1, 'Grau III': 2, 'Super Obesidade': 3
    }).fillna(0).astype(int)
    
    # ─── 2. FEATURES DEMOGRÁFICAS ──────────────────────────────────────
    print("[2/6] Features demográficas...")
    
    feat['idade'] = df['idade']
    feat['idade_z'] = (df['idade'] - df['idade'].mean()) / df['idade'].std()
    feat['sexo_feminino'] = (df['sexo'] == 'F').astype(int)
    
    # Faixa etária ordinal
    feat['faixa_etaria_num'] = df['faixa_etaria'].astype(str).map({
        '60-65': 1, '66-70': 2, '71-75': 3, '76-80': 4, '80+': 5
    }).fillna(0).astype(int)
    
    # ─── 3. FEATURES CLÍNICAS ──────────────────────────────────────────
    print("[3/6] Features clínicas...")
    
    # Pressão arterial
    feat['pa_sistolica'] = df['nu_pressao_arterial_maxima']
    feat['pa_diastolica'] = df['nu_pressao_arterial_minima']
    feat['pa_pulso'] = feat['pa_sistolica'] - feat['pa_diastolica']  # pressão de pulso
    feat['pa_media'] = feat['pa_diastolica'] + (feat['pa_pulso'] / 3)  # pressão arterial média
    
    # Categoria PA numérica
    feat['pa_categoria_num'] = df['categoria_pa'].map({
        'Normal': 0, 'Elevada': 1, 'Hipertensão Estágio 1': 2, 'Hipertensão Estágio 2': 3, 'Sem registro': -1
    }).fillna(-1).astype(int)
    
    # Glicemia
    feat['glicemia'] = df['nu_glicemia']
    feat['glicemia_categoria_num'] = df['categoria_glicemia'].map({
        'Normal': 0, 'Pré-diabetes': 1, 'Diabetes': 2, 'Sem registro': -1
    }).fillna(-1).astype(int)
    
    # ─── 4. FEATURES DE COMORBIDADES ───────────────────────────────────
    print("[4/6] Features de comorbidades...")
    
    feat['total_comorbidades'] = df['total_comorbidades']
    feat['score_comorbidades'] = df['score_comorbidades']
    feat['tem_diabetes'] = df['tem_diabetes'].astype(int)
    feat['tem_hipertensao'] = df['tem_hipertensao'].astype(int)
    feat['tem_doenca_cardiaca'] = df['tem_doenca_cardiaca'].astype(int)
    feat['tem_dislipidemia'] = df['tem_dislipidemia'].astype(int)
    feat['tem_irc'] = df['tem_irc'].astype(int)
    feat['tem_depressao'] = df['tem_depressao'].astype(int)
    feat['tem_artrose'] = df['tem_artrose'].astype(int)
    
    # Multimorbidade (>=3 condições simultâneas)
    comorb_cols = ['tem_diabetes', 'tem_hipertensao', 'tem_doenca_cardiaca',
                   'tem_dislipidemia', 'tem_irc', 'tem_depressao', 'tem_artrose']
    feat['n_condicoes_ativas'] = feat[comorb_cols].sum(axis=1)
    feat['multimorbidade'] = (feat['n_condicoes_ativas'] >= 3).astype(int)
    
    # ─── 5. FEATURES COMPORTAMENTAIS ──────────────────────────────────
    print("[5/6] Features comportamentais...")
    
    feat['dias_sem_visita'] = df['dias_desde_visita']
    feat['dias_sem_visita_log'] = np.log1p(df['dias_desde_visita'])  # log para reduzir skew
    
    # Risco de abandono numérico
    feat['risco_abandono_num'] = df['risco_abandono'].astype(str).map({
        'Regular': 0, 'Atenção': 1, 'Alerta': 2, 'Abandono': 3
    }).fillna(0).astype(int)
    
    # ─── 6. FEATURES DE INTERAÇÃO ─────────────────────────────────────
    print("[6/6] Features de interação...")
    
    feat['imc_x_idade'] = feat['imc'] * feat['idade'] / 100  # normalizado
    feat['imc_x_comorbidades'] = feat['imc'] * feat['score_comorbidades']
    feat['idade_x_comorbidades'] = feat['idade'] * feat['score_comorbidades'] / 10
    feat['imc_x_dias_sem_visita'] = feat['imc'] * feat['dias_sem_visita_log']
    
    print(f"\n  Total de features criadas: {feat.shape[1]}")
    return feat


def criar_target(df):
    """
    Cria variável target: Score de Risco Composto
    
    O score combina múltiplos fatores clínicos e comportamentais
    para determinar o nível de risco do paciente.
    """
    print("\n" + "=" * 70)
    print("CRIAÇÃO DO TARGET")
    print("=" * 70)
    
    # Score composto de risco (0-100)
    score = pd.Series(0.0, index=df.index)
    
    # Componente 1: IMC (0-25 pontos)
    # IMC 35 = 5pts, IMC 40 = 15pts, IMC 50+ = 25pts
    score += np.clip((df['imc_calculado'] - 30) * 2.5, 0, 25)
    
    # Componente 2: Comorbidades (0-30 pontos)
    score += np.clip(df['score_comorbidades'] * 5, 0, 30)
    
    # Componente 3: Pressão arterial (0-15 pontos)
    pa_score = df['categoria_pa'].map({
        'Normal': 0, 'Elevada': 5, 'Hipertensão Estágio 1': 10, 
        'Hipertensão Estágio 2': 15, 'Sem registro': 5  # penalizar falta de dado
    }).fillna(5)
    score += pa_score
    
    # Componente 4: Glicemia (0-15 pontos)
    glic_score = df['categoria_glicemia'].map({
        'Normal': 0, 'Pré-diabetes': 7, 'Diabetes': 15, 'Sem registro': 5
    }).fillna(5)
    score += glic_score
    
    # Componente 5: Dias sem acompanhamento (0-15 pontos)
    score += np.clip(df['dias_desde_visita'] / 60, 0, 15)
    
    # Normalizar para 0-100
    score = np.clip(score, 0, 100)
    
    # Classificar em níveis
    niveis = pd.cut(score, bins=[-1, 30, 50, 70, 100],
                    labels=['Baixo', 'Moderado', 'Alto', 'Crítico'])
    
    print(f"\n  Score de risco (0-100):")
    print(f"    mean: {score.mean():.1f}")
    print(f"    std:  {score.std():.1f}")
    print(f"    min:  {score.min():.1f}")
    print(f"    max:  {score.max():.1f}")
    print(f"\n  Distribuição de níveis:")
    print(niveis.value_counts().sort_index().to_string())
    
    return score, niveis


def preparar_dataset_ml(feat, score, niveis):
    """
    Prepara X e y finais, imputação de missing e normalização
    """
    print("\n" + "=" * 70)
    print("PREPARAÇÃO FINAL DO DATASET")
    print("=" * 70)
    
    X = feat.copy()
    
    # Imputação de missing values com mediana (para PA e glicemia)
    imputer = SimpleImputer(strategy='median')
    cols_com_missing = X.columns[X.isnull().any()].tolist()
    
    if cols_com_missing:
        print(f"\n  Imputando {len(cols_com_missing)} colunas com mediana: {cols_com_missing}")
        X[cols_com_missing] = imputer.fit_transform(X[cols_com_missing])
    
    # Remover features com variância zero
    variancia = X.var()
    zero_var = variancia[variancia == 0].index.tolist()
    if zero_var:
        print(f"  Removendo features com variância zero: {zero_var}")
        X.drop(columns=zero_var, inplace=True)
    
    # Verificar infinitos
    X.replace([np.inf, -np.inf], np.nan, inplace=True)
    X.fillna(0, inplace=True)
    
    # Target para classificação binária (Alto/Crítico vs Baixo/Moderado)
    y_binario = (niveis.isin(['Alto', 'Crítico'])).astype(int)
    
    # Target para regressão
    y_score = score
    
    print(f"\n  Dataset final:")
    print(f"    Amostras: {X.shape[0]:,}")
    print(f"    Features: {X.shape[1]}")
    print(f"    Missing: {X.isnull().sum().sum()}")
    print(f"\n  Target binário (Alto Risco):")
    print(f"    0 (Baixo/Moderado): {(y_binario == 0).sum()} ({(y_binario == 0).mean()*100:.1f}%)")
    print(f"    1 (Alto/Crítico):   {(y_binario == 1).sum()} ({(y_binario == 1).mean()*100:.1f}%)")
    
    # Salvar
    output_dir = Path(__file__).parent
    X.to_csv(output_dir / 'X_features.csv', index=False)
    y_binario.to_csv(output_dir / 'y_target.csv', index=False, header=['alto_risco'])
    y_score.to_csv(output_dir / 'y_score.csv', index=False, header=['score_risco'])
    
    # Metadata
    metadata = {
        'n_features': X.shape[1],
        'n_samples': X.shape[0],
        'features': list(X.columns),
        'cols_imputadas': cols_com_missing,
        'target_distribution': y_binario.value_counts().to_dict(),
        'score_stats': {
            'mean': round(float(score.mean()), 2),
            'std': round(float(score.std()), 2),
        }
    }
    with open(output_dir / 'features_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n  💾 Salvos:")
    print(f"    X_features.csv ({X.shape[1]} features)")
    print(f"    y_target.csv (classificação binária)")
    print(f"    y_score.csv (score contínuo 0-100)")
    print(f"    features_metadata.json")
    
    return X, y_binario, y_score


if __name__ == "__main__":
    # Carregar dados limpos
    print("Carregando dados_limpos.parquet...")
    data_path = Path(__file__).parent / 'dados_limpos.parquet'
    df = pd.read_parquet(data_path)
    print(f"  {len(df):,} registros carregados\n")
    
    # Criar features
    feat = criar_features(df)
    
    # Criar target
    score, niveis = criar_target(df)
    
    # Preparar dataset ML
    X, y_bin, y_score = preparar_dataset_ml(feat, score, niveis)
    
    print("\n✅ Feature Engineering concluído. Próximo: 03_model_training.py")
