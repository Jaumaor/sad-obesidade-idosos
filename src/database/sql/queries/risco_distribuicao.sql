-- Distribuição de risco (último score de cada paciente)
SELECT
    r.nivel_risco AS risco,
    COUNT(*) AS quantidade
FROM mv_idosos_obesos_atual mv
JOIN LATERAL (
    SELECT nivel_risco
    FROM risco_estratificado
    WHERE co_seq_cidadao = mv.co_seq_cidadao
    ORDER BY data_calculo DESC
    LIMIT 1
) r ON TRUE
GROUP BY r.nivel_risco
ORDER BY quantidade DESC;
