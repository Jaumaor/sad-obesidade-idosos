SELECT
    COUNT(*) AS total_pacientes,
    COUNT(*) FILTER (WHERE em_acompanhamento = TRUE) AS pacientes_ativos,
    COUNT(*) FILTER (WHERE dias_sem_visita > %(dias_abandono)s) AS pacientes_faltosos,
    COUNT(DISTINCT bairro) AS total_territorios
FROM mv_idosos_obesos_atual;
