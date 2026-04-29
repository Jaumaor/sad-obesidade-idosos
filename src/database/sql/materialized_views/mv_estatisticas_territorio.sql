CREATE MATERIALIZED VIEW IF NOT EXISTS mv_estatisticas_territorio AS
SELECT
    t.id AS territorio_id,
    t.nome AS territorio,
    COUNT(DISTINCT p.id) AS total_pacientes,
    COUNT(DISTINCT p.id) FILTER (WHERE p.em_acompanhamento = TRUE) AS pacientes_ativos,
    COUNT(DISTINCT p.id) FILTER (
        WHERE (CURRENT_DATE - p.data_ultima_visita) > 60
    ) AS pacientes_faltosos,
    AVG(r.score_risco) AS media_score_risco,
    CURRENT_TIMESTAMP AS atualizado_em
FROM territorios t
LEFT JOIN pacientes p ON t.id = p.territorio_id
LEFT JOIN LATERAL (
    SELECT score_risco
    FROM risco_estratificado
    WHERE paciente_id = p.id
    ORDER BY data_calculo DESC
    LIMIT 1
) r ON TRUE
GROUP BY t.id, t.nome;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_estatisticas_territorio_id
    ON mv_estatisticas_territorio (territorio_id);
