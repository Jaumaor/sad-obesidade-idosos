"""
Relatório Completo de Métricas, Features e Validação do Modelo
Gera todas as métricas necessárias para documentação do TCC.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
import json
import pickle
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    accuracy_score, precision_score, recall_score, f1_score,
    brier_score_loss, log_loss, matthews_corrcoef,
    precision_recall_curve, average_precision_score
)

import warnings
warnings.filterwarnings('ignore')

data_dir = Path(__file__).parent
models_dir = Path(__file__).resolve().parent.parent / 'src' / 'models'

# ============================================================
# CARREGAR DADOS E MODELO
# ============================================================
X = pd.read_csv(data_dir / 'X_features.csv')
y = pd.read_csv(data_dir / 'y_target.csv').iloc[:, 0]

with open(models_dir / 'risk_model.pkl', 'rb') as f:
    model_pkg = pickle.load(f)

modelo = model_pkg['modelo']

# Reproduzir o split (mesma seed)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

y_pred = modelo.predict(X_test)
y_proba = modelo.predict_proba(X_test)[:, 1]

# ============================================================
print("=" * 70)
print("RELATÓRIO COMPLETO DE MÉTRICAS DO MODELO")
print("Sistema de Apoio à Decisão - Obesidade em Idosos")
print("=" * 70)

# ============================================================
# 1. O QUE O MODELO PREDIZ
# ============================================================
print("""
╔══════════════════════════════════════════════════════════════════════╗
║  1. O QUE O MODELO PREDITIVO FAZ                                  ║
╚══════════════════════════════════════════════════════════════════════╝

O modelo é um CLASSIFICADOR BINÁRIO que prediz o NÍVEL DE RISCO
CLÍNICO de idosos (60+) com obesidade (IMC ≥ 35).

  ENTRADA: Dados clínicos do paciente (33 variáveis)
  SAÍDA:   Probabilidade de ALTO RISCO (0.0 a 1.0)

  Classes:
    0 = Baixo/Moderado risco  → Acompanhamento de rotina
    1 = Alto/Crítico risco    → Intervenção prioritária

O "risco" é um SCORE COMPOSTO baseado em 5 componentes clínicos:
  1. IMC (gravidade da obesidade)           → 0-25 pontos
  2. Comorbidades (diabetes, HAS, etc.)     → 0-30 pontos
  3. Pressão arterial                       → 0-15 pontos
  4. Glicemia                               → 0-15 pontos
  5. Dias sem acompanhamento                → 0-15 pontos
                                       TOTAL: 0-100 pontos

  Paciente com score > 50 = ALTO RISCO (classe 1)
  Paciente com score ≤ 50 = BAIXO/MODERADO (classe 0)

  FINALIDADE CLÍNICA: Priorizar visitas domiciliares e alertas
  para os idosos obesos com maior risco de complicações.
""")

# ============================================================
# 2. DADOS DE TREINAMENTO
# ============================================================
print("=" * 70)
print("2. DADOS DE TREINAMENTO")
print("=" * 70)
print(f"""
  Fonte:           Banco de dados e-SUS/PEC (PostgreSQL real)
  Tabela central:  tb_medicao (1.416.132 medições)
  
  Extração:        895 idosos com IMC ≥ 35 (antes da limpeza)
  Após limpeza:    757 registros válidos (15.4% removidos)
  
  Split:
    Treino: {len(X_train)} amostras (80%)
    Teste:  {len(X_test)} amostras (20%)
  
  Balanceamento do target:
    Classe 0 (Baixo/Moderado): {(y == 0).sum()} ({(y == 0).mean()*100:.1f}%)
    Classe 1 (Alto/Crítico):   {(y == 1).sum()} ({(y == 1).mean()*100:.1f}%)
    → Classes praticamente balanceadas (50/50)
  
  Perfil dos pacientes:
    Sexo: 86.3% feminino, 13.7% masculino
    Idade: mediana 66 anos (60-98)
    IMC: média 39.3 (35.0 - 79.8)
    Hipertensão: 61.7%
    Diabetes: 29.7%
