SELECT
    (SELECT COUNT(*) FROM pacientes) AS total_pacientes,
    (SELECT COUNT(*) FROM pacientes WHERE em_acompanhamento = TRUE) AS pacientes_ativos,
    (
        SELECT COUNT(*)
        FROM pacientes
        WHERE em_acompanhamento = TRUE
          AND (CURRENT_DATE - data_ultima_visita) > %(dias_abandono)s
    ) AS pacientes_faltosos,
    (SELECT COUNT(*) FROM territorios) AS total_territorios;
