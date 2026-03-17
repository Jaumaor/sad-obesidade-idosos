# Notebook Template: Análise Exploratória de Dados (EDA)

Este template auxilia na análise inicial dos dados do e-SUS.

## Como usar

1. Acesse o Jupyter Notebook:
   ```bash
   jupyter notebook
   ```

2. Crie um novo notebook na pasta `notebooks/` com o nome `01_eda.ipynb`

3. Cole o código abaixo em células separadas:

---

## Célula 1: Importações

```python
# Importações básicas
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

# Configurações
warnings.filterwarnings('ignore')
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 6)
plt.rcParams['font.size'] = 10

print("✅ Bibliotecas importadas com sucesso!")
```

---

## Célula 2: Carregar Dados

```python
# Carregar dados brutos do e-SUS
df = pd.read_csv('../data/raw/pacientes_esus.csv')

print(f"📊 Total de registros: {len(df):,}")
print(f"📋 Total de colunas: {len(df.columns)}")
print("\nPrimeiras linhas:")
df.head()
```

---

## Célula 3: Informações Gerais

```python
# Informações sobre os dados
print("=" * 60)
print("INFORMAÇÕES GERAIS DO DATASET")
print("=" * 60)

df.info()

print("\n" + "=" * 60)
print("ESTATÍSTICAS DESCRITIVAS")
print("=" * 60)

df.describe()
```

---

## Célula 4: Valores Ausentes

```python
# Análise de valores faltantes
missing = df.isnull().sum()
missing_percent = (missing / len(df)) * 100

missing_df = pd.DataFrame({
    'Coluna': missing.index,
    'Valores Ausentes': missing.values,
    'Percentual (%)': missing_percent.values
})

missing_df = missing_df[missing_df['Valores Ausentes'] > 0].sort_values(
    'Valores Ausentes', ascending=False
)

if len(missing_df) > 0:
    print("⚠️ Colunas com valores ausentes:\n")
    print(missing_df.to_string(index=False))
    
    # Visualização
    plt.figure(figsize=(10, 6))
    plt.barh(missing_df['Coluna'], missing_df['Percentual (%)'])
    plt.xlabel('Percentual de Valores Ausentes (%)')
    plt.title('Análise de Dados Faltantes')
    plt.tight_layout()
    plt.show()
else:
    print("✅ Nenhum valor ausente encontrado!")
```

---

## Célula 5: Filtrar Idosos com Obesidade Grau II/III

```python
# Supondo que os dados contenham as colunas: idade, peso, altura

# Calcular IMC (se não existir)
if 'imc' not in df.columns:
    df['imc'] = df['peso_kg'] / (df['altura_m'] ** 2)

# Filtrar idosos (≥ 60 anos)
df_idosos = df[df['idade'] >= 60].copy()

# Filtrar obesidade Grau II (IMC ≥ 35) e Grau III (IMC ≥ 40)
df_obesidade = df_idosos[df_idosos['imc'] >= 35].copy()

# Classificar grau de obesidade
df_obesidade['grau_obesidade'] = df_obesidade['imc'].apply(
    lambda x: 'Grau III' if x >= 40 else 'Grau II'
)

print(f"👴 Total de idosos: {len(df_idosos):,}")
print(f"⚠️  Idosos com obesidade Grau II/III: {len(df_obesidade):,}")
print(f"📊 Percentual: {(len(df_obesidade)/len(df_idosos)*100):.2f}%")

# Distribuição por grau
print("\n🔍 Distribuição por grau de obesidade:")
print(df_obesidade['grau_obesidade'].value_counts())
```

---

## Célula 6: Análise de Idade

```python
# Estatísticas de idade
print("=" * 60)
print("ANÁLISE DE IDADE")
print("=" * 60)
print(df_obesidade['idade'].describe())

# Visualização
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histograma
axes[0].hist(df_obesidade['idade'], bins=15, edgecolor='black', alpha=0.7)
axes[0].set_xlabel('Idade')
axes[0].set_ylabel('Frequência')
axes[0].set_title('Distribuição de Idade - Idosos com Obesidade')
axes[0].grid(axis='y', alpha=0.3)

# Boxplot por grau de obesidade
df_obesidade.boxplot(column='idade', by='grau_obesidade', ax=axes[1])
axes[1].set_xlabel('Grau de Obesidade')
axes[1].set_ylabel('Idade')
axes[1].set_title('Idade por Grau de Obesidade')
plt.suptitle('')  # Remover título automático

plt.tight_layout()
plt.show()
```

---

## Célula 7: Análise de IMC