""")

# ============================================================
# 3. FEATURES UTILIZADAS
# ============================================================
print("=" * 70)
print("3. FEATURES UTILIZADAS (33 variáveis)")
print("=" * 70)

# Importância das features
importancias = pd.DataFrame({
    'feature': X.columns,
    'importance': modelo.feature_importances_
}).sort_values('importance', ascending=False)

print("""
  ┌─────────────────────────────────────────────────────────────────┐
  │ GRUPO 1: ANTROPOMÉTRICAS (5 features)                         │
  ├─────────────────────────────────────────────────────────────────┤
  │ imc              │ IMC (peso/altura²)                          │
  │ imc_z            │ IMC padronizado (Z-score)                   │
  │ excesso_peso_kg  │ Peso real - peso ideal (ref: IMC 24.9)     │
  │ excesso_peso_pct │ % acima do peso ideal                      │
  │ grau_obesidade_num│ 1=Grau II, 2=Grau III, 3=Super Obesidade │
  ├─────────────────────────────────────────────────────────────────┤
  │ GRUPO 2: DEMOGRÁFICAS (4 features)                            │
  ├─────────────────────────────────────────────────────────────────┤
  │ idade            │ Idade em anos                               │
  │ idade_z          │ Idade padronizada (Z-score)                 │
  │ sexo_feminino    │ 1=Feminino, 0=Masculino                    │
  │ faixa_etaria_num │ 1=60-65, 2=66-70, ..., 5=80+              │
  ├─────────────────────────────────────────────────────────────────┤
  │ GRUPO 3: CLÍNICAS (7 features)                                │
  ├─────────────────────────────────────────────────────────────────┤
  │ pa_sistolica     │ Pressão arterial sistólica (mmHg)           │
  │ pa_diastolica    │ Pressão arterial diastólica (mmHg)          │
  │ pa_pulso         │ Pressão de pulso (sistólica - diastólica)   │
  │ pa_media         │ Pressão arterial média                      │
  │ pa_categoria_num │ 0=Normal, 1=Elevada, 2=HAS1, 3=HAS2       │
  │ glicemia         │ Glicemia em mg/dL                           │
  │ glicemia_cat_num │ 0=Normal, 1=Pré-diabetes, 2=Diabetes       │
  ├─────────────────────────────────────────────────────────────────┤
  │ GRUPO 4: COMORBIDADES (10 features)                           │
  ├─────────────────────────────────────────────────────────────────┤
  │ total_comorbidades│ Total de diagnósticos CID-10               │
  │ score_comorbidades│ Score ponderado (cardíaca=3, DM=2, etc.)  │
  │ tem_diabetes     │ CID E10-E14                                 │
  │ tem_hipertensao  │ CID I10-I15                                 │
  │ tem_doenca_cardiaca│ CID I20-I50                               │
  │ tem_dislipidemia │ CID E78                                     │
  │ tem_irc          │ CID N18-N19                                 │
  │ tem_depressao    │ CID F32-F33                                 │
  │ tem_artrose      │ CID M15-M19                                 │
  │ n_condicoes_ativas│ Soma de todas as flags acima               │
  │ multimorbidade   │ 1 se ≥3 condições simultâneas              │
  ├─────────────────────────────────────────────────────────────────┤
  │ GRUPO 5: COMPORTAMENTAIS (2 features)                         │
  ├─────────────────────────────────────────────────────────────────┤
  │ dias_sem_visita  │ Dias desde última medição                   │
  │ dias_sem_visita_log│ log(1 + dias) para reduzir assimetria    │
  ├─────────────────────────────────────────────────────────────────┤
  │ GRUPO 6: INTERAÇÕES (4 features)                              │
  ├─────────────────────────────────────────────────────────────────┤
  │ imc_x_idade      │ IMC × Idade / 100                          │
  │ imc_x_comorbidades│ IMC × Score comorbidades                  │
  │ idade_x_comorb   │ Idade × Score comorbidades / 10            │
  │ imc_x_dias       │ IMC × log(dias sem visita)                 │
  └─────────────────────────────────────────────────────────────────┘
