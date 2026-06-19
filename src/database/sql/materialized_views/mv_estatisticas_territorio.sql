-- Estatísticas por bairro/território a partir da MV principal
-- Dependência: mv_idosos_obesos_atual deve existir
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_estatisticas_territorio AS
SELECT
    mv.bairro AS territorio,
    COUNT(*) AS total_pacientes,
    COUNT(*) FILTER (WHERE mv.em_acompanhamento = TRUE) AS pacientes_ativos,
    COUNT(*) FILTER (WHERE mv.dias_sem_visita > 60) AS pacientes_faltosos,
    COALESCE(AVG(r.score_risco), 0) AS media_score_risco,
    CURRENT_TIMESTAMP AS atualizado_em
FROM mv_idosos_obesos_atual mv
LEFT JOIN LATERAL (
    SELECT score_risco
    FROM risco_estratificado
    WHERE co_seq_cidadao = mv.co_seq_cidadao
    ORDER BY data_calculo DESC
    LIMIT 1
) r ON TRUE
WHERE mv.bairro IS NOT NULL
GROUP BY mv.bairro;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_estatisticas_territorio_bairro
    ON mv_estatisticas_territorio (territorio);
