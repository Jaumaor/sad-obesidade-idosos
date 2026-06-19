-- Obter detalhes completos de um paciente pelo co_seq_cidadao
SELECT
    mv.co_seq_cidadao AS id,
    mv.codigo_anonimo,
    mv.idade,
    mv.sexo,
    mv.em_acompanhamento,
    mv.data_ultima_visita,
    mv.dias_sem_visita,

    mv.bairro AS territorio,

    mv.imc_atual,
    mv.peso_kg,
    mv.altura_cm / 100.0 AS altura_m,
    mv.grau_obesidade AS grau_obesidade_atual,
    mv.pa_sistolica,
    mv.pa_diastolica,
    mv.glicemia,

    mv.total_comorbidades,
    mv.tem_diabetes,
    mv.tem_hipertensao,
    mv.tem_doenca_cardiaca,
    mv.tem_dislipidemia,
    mv.tem_irc,
    mv.tem_depressao,
    mv.tem_artrose,
    mv.cids,

    -- Risco atual (último cálculo)
    r.nivel_risco,
    r.score_risco,
    CURRENT_DATE - r.data_calculo AS dias_desde_calculo_risco,
    r.fatores_risco,
    r.recomendacoes,

    0 AS total_alertas_pendentes

FROM mv_idosos_obesos_atual mv
LEFT JOIN LATERAL (
    SELECT nivel_risco, score_risco, data_calculo, fatores_risco, recomendacoes
    FROM risco_estratificado
    WHERE co_seq_cidadao = mv.co_seq_cidadao
    ORDER BY data_calculo DESC
    LIMIT 1
) r ON TRUE
WHERE mv.co_seq_cidadao = %(paciente_id)s;
