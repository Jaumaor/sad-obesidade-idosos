-- Dados geográficos para mapa de calor (lat/lon + nível de risco)
-- Rota: paciente -> tb_fat_cidadao_pec -> tb_fat_visita_domiciliar (última visita com GPS)
-- Intensidade do ponto = score_risco (0-100)
SELECT DISTINCT ON (mv.co_seq_cidadao)
    fvd.nu_latitude   AS lat,
    fvd.nu_longitude  AS lon,
    COALESCE(r.score_risco, 50) AS intensidade,
    COALESCE(r.nivel_risco, 'Sem cálculo') AS nivel_risco,
    mv.bairro
FROM mv_idosos_obesos_atual mv
JOIN tb_fat_cidadao_pec fcp ON fcp.co_cidadao = mv.co_seq_cidadao
JOIN tb_fat_visita_domiciliar fvd ON fvd.co_fat_cidadao_pec = fcp.co_seq_fat_cidadao_pec
LEFT JOIN LATERAL (
    SELECT score_risco, nivel_risco
    FROM risco_estratificado
    WHERE co_seq_cidadao = mv.co_seq_cidadao
    ORDER BY data_calculo DESC
    LIMIT 1
) r ON TRUE
WHERE fvd.nu_latitude IS NOT NULL
  AND fvd.nu_latitude != 0
  AND fvd.nu_latitude BETWEEN -15.5 AND -14.0
  AND fvd.nu_longitude BETWEEN -41.5 AND -40.0
ORDER BY mv.co_seq_cidadao, fvd.nu_latitude DESC;
