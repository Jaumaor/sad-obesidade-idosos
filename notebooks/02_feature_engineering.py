"""
Fase 3: Feature Engineering
Cria variáveis preditivas a partir dos dados brutos
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import json

def criar_features_risco(df):
    """
    Cria features para o modelo de risco de abandono/complicações
    """
    print("🔧 Criando features...")
    
    df_features = df.copy()
    
    # 1. Features Demográficas
    df_features['faixa_etaria'] = pd.cut(
        df_features['idade'],
        bins=[59, 65, 70, 75, 80, 200],
        labels=['60-65', '66-70', '71-75', '76-80', '80+']
    )
    
    # 2. Features Antropométricas
    df_features['grau_obesidade'] = df_features['imc_calculado'].apply(
        lambda x: 'Grau II' if 35 <= x < 40 else 'Grau III' if x >= 40 else 'Desconhecido'
    )
    
    df_features['excesso_peso_kg'] = df_features.apply(
        lambda row: row['nu_peso'] - (24.9 * ((row['nu_altura']/100) ** 2)) 
        if pd.notna(row['nu_altura']) else np.nan,
        axis=1
    )
    
    # 3. Features de Risco Clínico
    
    # Pressão arterial categorizada
    def categorizar_pa(row):
        if pd.isna(row['nu_pressao_arterial_maxima']):
            return 'Desconhecido'
        sistolica = row['nu_pressao_arterial_maxima']
        if sistolica < 120:
            return 'Normal'
        elif sistolica < 140:
            return 'Elevada'
        elif sistolica < 160:
            return 'Hipertensao_1'
        else:
            return 'Hipertensao_2'
    
    df_features['categoria_pa'] = df_features.apply(categorizar_pa, axis=1)
    
    # Glicemia categorizada
    def categorizar_glicemia(glicemia):
        if pd.isna(glicemia):
            return 'Desconhecido'
        if glicemia < 100:
            return 'Normal'
        elif glicemia < 126:
            return 'Pre_diabetes'
        else:
            return 'Diabetes'
    
    df_features['categoria_glicemia'] = df_features['nu_glicemia'].apply(categorizar_glicemia)
    
    # 4. Features Comportamentais (Engajamento)
    
    # Tempo desde última visita
    df_features['dias_sem_visita'] = pd.to_numeric(df_features['dias_desde_visita'], errors='coerce')
    
    # Risco de abandono
    df_features['risco_abandono'] = df_features['dias_sem_visita'].apply(
        lambda x: 'Alto' if pd.notna(x) and x > 90 else 
                  'Medio' if pd.notna(x) and x > 60 else 
                  'Baixo' if pd.notna(x) else 'Desconhecido'
    )
    
    # 5. Features de Comorbidade
    
    # Analisar CIDs para identificar condições específicas
    cids = df_features['cids'].fillna('[]')
    
    def tem_condicao(lista_cids, codigos):
        if pd.isna(lista_cids) or lista_cids == '[]':
            return False
        # Verificar se algum código está na lista
        for codigo in codigos:
            if codigo in str(lista_cids):
                return True
        return False
    
    # CIDs comuns em idosos obesos
    df_features['tem_diabetes'] = cids.apply(lambda x: tem_condicao(x, ['E10', 'E11', 'E12', 'E13', 'E14']))
    df_features['tem_hipertensao'] = cids.apply(lambda x: tem_condicao(x, ['I10', 'I11', 'I12', 'I13', 'I14', 'I15']))
    df_features['tem_doenca_cardiaca'] = cids.apply(lambda x: tem_condicao(x, ['I20', 'I21', 'I22', 'I25', 'I50']))
    df_features['tem_dislipidemia'] = cids.apply(lambda x: tem_condicao(x, ['E78']))
    df_features['tem_irc'] = cids.apply(lambda x: tem_condicao(x, ['N18', 'N19']))
    
    # Score de comorbidades ponderado
    pesos = {
        'tem_diabetes': 2,
        'tem_hipertensao': 1,
        'tem_doenca_cardiaca': 3,
        'tem_dislipidemia': 1,
        'tem_irc': 3
    }
    
    df_features['score_comorbidades'] = sum(
        df_features[col] * peso for col, peso in pesos.items()
    )
    
    # 6. Features Geográficas
    # (Aqui poderíamos calcular distância até UBS mais próxima)
    
    return df_features

def preparar_dataset_ml(df_features):
    """
    Prepara dataset final para ML (encoding, normalização)
    """
    print("📊 Preparando dataset para ML...")
    
    # Selecionar features relevantes
    features_numericas = [
        'idade', 'nu_peso', 'nu_altura', 'imc_calculado',
        'excesso_peso_kg', 'nu_glicemia', 'nu_pressao_arterial_maxima',
        'nu_pressao_arterial_minima', 'total_comorbidades',
        'score_comorbidades', 'dias_sem_visita'
    ]
    
    features_categoricas = [
        'faixa_etaria', 'grau_obesidade', 'categoria_pa', 
        'categoria_glicemia', 'risco_abandono'
    ]
    
    features_booleanas = [
        'tem_diabetes', 'tem_hipertensao', 'tem_doenca_cardiaca',
        'tem_dislipidemia', 'tem_irc'
    ]
    
    # Criar dummies para categóricas
    df_dummies = pd.get_dummies(df_features[features_categoricas], drop_first=True)
    
    # Montar dataset final
    X = pd.concat([
        df_features[features_numericas].fillna(0),
        df_dummies,
        df_features[features_booleanas].fillna(False).astype(int)
    ], axis=1)
    
    # Target: Risco de Abandono (exemplo)
    # 1 = Alto risco de abandono (não retornará em 90 dias)
    y = (df_features['dias_sem_visita'] > 90).astype(int)
    
    print(f"Features criadas: {X.shape[1]}")
    print(f"Amostras: {X.shape[0]:,}")
    print(f"\nDistribuição do target:")
    print(y.value_counts(normalize=True))
    
    # Salvar
    X.to_csv('X_features.csv', index=False)
    y.to_csv('y_target.csv', index=False)
    
    # Salvar metadata das features
    metadata = {
        'features_numericas': features_numericas,
        'features_categoricas': list(df_dummies.columns),
        'features_booleanas': features_booleanas,
        'n_features': X.shape[1],
        'n_samples': X.shape[0],
        'target_distribution': y.value_counts().to_dict()
    }
    
    with open('features_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return X, y

if __name__ == "__main__":
    # Carregar amostra
    print("Carregando amostra...")
    df = pd.read_parquet('amostra_idosos_obesidade.parquet')
    
    # Criar features
    df_features = criar_features_risco(df)
    
    # Preparar para ML
    X, y = preparar_dataset_ml(df_features)
    
    print("\n✅ Próximo passo: Executar 03_model_training.py")
