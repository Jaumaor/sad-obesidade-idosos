-- Comorbidades (condições crônicas) de um paciente
SELECT
    c.id,
    c.condicao,
    c.data_diagnostico,
    c.ativo,
    c.descricao_adicional,
    c.criado_em,
    c.atualizado_em
FROM comorbidades c
WHERE c.paciente_id = %(paciente_id)s
ORDER BY ativo DESC, c.condicao ASC;
