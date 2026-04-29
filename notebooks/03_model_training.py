"""
Fase 4: Treinamento do Modelo de ML
Algoritmos: Random Forest, XGBoost, Logistic Regression
"""

import pandas as pd
import numpy as np
import json
import pickle
from datetime import datetime

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve

import warnings
warnings.filterwarnings('ignore')

def treinar_modelos(X, y):
    """
    Treina e compara múltiplos modelos
    """
    print("🤖 Treinando modelos...")
    print(f"Dataset: {X.shape[0]:,} amostras, {X.shape[1]} features")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Normalização para regressão logística
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Modelos a testar
    modelos = {
        'RandomForest': RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ),
        'GradientBoosting': GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        ),
        'LogisticRegression': LogisticRegression(
            class_weight='balanced',
            max_iter=1000,
            random_state=42
        )
    }
    
    resultados = {}
    melhor_modelo = None
    melhor_auc = 0
    
    for nome, modelo in modelos.items():
        print(f"\n{'='*50}")
        print(f"Treinando: {nome}")
        print('='*50)
        
        # Treinar
        if nome == 'LogisticRegression':
            modelo.fit(X_train_scaled, y_train)
            y_pred = modelo.predict(X_test_scaled)
            y_proba = modelo.predict_proba(X_test_scaled)[:, 1]
        else:
            modelo.fit(X_train, y_train)
            y_pred = modelo.predict(X_test)
            y_proba = modelo.predict_proba(X_test)[:, 1]
        
        # Métricas
        auc = roc_auc_score(y_test, y_proba)
        cv_scores = cross_val_score(modelo, 
                                   X_train_scaled if nome == 'LogisticRegression' else X_train,
                                   y_train, 
                                   cv=5, 
                                   scoring='roc_auc')
        
        print(f"\nAUC-ROC: {auc:.4f}")
        print(f"CV AUC (5-fold): {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
        print(f"\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Baixo Risco', 'Alto Risco']))
        
        resultados[nome] = {
            'auc_roc': auc,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'modelo': modelo,
            'scaler': scaler if nome == 'LogisticRegression' else None
        }
        
        # Guardar melhor
        if auc > melhor_auc:
            melhor_auc = auc
            melhor_modelo = nome
    
    print(f"\n{'='*60}")
    print(f"🏆 MELHOR MODELO: {melhor_modelo} (AUC: {melhor_auc:.4f})")
    print('='*60)
    
    return resultados, melhor_modelo, (X_train, X_test, y_train, y_test)

def analisar_importancia(modelo, feature_names, nome_modelo):
    """
    Extrai importância das features
    """
    if hasattr(modelo, 'feature_importances_'):
        importancias = modelo.feature_importances_
    elif hasattr(modelo, 'coef_'):
        importancias = np.abs(modelo.coef_[0])
    else:
        return None
    
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': importancias
    }).sort_values('importance', ascending=False)
    
    print(f"\n📊 Top 10 Features mais importantes ({nome_modelo}):")
    print(feature_importance.head(10).to_string(index=False))
    
    return feature_importance

def salvar_modelo(resultados, melhor_modelo, feature_names):
    """
    Salva modelo em formato para produção
    """
    print(f"\n💾 Salvando modelo {melhor_modelo}...")
    
    modelo_info = resultados[melhor_modelo]
    modelo = modelo_info['modelo']
    
    # Pacote do modelo
    model_package = {
        'modelo': modelo,
        'scaler': modelo_info['scaler'],
        'feature_names': list(feature_names),
        'algoritmo': melhor_modelo,
        'auc_roc': modelo_info['auc_roc'],
        'data_treinamento': datetime.now().isoformat(),
        'version': '1.0.0'
    }
    
    # Salvar com pickle
    with open('../src/models/risk_model.pkl', 'wb') as f:
        pickle.dump(model_package, f)
    
    # Salvar metadados
    metadata = {
        'algoritmo': melhor_modelo,
        'auc_roc': float(modelo_info['auc_roc']),
        'cv_mean': float(modelo_info['cv_mean']),
        'cv_std': float(modelo_info['cv_std']),
        'n_features': len(feature_names),
        'features': list(feature_names),
        'data_treinamento': datetime.now().isoformat()
    }
    
    with open('../src/models/risk_model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Modelo salvo em: src/models/risk_model.pkl")
    print(f"✅ Metadados salvos em: src/models/risk_model_metadata.json")

def gerar_regras_negocio(feature_importance):
    """
    Gera regras interpretáveis para o SAD
    """
    print("\n📋 Gerando regras de negócio interpretáveis...")
    
    regras = {
        'risco_critico': {
            'condicoes': [
                'dias_sem_visita > 90',
                'imc_calculado >= 40',
                'score_comorbidades >= 5'
            ],
            'acao': 'Visita domiciliar prioritária em 24h'
        },
        'risco_alto': {
            'condicoes': [
                'dias_sem_visita > 60',
                'tem_diabetes == True AND tem_doenca_cardiaca == True'
            ],
            'acao': 'Agendar consulta em 7 dias'
        },
        'risco_moderado': {
            'condicoes': [
                'dias_sem_visita > 45',
                'categoria_pa == "Hipertensao_2"'
            ],
            'acao': 'Telemonitoramento + retorno em 15 dias'
        }
    }
    
    with open('../src/models/regras_risco.json', 'w') as f:
        json.dump(regras, f, indent=2, ensure_ascii=False)
    
    print("✅ Regras salvas em: src/models/regras_risco.json")

if __name__ == "__main__":
    # Carregar dados
    print("Carregando features...")
    X = pd.read_csv('X_features.csv')
    y = pd.read_csv('y_target.csv').iloc[:, 0]
    
    # Treinar
    resultados, melhor_modelo, splits = treinar_modelos(X, y)
    
    # Análise de importância
    modelo_final = resultados[melhor_modelo]['modelo']
    importancias = analisar_importancia(modelo_final, X.columns, melhor_modelo)
    
    # Salvar
    salvar_modelo(resultados, melhor_modelo, X.columns)
    
    # Regras de negócio
    if importancias is not None:
        gerar_regras_negocio(importancias)
    
    print("\n" + "="*60)
    print("✅ TREINAMENTO CONCLUÍDO")
    print("="*60)
    print("\nPróximos passos:")
    print("1. Implementar endpoint de predição na API")
    print("2. Criar job de recalcular risco semanalmente")
    print("3. Integrar com sistema de alertas")
