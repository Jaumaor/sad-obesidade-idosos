# 🚀 Guia de Início Rápido - SAD

Este documento contém os passos práticos para configurar seu ambiente e começar a trabalhar no TCC.

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- [ ] **Python 3.10 ou superior** ([Download](https://www.python.org/downloads/))
- [ ] **PostgreSQL 14+** ([Download](https://www.postgresql.org/download/windows/))
- [ ] **Git** ([Download](https://git-scm.com/downloads))
- [ ] **Visual Studio Code** (opcional, mas recomendado)

## 🛠️ Passo 1: Configuração Inicial

### 1.1. Verificar Instalações

Abra o PowerShell e execute:

```powershell
# Verificar Python
python --version  # Deve mostrar 3.10 ou superior

# Verificar PostgreSQL
psql --version

# Verificar Git
git --version
```

### 1.2. Criar Ambiente Virtual Python

No diretório do projeto:

```powershell
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Se der erro de execução de scripts, execute (como Admin):
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Quando ativado, você verá `(venv)` no início da linha do terminal.

### 1.3. Instalar Dependências

```powershell
# Atualizar pip
python -m pip install --upgrade pip

# Instalar todas as bibliotecas
pip install -r requirements.txt
```

⏱️ Isso pode levar alguns minutos (vai baixar pandas, scikit-learn, geopandas, etc.)

## 🗄️ Passo 2: Configurar Banco de Dados

### 2.1. Criar o Banco de Dados

Abra o **SQL Shell (psql)** ou o **pgAdmin 4** e execute:

```sql
-- Criar banco de dados
CREATE DATABASE sad_obesidade;

-- Conectar ao banco
\c sad_obesidade

-- Habilitar PostGIS
CREATE EXTENSION postgis;

-- Verificar versão
SELECT PostGIS_Version();
```

### 2.2. Executar o Schema (Criar Tabelas)

No PowerShell:

```powershell
# Executar script SQL
psql -U postgres -d sad_obesidade -f src/database/schema.sql

# Você será solicitado a inserir a senha do PostgreSQL
```

Se tudo deu certo, você verá mensagens de criação das tabelas.

### 2.3. Configurar Variáveis de Ambiente

```powershell
# Copiar arquivo de exemplo
Copy-Item .env.example .env

# Editar o .env com suas credenciais
notepad .env
```

**Edite o arquivo `.env` e preencha:**

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sad_obesidade
DB_USER=postgres
DB_PASSWORD=SUA_SENHA_AQUI  # ⚠️ Coloque a senha do seu PostgreSQL
```

### 2.4. Testar Conexão

```powershell
# Ativar ambiente virtual (se não estiver ativo)
.\venv\Scripts\Activate.ps1

# Testar conexão
python src/database/connection.py
```

Se aparecer `✅ CONEXÃO BEM-SUCEDIDA!`, está tudo certo!

## 📊 Passo 3: Preparar os Dados

### 3.1. Obter Dados do e-SUS

1. Solicite os dados anonimizados junto à Secretaria de Saúde de Vitória da Conquista
2. Salve os arquivos CSV na pasta `data/raw/`

**Exemplo de estrutura esperada:**

```
data/raw/
├── pacientes_esus.csv
├── atendimentos_esus.csv
└── territorios.geojson (opcional)
```

### 3.2. Criar Notebook de Exploração

```powershell
# Iniciar Jupyter
jupyter notebook
```

Isso abrirá o navegador. Navegue até `notebooks/` e crie um novo notebook chamado `01_eda.ipynb`.

**Código inicial para explorar os dados:**

```python
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns

# Configurações de visualização
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# Carregar dados brutos
df_pacientes = pd.read_csv('../data/raw/pacientes_esus.csv')

# Primeiras linhas
df_pacientes.head()

# Informações básicas
df_pacientes.info()

# Estatísticas descritivas
df_pacientes.describe()

# Distribuição de idade
df_pacientes['idade'].hist(bins=20)
plt.title('Distribuição de Idade dos Pacientes')
plt.xlabel('Idade')
plt.ylabel('Frequência')
plt.show()
```

## 🧪 Passo 4: Primeiro Teste do Sistema

### 4.1. Inserir Dados de Teste

Crie um arquivo `src/database/insert_test_data.py`:

```python
from connection import DatabaseConnection

db = DatabaseConnection()
db.connect_psycopg2()

# Inserir território de teste
db.execute_query("""
    INSERT INTO territorios (nome, populacao_estimada, area_km2)
    VALUES ('Centro', 15000, 2.5)
    ON CONFLICT DO NOTHING
""", fetch=False)

print("✅ Dados de teste inseridos!")
db.close()
```

Execute:

```powershell
python src/database/insert_test_data.py
```

### 4.2. Consultar os Dados

```python
from connection import DatabaseConnection

db = DatabaseConnection()
db.connect_psycopg2()

# Listar territórios
territorios = db.execute_query("SELECT * FROM territorios")

for t in territorios:
    print(f"{t['id']}: {t['nome']} - População: {t['populacao_estimada']}")

db.close()
```

## 🎨 Passo 5: Primeiro Dashboard (Streamlit)

### 5.1. Criar Aplicação Básica

Crie o arquivo `src/app/app.py`:

```python
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Adicionar caminho para importar config
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from config import DashboardConfig
from src.database.connection import DatabaseConnection

# Configurar página
st.set_page_config(
    page_title=DashboardConfig.APP_TITLE,
    page_icon=DashboardConfig.PAGE_ICON,
    layout=DashboardConfig.LAYOUT
)

# Título
st.title("🏥 Sistema de Apoio à Decisão")
st.subheader("Monitoramento de Idosos com Obesidade Grau II e III")

# Conectar ao banco
db = DatabaseConnection()
db.connect_psycopg2()

# Consultar dados
territorios = db.execute_query("SELECT * FROM territorios")

if territorios:
    st.success(f"✅ {len(territorios)} território(s) cadastrado(s)")
    
    # Exibir tabela
    df = pd.DataFrame(territorios)
    st.dataframe(df)
else:
    st.warning("⚠️ Nenhum território cadastrado ainda")

db.close()
```

### 5.2. Executar Dashboard

```powershell
streamlit run src/app/app.py
```

O navegador abrirá automaticamente em `http://localhost:8501`

## 📚 Próximos Passos

Agora que tudo está configurado, você pode:

### Semana 1-2: Análise Exploratória
- [ ] Limpar e normalizar dados do e-SUS
- [ ] Identificar padrões de obesidade por território
- [ ] Analisar comorbidades mais frequentes

### Semana 3-4: Modelo de Risco
- [ ] Definir variáveis preditoras (features)
- [ ] Treinar modelo de classificação (Random Forest, XGBoost)
- [ ] Validar modelo (acurácia, precisão, recall)

### Semana 5-6: Dashboard Completo
- [ ] Implementar mapa de calor com Folium
- [ ] Criar painel de pacientes em risco
- [ ] Sistema de alertas para ACS

### Semana 7-8: Testes e Refinamento
- [ ] Testes de usabilidade
- [ ] Ajustes de desempenho
- [ ] Documentação final

## 🆘 Problemas Comuns

### Erro: "psycopg2 not found"
```powershell
pip install psycopg2-binary
```

### Erro: "PostGIS extension not found"
```sql
-- No psql:
CREATE EXTENSION postgis;
```

### Erro: "Permission denied" no PowerShell
```powershell
# Executar como Admin:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Erro ao importar geopandas
```powershell
# Instalar dependências do sistema
# Baixe o GDAL para Windows:
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal
pip install GDAL-3.X.X-cpXX-cpXX-win_amd64.whl
pip install geopandas
```

## 📞 Contato e Orientação

- **Prof. Cláudio Rodolfo**: [email]
- **Prof. Sóstenes Mistro**: [email]

## 📖 Recursos Úteis

- [Documentação Pandas](https://pandas.pydata.org/docs/)
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [Streamlit Cheat Sheet](https://docs.streamlit.io/library/cheatsheet)
- [PostGIS Documentation](https://postgis.net/documentation/)

---

**Boa sorte no desenvolvimento do seu TCC! 🎓**