""")

print("  RANKING DE IMPORTÂNCIA DAS FEATURES:")
print("  " + "-" * 60)
for i, row in importancias.iterrows():
    bar = "█" * int(row['importance'] * 100)
    print(f"  {row['feature']:30s} {row['importance']:.4f}  {bar}")

# ============================================================
# 4. MÉTRICAS DO MODELO
# ============================================================
print("\n" + "=" * 70)
print("4. MÉTRICAS COMPLETAS DO MODELO")
print("=" * 70)

acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred)
rec = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_proba)
ap = average_precision_score(y_test, y_proba)
brier = brier_score_loss(y_test, y_proba)
ll = log_loss(y_test, y_proba)
mcc = matthews_corrcoef(y_test, y_pred)

# Cross-validation
cv = cross_val_score(modelo, X_train, y_train, cv=5, scoring='roc_auc')

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()
specificity = tn / (tn + fp)
npv = tn / (tn + fn)  # negative predictive value

print(f"""
  Algoritmo: GradientBoosting (100 árvores, max_depth=5, lr=0.1)
  
  ┌──────────────────────────────────────────────────────────────┐
  │ MÉTRICAS PRIMÁRIAS (no conjunto de teste, n={len(X_test)})          │
  ├──────────────────────────────────────────────────────────────┤
  │ Acurácia (Accuracy)        │ {acc:.4f} ({acc*100:.1f}%)            │
  │ Precisão (Precision)       │ {prec:.4f} ({prec*100:.1f}%)            │
  │ Sensibilidade (Recall)     │ {rec:.4f} ({rec*100:.1f}%)            │
  │ Especificidade             │ {specificity:.4f} ({specificity*100:.1f}%)            │
  │ F1-Score                   │ {f1:.4f}                      │
  │ AUC-ROC                    │ {auc:.4f}                      │
  │ AUC-PR (Avg Precision)     │ {ap:.4f}                      │
  │ MCC (Matthews Corr. Coef.) │ {mcc:.4f}                      │
  │ Brier Score                │ {brier:.4f} (quanto menor, melhor)│
  │ Log Loss                   │ {ll:.4f}                      │
  └──────────────────────────────────────────────────────────────┘
  
  ┌──────────────────────────────────────────────────────────────┐
  │ VALIDAÇÃO CRUZADA (5-fold no treino, n={len(X_train)})             │
  ├──────────────────────────────────────────────────────────────┤
  │ AUC-ROC médio              │ {cv.mean():.4f} ± {cv.std():.4f}         │
  │ Fold 1                     │ {cv[0]:.4f}                      │
  │ Fold 2                     │ {cv[1]:.4f}                      │
  │ Fold 3                     │ {cv[2]:.4f}                      │
  │ Fold 4                     │ {cv[3]:.4f}                      │
  │ Fold 5                     │ {cv[4]:.4f}                      │
  └──────────────────────────────────────────────────────────────┘
  
  ┌──────────────────────────────────────────────────────────────┐
  │ MATRIZ DE CONFUSÃO                                          │
  ├──────────────────────────────────────────────────────────────┤
  │                    │ Predito: Baixo │ Predito: Alto          │
  │ Real: Baixo Risco  │     {tn:3d} (VN)    │     {fp:3d} (FP)           │
  │ Real: Alto Risco   │     {fn:3d} (FN)    │     {tp:3d} (VP)           │
  └──────────────────────────────────────────────────────────────┘
  
  VN (Verdadeiro Negativo): {tn} pacientes de baixo risco corretamente identificados
  VP (Verdadeiro Positivo): {tp} pacientes de alto risco corretamente identificados
  FP (Falso Positivo):      {fp} pacientes de baixo risco erroneamente classificados como alto
  FN (Falso Negativo):      {fn} pacientes de alto risco que o modelo NÃO detectou
