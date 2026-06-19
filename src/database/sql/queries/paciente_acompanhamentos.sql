-- Histórico de medições de um paciente (dados reais do e-SUS)
SELECT
    m.co_seq_medicao AS id,
    m.dt_medicao::date AS data_registro,
    'Atendimento' AS tipo_atendimento,
    CAST(m.nu_medicao_peso AS NUMERIC) AS peso_kg,
    CAST(m.nu_medicao_altura AS NUMERIC) / 100.0 AS altura_m,
    CAST(m.nu_medicao_imc AS NUMERIC) AS imc,
    NULL::numeric AS circunferencia_abdominal_cm,
    CASE
        WHEN CAST(m.nu_medicao_imc AS NUMERIC) >= 50 THEN 'Super Obesidade'
        WHEN CAST(m.nu_medicao_imc AS NUMERIC) >= 40 THEN 'Grau III'
        WHEN CAST(m.nu_medicao_imc AS NUMERIC) >= 35 THEN 'Grau II'
        ELSE NULL
    END AS grau_obesidade,
    CAST(NULLIF(SPLIT_PART(m.nu_medicao_pressao_arterial, '/', 1), '') AS NUMERIC) AS pressao_arterial_sistolica,
    CAST(NULLIF(SPLIT_PART(m.nu_medicao_pressao_arterial, '/', 2), '') AS NUMERIC) AS pressao_arterial_diastolica,
    CAST(m.nu_medicao_glicemia AS NUMERIC) AS glicemia_mg_dl,
    NULL AS observacoes,
    m.dt_medicao AS criado_em,
    -- Variação IMC em relação à medição anterior
    CAST(m.nu_medicao_imc AS NUMERIC) - LAG(CAST(m.nu_medicao_imc AS NUMERIC))
        OVER (ORDER BY m.dt_medicao ASC) AS variacao_imc
FROM tb_medicao m
JOIN tb_atend_prof ap ON m.co_atend_prof = ap.co_seq_atend_prof
JOIN tb_atend a ON ap.co_seq_atend_prof = a.co_atend_prof
JOIN tb_prontuario pr ON a.co_prontuario = pr.co_seq_prontuario
WHERE pr.co_cidadao = %(paciente_id)s
  AND m.nu_medicao_peso IS NOT NULL
  AND m.nu_medicao_altura IS NOT NULL
ORDER BY m.dt_medicao DESC
LIMIT %(limite)s;
