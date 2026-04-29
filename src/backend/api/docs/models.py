"""Modelos OpenAPI/Swagger da API SAD."""

from flask_restx import fields


def register_models(api):
    """Registra modelos e retorna dicionario para uso nos namespaces."""
    return {
        "health": api.model(
            "HealthResponse",
            {
                "status": fields.String(example="ok"),
                "service": fields.String(example="sad-backend-api"),
            },
        ),
        "kpis": api.model(
            "KpisResponse",
            {
                "total_pacientes": fields.Integer(example=30),
                "pacientes_ativos": fields.Integer(example=30),
                "pacientes_faltosos": fields.Integer(example=16),
                "total_territorios": fields.Integer(example=5),
            },
        ),
        "paciente_resumo": api.model(
            "PacienteResumo",
            {
                "Codigo": fields.String(example="4a2edaad9953236d"),
                "Idade": fields.Integer(example=68),
                "Sexo": fields.String(example="F"),
                "IMC": fields.String(example="42.5"),
                "Grau": fields.String(example="Grau III"),
                "Comorbidades": fields.Integer(example=2),
                "Dias Sem Visita": fields.Integer(example=90),
                "Risco": fields.String(example="Critico"),
                "Territorio": fields.String(example="Centro"),
            },
        ),
        "distribuicao_risco": api.model(
            "DistribuicaoRiscoItem",
            {
                "Risco": fields.String(example="Alto"),
                "Quantidade": fields.Integer(example=12),
            },
        ),
        "distribuicao_grau": api.model(
            "DistribuicaoGrauItem",
            {
                "Grau": fields.String(example="Grau III"),
                "Quantidade": fields.Integer(example=53),
            },
        ),
        "refresh": api.model(
            "RefreshResponse",
            {
                "status": fields.String(example="ok"),
                "refreshed": fields.List(fields.String, example=["mv_estatisticas_territorio"]),
            },
        ),
        "module_status": api.model(
            "ModuleStatusResponse",
            {
                "modulo": fields.String(example="pacientes"),
                "status": fields.String(example="planejado"),
                "mensagem": fields.String(example="Modulo em desenvolvimento incremental."),
            },
        ),
        "paciente_detalhes": api.model(
            "PacienteDetalhes",
            {
                "id": fields.String(example="550e8400-e29b-41d4-a716-446655440000"),
                "codigo_anonimo": fields.String(example="4a2edaad9953236d"),
                "idade": fields.Integer(example=68),
                "sexo": fields.String(example="F"),
                "data_nascimento": fields.String(example="1956-03-15"),
                "em_acompanhamento": fields.Boolean(example=True),
                "data_cadastro": fields.String(example="2024-01-10"),
                "data_ultima_visita": fields.String(example="2024-10-15"),
                "dias_sem_visita": fields.Integer(example=45),
                "territorio": fields.String(example="Centro"),
                "unidade_saude": fields.String(example="UBS Brasil"),
                "endereco": fields.String(example="Rua das Flores, 123"),
                "imc_atual": fields.Float(example=42.5),
                "peso_kg": fields.Float(example=95.5),
                "altura_m": fields.Float(example=1.50),
                "grau_obesidade_atual": fields.String(example="Grau III"),
                "pa_sistolica": fields.Integer(example=145),
                "pa_diastolica": fields.Integer(example=92),
                "glicemia": fields.Integer(example=156),
                "total_comorbidades": fields.Integer(example=3),
                "nivel_risco": fields.String(example="Alto"),
                "score_risco": fields.Float(example=8.2),
                "dias_desde_calculo_risco": fields.Integer(example=7),
                "total_alertas_pendentes": fields.Integer(example=2),
            },
        ),
        "acompanhamento": api.model(
            "Acompanhamento",
            {
                "id": fields.Integer(example=1),
                "data_registro": fields.String(example="2024-10-15"),
                "tipo_atendimento": fields.String(example="Visita Domiciliar"),
                "peso_kg": fields.Float(example=95.5),
                "altura_m": fields.Float(example=1.50),
                "imc": fields.Float(example=42.5),
                "circunferencia_abdominal_cm": fields.Float(example=118.5),
                "grau_obesidade": fields.String(example="Grau III"),
                "pressao_arterial_sistolica": fields.Integer(example=145),
                "pressao_arterial_diastolica": fields.Integer(example=92),
                "glicemia_mg_dl": fields.Integer(example=156),
                "observacoes": fields.String(example="Paciente apresenta edema em membros inferiores"),
                "criado_em": fields.String(example="2024-10-15T10:30:00"),
                "variacao_imc": fields.Float(example=-0.5),
            },
        ),
        "comorbidade": api.model(
            "Comorbidade",
            {
                "id": fields.Integer(example=1),
                "condicao": fields.String(example="Diabetes Mellitus Tipo 2"),
                "data_diagnostico": fields.String(example="2015-05-20"),
                "ativo": fields.Boolean(example=True),
                "descricao_adicional": fields.String(example="Controlada com Metformina"),
            },
        ),
        "alerta": api.model(
            "Alerta",
            {
                "id": fields.Integer(example=1),
                "tipo_alerta": fields.String(example="Visita Pendente"),
                "prioridade": fields.String(example="Alta"),
                "titulo": fields.String(example="Paciente sem visita há 60 dias"),
                "descricao": fields.String(example="Última visita foi em 15/08/2024"),
                "data_geracao": fields.String(example="2024-10-15T10:30:00"),
                "resolvido": fields.Boolean(example=False),
                "dias_alerta": fields.Integer(example=3),
            },
        ),
        "paciente_busca_resultado": api.model(
            "PacienteBuscaResultado",
            {
                "id": fields.String(example="550e8400-e29b-41d4-a716-446655440000"),
                "codigo_anonimo": fields.String(example="4a2edaad9953236d"),
                "idade": fields.Integer(example=68),
                "sexo": fields.String(example="F"),
                "em_acompanhamento": fields.Boolean(example=True),
                "dias_sem_visita": fields.Integer(example=45),
                "territorio": fields.String(example="Centro"),
                "unidade_saude": fields.String(example="UBS Brasil"),
                "imc_atual": fields.Float(example=42.5),
                "grau_obesidade": fields.String(example="Grau III"),
                "total_comorbidades": fields.Integer(example=3),
                "nivel_risco": fields.String(example="Alto"),
                "score_risco": fields.Float(example=8.2),
            },
        ),
        "risco_calculado": api.model(
            "RiscoCalculado",
            {
                "paciente_id": fields.String(example="550e8400-e29b-41d4-a716-446655440000"),
                "score_risco": fields.Integer(example=78),
                "nivel_risco": fields.String(example="Alto"),
                "fatores_risco": fields.List(fields.String, example=["Atraso no acompanhamento", "Obesidade Grau III"]),
                "metodo": fields.String(example="machine_learning"),
                "recomendacao": fields.String(example="Agendar consulta em 7 dias. Telemonitoramento diário."),
            },
        ),
    }