```python
# Análise do IMC
print("=" * 60)
print("ANÁLISE DO IMC")
print("=" * 60)
print(df_obesidade['imc'].describe())

# Visualização
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histograma
axes[0].hist(df_obesidade['imc'], bins=20, edgecolor='black', alpha=0.7, color='coral')
axes[0].axvline(35, color='orange', linestyle='--', label='Grau II (IMC=35)')
axes[0].axvline(40, color='red', linestyle='--', label='Grau III (IMC=40)')
axes[0].set_xlabel('IMC')
axes[0].set_ylabel('Frequência')
axes[0].set_title('Distribuição de IMC')
axes[0].legend()
axes[0].grid(axis='y', alpha=0.3)

# Boxplot por sexo (se disponível)
if 'sexo' in df_obesidade.columns:
    df_obesidade.boxplot(column='imc', by='sexo', ax=axes[1])
    axes[1].set_xlabel('Sexo')
    axes[1].set_ylabel('IMC')
    axes[1].set_title('IMC por Sexo')
    plt.suptitle('')

plt.tight_layout()
plt.show()
```

---

## Célula 8: Análise de Comorbidades

```python
# Supondo que existam colunas: diabetes, hipertensao, etc. (True/False)
comorbidades = ['diabetes', 'hipertensao', 'dislipidemia', 'cardiopatia']

# Verificar quais colunas existem
comorbidades_disponiveis = [c for c in comorbidades if c in df_obesidade.columns]

if comorbidades_disponiveis:
    print("=" * 60)
    print("ANÁLISE DE COMORBIDADES")
    print("=" * 60)
    
    # Contar comorbidades
    for comorbidade in comorbidades_disponiveis:
        total = df_obesidade[comorbidade].sum()
        percentual = (total / len(df_obesidade)) * 100
        print(f"{comorbidade.capitalize()}: {total} ({percentual:.1f}%)")
    
    # Visualização
    counts = [df_obesidade[c].sum() for c in comorbidades_disponiveis]
    
    plt.figure(figsize=(10, 6))
    plt.bar(comorbidades_disponiveis, counts, color='steelblue', edgecolor='black')
    plt.xlabel('Comorbidade')
    plt.ylabel('Número de Pacientes')
    plt.title('Prevalência de Comorbidades em Idosos com Obesidade Grau II/III')
    plt.xticks(rotation=45)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.show()
else:
    print("⚠️ Colunas de comorbidades não encontradas nos dados")
```

---

## Célula 9: Análise Territorial (se disponível)

```python
# Análise por território/bairro
if 'territorio' in df_obesidade.columns or 'bairro' in df_obesidade.columns:
    col_territorio = 'territorio' if 'territorio' in df_obesidade.columns else 'bairro'
    
    print("=" * 60)
    print(f"ANÁLISE POR {col_territorio.upper()}")
    print("=" * 60)
    
    # Contagem por território
    territorio_counts = df_obesidade[col_territorio].value_counts().head(10)
    print(f"\nTop 10 territórios com mais casos:\n")
    print(territorio_counts)
    
    # Visualização
    plt.figure(figsize=(12, 6))
    territorio_counts.plot(kind='barh', color='teal', edgecolor='black')
    plt.xlabel('Número de Pacientes')
    plt.ylabel('Território')
    plt.title('Distribuição de Pacientes com Obesidade Grau II/III por Território')
    plt.tight_layout()
    plt.show()
else:
    print("⚠️ Coluna de território não encontrada")
```

---

## Célula 10: Salvar Dados Processados

```python
# Salvar dataset limpo e filtrado
output_path = '../data/processed/idosos_obesidade_limpo.csv'
df_obesidade.to_csv(output_path, index=False)

print(f"✅ Dados processados salvos em: {output_path}")
print(f"📊 Total de registros salvos: {len(df_obesidade):,}")
```

---

## Célula 11: Resumo da Análise

```python
print("=" * 70)
print("RESUMO DA ANÁLISE EXPLORATÓRIA")
print("=" * 70)

resumo = f"""
📍 Dataset Original: {len(df):,} registros
👴 Idosos (≥ 60 anos): {len(df_idosos):,} ({len(df_idosos)/len(df)*100:.1f}%)
⚠️  Obesidade Grau II/III: {len(df_obesidade):,} ({len(df_obesidade)/len(df_idosos)*100:.1f}% dos idosos)

📊 IMC Médio: {df_obesidade['imc'].mean():.2f} (DP: {df_obesidade['imc'].std():.2f})
📈 IMC Mínimo: {df_obesidade['imc'].min():.2f}
📈 IMC Máximo: {df_obesidade['imc'].max():.2f}

👥 Idade Média: {df_obesidade['idade'].mean():.1f} anos
"""

print(resumo)

print("=" * 70)
print("✅ Análise exploratória concluída!")
print("=" * 70)
```

---

## Próximos Passos

Após executar todas as células acima, você terá:

1. ✅ Uma visão geral dos dados
2. ✅ Identificação de valores ausentes
3. ✅ Dataset filtrado (apenas idosos com obesidade Grau II/III)
4. ✅ Análises visuais de idade, IMC e comorbidades
5. ✅ Dados processados salvos para a próxima etapa

**Próximo Notebook:** `02_feature_engineering.ipynb` (criação de variáveis para o modelo de ML)
