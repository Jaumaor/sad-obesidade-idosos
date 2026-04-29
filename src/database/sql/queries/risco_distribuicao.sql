SELECT
    nivel_risco AS risco,
    COUNT(*) AS quantidade
FROM risco_estratificado
WHERE data_calculo = CURRENT_DATE
GROUP BY nivel_risco
ORDER BY quantidade DESC;
