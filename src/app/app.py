"""
SAD - Sistema de Apoio à Decisão
Dashboard Principal (Versão Inicial)

Autor: João Henrique de Jesus Silva
IFBA - Campus Vitória da Conquista
"""

from src.database.connection import DatabaseConnection
from config import DashboardConfig, ClinicalConfig
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

# Adicionar caminho para importar módulos do projeto
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))


# ============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================================

st.set_page_config(
    page_title=DashboardConfig.APP_TITLE,
    page_icon=DashboardConfig.PAGE_ICON,
    layout=DashboardConfig.LAYOUT,
    initial_sidebar_state="expanded"
)

# ============================================================================
# ESTILO CSS CUSTOMIZADO
# ============================================================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #009639;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #009639;
    }
    .risk-low { color: #4CAF50; font-weight: bold; }
    .risk-moderate { color: #FFC107; font-weight: bold; }
    .risk-high { color: #FF9800; font-weight: bold; }
    .risk-critical { color: #F44336; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - FILTROS
# ============================================================================

st.sidebar.image(
    "https://via.placeholder.com/300x100.png?text=IFBA+Logo", use_column_width=True)
st.sidebar.title("Filtros")

# Filtro por território (será implementado quando houver dados)
territorio_filter = st.sidebar.multiselect(
    "Território/Bairro",
    options=["Todos"],  # Será populado com dados reais
    default=["Todos"]
)

# Filtro por nível de risco
risco_filter = st.sidebar.multiselect(
    "Nível de Risco",
    options=["Todos", "Crítico", "Alto", "Moderado", "Baixo"],
    default=["Todos"]
)

# Filtro por grau de obesidade
obesidade_filter = st.sidebar.multiselect(
    "Grau de Obesidade",
    options=["Todos", "Grau II", "Grau III"],
    default=["Todos"]
)

st.sidebar.markdown("---")
st.sidebar.info("""
Sobre o Sistema

Este dashboard auxilia no monitoramento de idosos com obesidade grau II e III na Atenção Básica de Vitória da Conquista - BA.

Desenvolvido como TCC do curso de Sistemas de Informação - IFBA.
""")

# ============================================================================
# HEADER PRINCIPAL
# ============================================================================

st.markdown('<div class="main-header">Sistema de Apoio à Decisão</div>',
            unsafe_allow_html=True)
st.markdown("### Monitoramento de Idosos com Obesidade Grau II e III")
st.markdown(
    f"**Data de atualização:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.markdown("---")

# ============================================================================
# CONECTAR AO BANCO DE DADOS
# ============================================================================


@st.cache_resource
def get_database_connection():
    """Cria conexão com o banco (cached para melhor performance)"""
    db = DatabaseConnection()
    db.connect_psycopg2()
    return db


try:
    db = get_database_connection()
    conexao_ok = True
except Exception as e:
    st.error(f"[ERRO] Erro ao conectar ao banco de dados: {e}")
    st.info("Verifique se o PostgreSQL está rodando e as configurações no arquivo .env estão corretas.")
    conexao_ok = False

# ============================================================================
# DASHBOARD - KPIS PRINCIPAIS
# ============================================================================

if conexao_ok:
    st.subheader("Indicadores Principais")

    # Consultar estatísticas básicas
    try:
        # Total de pacientes cadastrados
        result_total = db.execute_query("""
            SELECT COUNT(*) as total FROM pacientes
        """)
        total_pacientes = result_total[0]['total'] if result_total else 0

        # Pacientes em acompanhamento
        result_acompanhamento = db.execute_query("""
            SELECT COUNT(*) as total 
            FROM pacientes 
            WHERE em_acompanhamento = TRUE
        """)
        pacientes_ativos = result_acompanhamento[0]['total'] if result_acompanhamento else 0

        # Pacientes faltosos (mais de 60 dias sem visita)
        result_faltosos = db.execute_query("""
            SELECT COUNT(*) as total 
            FROM pacientes 
            WHERE (CURRENT_DATE - data_ultima_visita) > 60
            AND em_acompanhamento = TRUE
        """)
        pacientes_faltosos = result_faltosos[0]['total'] if result_faltosos else 0

        # Total de territórios
        result_territorios = db.execute_query("""
            SELECT COUNT(*) as total FROM territorios
        """)
        total_territorios = result_territorios[0]['total'] if result_territorios else 0

        # Exibir métricas em colunas
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Total de Pacientes",
                value=total_pacientes,
                delta=None
            )

        with col2:
            st.metric(
                label="Em Acompanhamento",
                value=pacientes_ativos,
                delta=f"{(pacientes_ativos/total_pacientes*100):.1f}%" if total_pacientes > 0 else "0%"
            )

        with col3:
            st.metric(
                label="Pacientes Faltosos",
                value=pacientes_faltosos,
                delta=f"{(pacientes_faltosos/total_pacientes*100):.1f}%" if total_pacientes > 0 else "0%",
                delta_color="inverse"
            )

        with col4:
            st.metric(
                label="Territórios Cobertos",
                value=total_territorios,
                delta=None
            )

        st.markdown("---")

        # ================================================================
        # SEÇÃO: LISTA DE PACIENTES
        # ================================================================

        st.subheader("Lista de Pacientes")

        # Consultar pacientes com dados completos
        pacientes_query = """
            SELECT * FROM vw_pacientes_completos 
            ORDER BY dias_sem_visita DESC NULLS LAST
            LIMIT 50
        """

        try:
            pacientes_data = db.execute_query(pacientes_query)

            if pacientes_data:
                df_pacientes = pd.DataFrame(pacientes_data)

                # Formatar colunas para exibição
                df_display = df_pacientes[[
                    'codigo_anonimo', 'idade', 'sexo', 'imc_atual',
                    'grau_obesidade_atual', 'total_comorbidades',
                    'dias_sem_visita', 'nivel_risco_atual', 'territorio'
                ]].copy()

                df_display.columns = [
                    'Código', 'Idade', 'Sexo', 'IMC',
                    'Grau', 'Comorbidades',
                    'Dias Sem Visita', 'Risco', 'Território'
                ]

                # Aplicar formatação condicional
                def highlight_risk(row):
                    if row['Risco'] == 'Crítico':
                        return ['background-color: #ffebee'] * len(row)
                    elif row['Risco'] == 'Alto':
                        return ['background-color: #fff3e0'] * len(row)
                    else:
                        return [''] * len(row)

                st.dataframe(
                    df_display.style.apply(highlight_risk, axis=1),
                    use_container_width=True,
                    height=400
                )

                # Download dos dados
                csv = df_display.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Baixar Lista (CSV)",
                    data=csv,
                    file_name=f"pacientes_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.info(
                    "Nenhum paciente cadastrado ainda. Execute o script de inserção de dados de teste.")

        except Exception as e:
            st.warning(f"[AVISO] Erro ao carregar lista de pacientes: {e}")

        st.markdown("---")

        # ================================================================
        # SEÇÃO: GRÁFICOS
        # ================================================================

        st.subheader("Análises")

        col_graph1, col_graph2 = st.columns(2)

        with col_graph1:
            st.markdown("**Distribuição por Grau de Obesidade**")

            # Dados fictícios (substituir por dados reais quando disponível)
            grau_data = pd.DataFrame({
                'Grau': ['Grau II', 'Grau III'],
                'Quantidade': [30, 15]  # Exemplo
            })

            fig_grau = px.pie(
                grau_data,
                values='Quantidade',
                names='Grau',
                color_discrete_sequence=['#FFC107', '#F44336']
            )
            st.plotly_chart(fig_grau, use_container_width=True)

        with col_graph2:
            st.markdown("**Distribuição por Nível de Risco**")

            # Dados fictícios
            risco_data = pd.DataFrame({
                'Risco': ['Baixo', 'Moderado', 'Alto', 'Crítico'],
                'Quantidade': [10, 20, 12, 3]  # Exemplo
            })

            fig_risco = px.bar(
                risco_data,
                x='Risco',
                y='Quantidade',
                color='Risco',
                color_discrete_map={
                    'Baixo': '#4CAF50',
                    'Moderado': '#FFC107',
                    'Alto': '#FF9800',
                    'Crítico': '#F44336'
                }
            )
            fig_risco.update_layout(showlegend=False)
            st.plotly_chart(fig_risco, use_container_width=True)

    except Exception as e:
        st.error(f"[ERRO] Erro ao carregar indicadores: {e}")

else:
    st.warning(
        "[AVISO] Sistema sem conexão com o banco de dados. Configure o ambiente primeiro.")
    st.info("""
    **Passos para configurar:**
    
    1. Instale o PostgreSQL e crie o banco 'sad_obesidade'
    2. Execute o script: `src/database/schema.sql`
    3. Configure o arquivo `.env` com suas credenciais
    4. Reinicie a aplicação
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9rem;'>
    Desenvolvido por João Henrique de Jesus Silva | IFBA - Campus Vitória da Conquista | 2025<br>
    TCC - Bacharelado em Sistemas de Informação
</div>
""", unsafe_allow_html=True)
