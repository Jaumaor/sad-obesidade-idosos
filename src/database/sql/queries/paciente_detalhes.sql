-- Obter detalhes completos de um paciente específico
SELECT
    p.id,
    p.codigo_anonimo,
    p.idade,
    p.sexo,
    p.data_nascimento,
    p.em_acompanhamento,
    p.data_cadastro,
    p.data_ultima_visita,
    CURRENT_DATE - p.data_ultima_visita AS dias_sem_visita,
    
    t.id AS territorio_id,
    t.nome AS territorio,
    
    us.id AS unidade_saude_id,
    us.nome AS unidade_saude,
    us.endereco,
    us.telefone,
    
    -- Último acompanhamento
    (SELECT imc FROM acompanhamentos WHERE paciente_id = p.id ORDER BY data_registro DESC LIMIT 1) AS imc_atual,
    (SELECT peso_kg FROM acompanhamentos WHERE paciente_id = p.id ORDER BY data_registro DESC LIMIT 1) AS peso_kg,
    (SELECT altura_m FROM acompanhamentos WHERE paciente_id = p.id ORDER BY data_registro DESC LIMIT 1) AS altura_m,
    (SELECT grau_obesidade FROM acompanhamentos WHERE paciente_id = p.id ORDER BY data_registro DESC LIMIT 1) AS grau_obesidade_atual,
    (SELECT pressao_arterial_sistolica FROM acompanhamentos WHERE paciente_id = p.id ORDER BY data_registro DESC LIMIT 1) AS pa_sistolica,
    (SELECT pressao_arterial_diastolica FROM acompanhamentos WHERE paciente_id = p.id ORDER BY data_registro DESC LIMIT 1) AS pa_diastolica,
    (SELECT glicemia_mg_dl FROM acompanhamentos WHERE paciente_id = p.id ORDER BY data_registro DESC LIMIT 1) AS glicemia,
    
    -- Contagem de comorbidades
    (SELECT COUNT(*) FROM comorbidades WHERE paciente_id = p.id AND ativo = TRUE) AS total_comorbidades,
    
    -- Risco atual
    (SELECT nivel_risco FROM risco_estratificado WHERE paciente_id = p.id ORDER BY data_calculo DESC LIMIT 1) AS nivel_risco,
    (SELECT score_risco FROM risco_estratificado WHERE paciente_id = p.id ORDER BY data_calculo DESC LIMIT 1) AS score_risco,
    (SELECT CURRENT_DATE - data_calculo::date FROM risco_estratificado WHERE paciente_id = p.id ORDER BY data_calculo DESC LIMIT 1) AS dias_desde_calculo_risco,
    
    -- Alertas não resolvidos
    (SELECT COUNT(*) FROM alertas WHERE paciente_id = p.id AND resolvido = FALSE) AS total_alertas_pendentes,
    
    p.criado_em,
    p.atualizado_em
FROM pacientes p
LEFT JOIN territorios t ON p.territorio_id = t.id
LEFT JOIN unidades_saude us ON p.unidade_saude_id = us.id
WHERE p.id = %(paciente_id)s;