""")

# ============================================================
# 5. QUAL MÉTRICA IMPORTA MAIS
# ============================================================
print("=" * 70)
print("5. QUAL MÉTRICA É MAIS VÁLIDA PARA ESTE CASO?")
print("=" * 70)
print(f"""
  CONTEXTO CLÍNICO: Triagem de risco em saúde pública.
  
  Neste tipo de sistema, o CUSTO DE UM FALSO NEGATIVO é muito maior
  que o custo de um FALSO POSITIVO:
  
    - Falso Negativo (FN = {fn}): Paciente de ALTO RISCO que o modelo
      classifica como baixo → NÃO recebe atendimento prioritário
      → Risco de complicações graves, internação, óbito
      → CONSEQUÊNCIA GRAVE
    
    - Falso Positivo (FP = {fp}): Paciente de BAIXO RISCO que o modelo
      classifica como alto → Recebe atendimento prioritário desnecessário
      → Apenas gasto de recurso, sem dano ao paciente
      → CONSEQUÊNCIA LEVE
  
  ┌──────────────────────────────────────────────────────────────┐
  │ MÉTRICAS MAIS RELEVANTES (em ordem de importância):        │
  ├──────────────────────────────────────────────────────────────┤
  │                                                              │
  │ 1. SENSIBILIDADE (Recall) = {rec:.4f}                        │
  │    "De todos os pacientes de alto risco, quantos o modelo    │
  │     consegue identificar?"                                   │
  │    → É a métrica MAIS IMPORTANTE em triagem clínica.         │
  │    → Recall de {rec*100:.1f}% significa que de cada 100 pacientes    │
  │      de alto risco, o modelo identifica {rec*100:.0f} corretamente.  │
  │                                                              │
  │ 2. AUC-ROC = {auc:.4f}                                       │
  │    "Qual a capacidade geral do modelo de distinguir alto     │
  │     risco de baixo risco, em todos os limiares possíveis?"   │
  │    → AUC > 0.90 = Excelente poder discriminativo             │
  │    → AUC > 0.95 = Classificação quase perfeita               │
  │    → Nosso AUC de {auc:.4f} indica desempenho muito forte.  │
  │                                                              │
  │ 3. F1-SCORE = {f1:.4f}                                       │
  │    "Equilíbrio entre Precisão e Sensibilidade"               │
  │    → Importante quando queremos minimizar tanto FP quanto FN │
  │                                                              │
  │ 4. ESPECIFICIDADE = {specificity:.4f}                        │
  │    "De todos os pacientes de baixo risco, quantos o modelo   │
  │     corretamente classifica como baixo?"                     │
  │    → Evita sobrecarga do sistema com falsos alertas          │
  │                                                              │
  │ MÉTRICAS MENOS RELEVANTES AQUI:                              │
  │ - Acurácia: enganosa com classes desbalanceadas (não é       │
  │   nosso caso, mas é uma métrica fraca para decisão clínica)  │
  │ - Precisão isolada: penaliza falsos positivos, que são       │
  │   aceitáveis em triagem de saúde                             │
  └──────────────────────────────────────────────────────────────┘
""")

# ============================================================
# 6. COMPARAÇÃO DOS 3 MODELOS
# ============================================================
print("=" * 70)
print("6. COMPARAÇÃO COMPLETA DOS 3 MODELOS TESTADOS")
print("=" * 70)
print("""
  ┌─────────────────────┬────────────┬────────────┬──────────────────┐
  │ Métrica             │ GradBoost  │ RandForest │ LogRegression    │
  ├─────────────────────┼────────────┼────────────┼──────────────────┤
  │ AUC-ROC             │ 0.9920 ★   │ 0.9910     │ 0.9687           │
  │ CV AUC (5-fold)     │ 0.9761     │ 0.9792 ★   │ 0.9634           │
  │ Accuracy            │ 94.1%      │ 96.1% ★    │ 88.2%            │
  │ Tipo                │ Ensemble   │ Ensemble   │ Linear           │
  │ Interpretabilidade  │ Média      │ Média      │ Alta ★           │
  │ Risco de Overfit    │ Baixo      │ Médio      │ Muito Baixo ★    │
  └─────────────────────┴────────────┴────────────┴──────────────────┘
  
  ESCOLHIDO: GradientBoosting
  MOTIVO: Melhor AUC-ROC no teste (0.9920), que é a métrica principal.
  RandomForest teve CV ligeiramente melhor, mas ambos são muito próximos.
