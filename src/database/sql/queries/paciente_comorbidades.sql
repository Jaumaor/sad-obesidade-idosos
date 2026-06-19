-- Comorbidades (condições crônicas) de um paciente via CID-10 do e-SUS
SELECT
    p.co_seq_problema AS id,
    COALESCE(cid.ds_cid10, cid.nu_cid10, 'Sem descrição') AS condicao,
    NULL::date AS data_diagnostico,
    TRUE AS ativo,
    cid.nu_cid10 AS descricao_adicional
FROM tb_problema p
JOIN tb_prontuario pr ON p.co_prontuario = pr.co_seq_prontuario
LEFT JOIN tb_cid10 cid ON p.co_cid10 = cid.co_cid10
WHERE pr.co_cidadao = %(paciente_id)s
ORDER BY cid.nu_cid10 ASC;
