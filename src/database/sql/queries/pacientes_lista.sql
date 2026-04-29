SELECT
    codigo_anonimo,
    idade,
    sexo,
    imc_atual,
    grau_obesidade_atual,
    total_comorbidades,
    dias_sem_visita,
    nivel_risco_atual,
    territorio
FROM vw_pacientes_completos
ORDER BY dias_sem_visita DESC NULLS LAST
LIMIT %(limite)s;
