-- Busca avançada de pacientes com filtros
SELECT
    p.id,
    p.codigo_anonimo,
    p.idade,
    p.sexo,
    p.em_acompanhamento,
    p.data_ultima_visita,
    CURRENT_DATE - p.data_ultima_visita AS dias_sem_visita,
    
    t.nome AS territorio,
    us.nome AS unidade_saude,
    
    (SELECT imc FROM acompanhamentos WHERE paciente_id = p.id ORDER BY data_registro DESC LIMIT 1) AS imc_atual,
    (SELECT grau_obesidade FROM acompanhamentos WHERE paciente_id = p.id ORDER BY data_registro DESC LIMIT 1) AS grau_obesidade,
    (SELECT COUNT(*) FROM comorbidades WHERE paciente_id = p.id AND ativo = TRUE) AS total_comorbidades,
    (SELECT nivel_risco FROM risco_estratificado WHERE paciente_id = p.id ORDER BY data_calculo DESC LIMIT 1) AS nivel_risco,
    (SELECT score_risco FROM risco_estratificado WHERE paciente_id = p.id ORDER BY data_calculo DESC LIMIT 1) AS score_risco
FROM pacientes p
LEFT JOIN territorios t ON p.territorio_id = t.id
LEFT JOIN unidades_saude us ON p.unidade_saude_id = us.id
WHERE 
    (%(territorio_ids)s::INTEGER[] IS NULL OR t.id = ANY(%(territorio_ids)s::INTEGER[]))
    AND (%(unidade_saude_ids)s::INTEGER[] IS NULL OR us.id = ANY(%(unidade_saude_ids)s::INTEGER[]))
    AND (%(idade_minima)s IS NULL OR p.idade >= %(idade_minima)s)
    AND (%(idade_maxima)s IS NULL OR p.idade <= %(idade_maxima)s)
    AND (%(em_acompanhamento)s IS NULL OR p.em_acompanhamento = %(em_acompanhamento)s)
ORDER BY 
    CASE 
        WHEN (SELECT nivel_risco FROM risco_estratificado WHERE paciente_id = p.id ORDER BY data_calculo DESC LIMIT 1) = 'Crítico' THEN 1
        WHEN (SELECT nivel_risco FROM risco_estratificado WHERE paciente_id = p.id ORDER BY data_calculo DESC LIMIT 1) = 'Alto' THEN 2
        WHEN (SELECT nivel_risco FROM risco_estratificado WHERE paciente_id = p.id ORDER BY data_calculo DESC LIMIT 1) = 'Moderado' THEN 3
        ELSE 4
    END ASC,
    CURRENT_DATE - p.data_ultima_visita DESC
LIMIT %(limite)s;
