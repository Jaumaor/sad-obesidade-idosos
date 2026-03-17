# SAD - Sistema de Apoio à Decisão para Monitoramento de Idosos com Obesidade

## Sobre o Projeto

Sistema de Apoio à Decisão focado no monitoramento e acompanhamento de pacientes idosos com obesidade grau II e III na Atenção Primária à Saúde (APS) do SUS em Vitória da Conquista - BA.

**Autor:** João Henrique de Jesus Silva  
**Orientador:** Prof. Cláudio Rodolfo S. de Oliveira  
**Co-orientador:** Prof. Sóstenes Mistro  
**Instituição:** IFBA - Campus Vitória da Conquista  
**Curso:** Bacharelado em Sistemas de Informação

## Objetivos

- Auxiliar equipes da APS na identificação precoce de riscos em idosos com obesidade severa
- Estratificar pacientes por nível de risco utilizando Machine Learning
- Georreferenciar casos prioritários para otimização de visitas domiciliares
- Fornecer dashboards interativos para Agentes Comunitários de Saúde (ACS)

## Arquitetura do Sistema

```
┌─────────────────┐
│   Dashboard     │  ← Streamlit/Flask (Visualização)
│   (Frontend)    │
└────────┬────────┘
         │
┌────────▼────────┐
│   API/Lógica    │  ← Python (Flask/Django)
│   (Backend)     │
└────────┬────────┘
         │
┌────────▼────────┐
│  PostgreSQL +   │  ← Banco de Dados Geoespacial
│    PostGIS      │
└─────────────────┘
```

## Estrutura de Pastas

```
sad-obesidade-idoso/
├── data/                    # Dados brutos e processados (não versionados)
│   ├── raw/                 # CSVs originais do e-SUS (anonimizados)
│   ├── processed/           # Dados limpos e estruturados
│   └── geojson/            # Polígonos de bairros/territórios
├── notebooks/               # Jupyter Notebooks para análise exploratória
│   ├── 01_eda.ipynb        # Análise Exploratória de Dados
│   ├── 02_feature_engineering.ipynb
│   └── 03_model_training.ipynb
├── src/                     # Código fonte da aplicação
│   ├── database/           # Scripts SQL e configuração do banco
│   │   ├── schema.sql      # Estrutura das tabelas
│   │   ├── migrations/     # Migrações de banco de dados
│   │   └── seeds/          # Dados de teste (opcional)
│   ├── models/             # Modelos de Machine Learning
│   │   ├── risk_model.pkl  # Modelo serializado
│   │   └── predictor.py    # Lógica de predição
│   ├── preprocessing/      # Scripts de limpeza de dados
│   │   ├── clean_esus_data.py
│   │   └── geocode.py      # Georreferenciamento de endereços
│   └── app/                # Aplicação web
│       ├── app.py          # Streamlit/Flask main
│       ├── components/     # Componentes de UI
│       └── utils/          # Funções auxiliares
├── tests/                   # Testes automatizados
├── docs/                    # Documentação adicional
├── requirements.txt         # Dependências Python
├── config.py               # Configurações gerais
├── .env.example            # Exemplo de variáveis de ambiente
├── .gitignore
└── README.md
```

## Tecnologias Utilizadas

### Banco de Dados
- **PostgreSQL 14+**: Sistema gerenciador de banco de dados relacional
- **PostGIS 3.x**: Extensão para dados geoespaciais

### Backend & Análise
- **Python 3.10+**: Linguagem principal
- **Pandas**: Manipulação de dados
- **GeoPandas**: Análise geoespacial
- **Scikit-learn**: Machine Learning
- **Matplotlib/Seaborn**: Visualizações estáticas

### Frontend
- **Streamlit**: Prototipação de dashboards interativos
- **Plotly**: Gráficos interativos
- **Folium**: Mapas web

## Requisitos do Sistema

### Software
- Python 3.10 ou superior
- PostgreSQL 14+ com extensão PostGIS
- pip (gerenciador de pacotes Python)