""")

# ============================================================
# 7. LIMITAÇÕES E VIESES
# ============================================================
print("=" * 70)
print("7. LIMITAÇÕES E VIESES CONHECIDOS")
print("=" * 70)
print(f"""
  ⚠️  LIMITAÇÕES DO DATASET:
  
  1. TAMANHO DA AMOSTRA: 757 pacientes
     → Suficiente para treino, mas modelo pode não generalizar
       para populações muito diferentes
  
  2. DESBALANCEAMENTO DE SEXO: 86.3% feminino
     → Modelo pode ter viés: performance melhor para mulheres
     → Reflete a realidade do SUS (mulheres procuram mais atendimento)
  
  3. DADOS FALTANTES IMPUTADOS:
     → Glicemia: 74.4% missing (imputado com mediana)
     → Pressão arterial: 19.8% missing (imputado com mediana)
     → A imputação pode mascarar padrões reais
  
  4. TARGET CONSTRUÍDO (não observado):
     → O score de risco foi CALCULADO por fórmula, não observado
     → Não é um desfecho real (ex: internação, óbito)
     → O modelo está "aprendendo a fórmula", não um desfecho clínico
     → Isso explica o AUC muito alto (0.99) — o modelo aprende
       a reproduzir o score composto quase perfeitamente
  
  5. DADOS TEMPORAIS:
     → Todos os pacientes com > 272 dias sem visita
     → Não há dados recentes de acompanhamento
     → O modelo funciona como "foto" de um momento, não temporal
  
  6. VIÉS GEOGRÁFICO:
     → Dados de um único município
     → Não generaliza para outras regiões
""")

# ============================================================
# 8. COMO INSERIR NO TCC
# ============================================================
print("=" * 70)
print("8. SUGESTÃO DE COMO APRESENTAR NO TCC")
print("=" * 70)
print("""
  CAPÍTULO: Resultados e Discussão
  
  Seção 4.1 - Dataset
    - Tabela com perfil epidemiológico (idade, sexo, IMC, comorbidades)
    - Fluxograma de limpeza (895 → 757 registros)
    - Tabela de missing values e estratégia de imputação
  
  Seção 4.2 - Features
    - Tabela descrevendo cada feature, seu grupo e tipo
    - Gráfico de importância das features (barplot horizontal)
    - Discussão sobre por que imc_x_comorbidades é a mais importante
  
  Seção 4.3 - Métricas do Modelo
    - Tabela comparativa dos 3 modelos (AUC, Accuracy, F1, etc.)
    - Curva ROC dos 3 modelos sobrepostas
    - Matriz de confusão do modelo escolhido
    - Discussão: por que Recall > Precision em triagem clínica
  
  Seção 4.4 - Validação
    - Cross-validation 5-fold (mostra estabilidade)
    - Discussão de limitações (target construído, dados faltantes)
  
  Seção 4.5 - Aplicação Prática
    - Regras de negócio derivadas do modelo
    - Exemplo de classificação de um paciente real
    - Impacto na rotina da equipe de saúde
""")

# Salvar tudo em JSON
report = {
    'modelo': 'GradientBoosting',
    'metricas_teste': {
        'accuracy': round(acc, 4),
        'precision': round(prec, 4),
        'recall_sensibilidade': round(rec, 4),
        'especificidade': round(specificity, 4),
        'f1_score': round(f1, 4),
        'auc_roc': round(auc, 4),
        'auc_pr': round(ap, 4),
        'mcc': round(mcc, 4),
        'brier_score': round(brier, 4),
        'log_loss': round(ll, 4),
    },
    'cross_validation': {
        'mean': round(cv.mean(), 4),
        'std': round(cv.std(), 4),
        'folds': [round(v, 4) for v in cv],
    },
    'matriz_confusao': {
        'verdadeiro_negativo': int(tn),
        'falso_positivo': int(fp),
        'falso_negativo': int(fn),
        'verdadeiro_positivo': int(tp),
    },
    'n_amostras_treino': len(X_train),
    'n_amostras_teste': len(X_test),
    'n_features': X.shape[1],
    'features_ranking': importancias.to_dict('records'),
}

with open(data_dir / 'relatorio_metricas_completo.json', 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n💾 Relatório salvo em: {data_dir / 'relatorio_metricas_completo.json'}")
print("\n✅ RELATÓRIO COMPLETO GERADO")
