SELECT
    grau_obesidade AS grau,
    COUNT(*) AS quantidade
FROM mv_idosos_obesos_atual
WHERE grau_obesidade IS NOT NULL
GROUP BY grau_obesidade
ORDER BY quantidade DESC;