### Hardware Recomendado
- 8GB RAM mínimo (16GB recomendado para análise de grandes volumes)
- 10GB de espaço em disco

## Instalação

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd obesidade-idosos
```

### 2. Crie um ambiente virtual Python
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instale as dependências
```powershell
pip install -r requirements.txt
```

### 4. Configure o PostgreSQL/PostGIS

**Certifique-se de ter o PostgreSQL instalado com a extensão PostGIS.**

Crie o banco de dados:
```sql
CREATE DATABASE sad_obesidade;
\c sad_obesidade
CREATE EXTENSION postgis;
```

### 5. Configure as variáveis de ambiente
```powershell
Copy-Item .env.example .env
# Edite o arquivo .env com suas credenciais do banco
```

### 6. Execute o schema inicial
```powershell
psql -U postgres -d sad_obesidade -f src/database/schema.sql
```

## Uso

### Executar Análise Exploratória
```powershell
jupyter notebook notebooks/01_eda.ipynb
```

### Executar Dashboard (Streamlit)
```powershell
streamlit run src/app/app.py
```

## Funcionalidades Principais

### 1. Dashboard Gerencial
- Visualização de idosos com obesidade grau II/III
- Separação por acompanhamento regular vs. irregular
- Indicadores de desempenho (KPIs)

### 2. Painel de Risco
- Score de risco calculado por ML
- Lista automática de pacientes faltosos
- Alertas de abandono de tratamento

### 3. Mapa de Calor
- Distribuição geoespacial de pacientes em risco
- Análise por território/bairro
- Otimização de rotas para visitas domiciliares

### 4. Sistema de Alertas
- Notificações para ACS responsáveis
- Priorização de visitas domiciliares

## Modelo de Risco

O escore de risco é calculado considerando:

- **IMC**: Grau de obesidade (II ou III)
- **Comorbidades**: Diabetes, hipertensão, doenças cardiovasculares
- **Tempo desde última visita**: Indicador de abandono
- **Idade**: Fator de vulnerabilidade adicional
- **Sarcopenia**: Quando disponível

Algoritmos testados:
- Random Forest Classifier
- Gradient Boosting
- Logistic Regression

## Aspectos Éticos e de Segurança

⚠️ **IMPORTANTE**: Este sistema manipula dados sensíveis de saúde.

- Todos os dados devem ser **anonimizados** antes do processamento
- Nunca versionar dados reais no Git
- Cumprir LGPD (Lei Geral de Proteção de Dados)
- Acesso restrito apenas a profissionais autorizados

## Cronograma de Desenvolvimento

| Etapa | Período |
|-------|---------|
| Revisão e Configuração do Ambiente | 01/02/2026 - 28/02/2026 |
| Coleta e Pré-processamento de Dados | 01/02/2026 - 30/03/2026 |
| Desenvolvimento do Modelo de Risco | 01/03/2026 - 30/03/2026 |
| Implementação Visual e Geoespacial | 01/03/2026 - 30/04/2026 |
| Testes Funcionais e Ajustes | 01/04/2026 - 30/04/2026 |
| Análise dos Resultados Técnicos | 01/05/2026 - 30/05/2026 |
| Redação Final | 01/06/2026 - 30/06/2026 |

## Contribuindo

Este é um projeto acadêmico de TCC. Sugestões e melhorias são bem-vindas através de issues ou pull requests.

## Licença

Este projeto está sob licença MIT - veja o arquivo LICENSE para detalhes.

## Contato

João Henrique de Jesus Silva - [email institucional]

## Referências Principais

- ZASLAVSKY, O. et al. (2021). Obesity in the Elderly. *J Clin Endocrinol Metab*, 106(9), 2788-2798.
- MACHADO, R. E. T. et al. (2020). Experiências de idosos com obesidade na APS. *Rev Bras Enferm*, 73(supl.3).
- ALSAREII, S. A. et al. (2022). IoT Framework for Decision-Making System of Obesity. *Life*, 12(9), 1414.

---

**Desenvolvido no IFBA - Campus Vitória da Conquista | 2025-2026**
