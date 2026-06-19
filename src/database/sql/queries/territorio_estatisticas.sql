-- Estatísticas por bairro/território (agregação direta da MV)
SELECT
    mv.bairro AS territorio,
    COUNT(*) AS total_pacientes,
    COUNT(*) FILTER (WHERE mv.em_acompanhamento = TRUE) AS pacientes_ativos,
    COUNT(*) FILTER (WHERE mv.dias_sem_visita > 60) AS pacientes_faltosos,
    COALESCE(AVG(r.score_risco), 0) AS media_score_risco
FROM mv_idosos_obesos_atual mv
LEFT JOIN LATERAL (
    SELECT score_risco
    FROM risco_estratificado
    WHERE co_seq_cidadao = mv.co_seq_cidadao
    ORDER BY data_calculo DESC
    LIMIT 1
) r ON TRUE
WHERE mv.bairro IS NOT NULL
GROUP BY mv.bairro
ORDER BY media_score_risco DESC, total_pacientes DESC;
