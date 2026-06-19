-- Busca avançada de pacientes com filtros (dados do e-SUS via MV)
SELECT
    mv.co_seq_cidadao AS id,
    mv.codigo_anonimo,
    mv.idade,
    mv.sexo,
    mv.em_acompanhamento,
    mv.data_ultima_visita,
    mv.dias_sem_visita,
    mv.bairro AS territorio,
    NULL AS unidade_saude,
    mv.imc_atual,
    mv.grau_obesidade,
    mv.total_comorbidades,
    r.nivel_risco,
    r.score_risco
FROM mv_idosos_obesos_atual mv
LEFT JOIN LATERAL (
    SELECT nivel_risco, score_risco
    FROM risco_estratificado
    WHERE co_seq_cidadao = mv.co_seq_cidadao
    ORDER BY data_calculo DESC
    LIMIT 1
) r ON TRUE
WHERE
    (%(idade_minima)s IS NULL OR mv.idade >= %(idade_minima)s)
    AND (%(idade_maxima)s IS NULL OR mv.idade <= %(idade_maxima)s)
    AND (%(em_acompanhamento)s IS NULL OR mv.em_acompanhamento = %(em_acompanhamento)s)
ORDER BY
    CASE
        WHEN r.nivel_risco = 'Critico' THEN 1
        WHEN r.nivel_risco = 'Alto' THEN 2
        WHEN r.nivel_risco = 'Moderado' THEN 3
        ELSE 4
    END ASC,
    mv.dias_sem_visita DESC
LIMIT %(limite)s;
