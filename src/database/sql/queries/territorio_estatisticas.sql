SELECT
    territorio,
    total_pacientes,
    pacientes_ativos,
    pacientes_faltosos,
    COALESCE(media_score_risco, 0) AS media_score_risco
FROM mv_estatisticas_territorio
ORDER BY media_score_risco DESC, total_pacientes DESC;
