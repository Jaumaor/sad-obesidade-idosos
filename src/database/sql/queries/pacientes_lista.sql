SELECT
    mv.codigo_anonimo,
    mv.idade,
    mv.sexo,
    mv.imc_atual AS "IMC",
    mv.grau_obesidade AS grau_obesidade_atual,
    mv.total_comorbidades,
    mv.dias_sem_visita,
    r.nivel_risco AS nivel_risco_atual,
    mv.bairro AS territorio
FROM mv_idosos_obesos_atual mv
LEFT JOIN LATERAL (
    SELECT nivel_risco
    FROM risco_estratificado
    WHERE co_seq_cidadao = mv.co_seq_cidadao
    ORDER BY data_calculo DESC
    LIMIT 1
) r ON TRUE
ORDER BY mv.dias_sem_visita DESC NULLS LAST
LIMIT %(limite)s;
