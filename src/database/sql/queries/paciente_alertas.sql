-- Alertas gerados para um paciente
SELECT
    a.id,
    a.tipo_alerta,
    a.prioridade,
    a.titulo,
    a.descricao,
    a.data_geracao,
    a.data_visualizacao,
    a.data_resolucao,
    a.resolvido,
    a.observacoes_resolucao,
    EXTRACT(DAY FROM CURRENT_TIMESTAMP - a.data_geracao) AS dias_alerta
FROM alertas a
WHERE a.paciente_id = %(paciente_id)s
ORDER BY a.resolvido ASC, a.prioridade DESC, a.data_geracao DESC
LIMIT %(limite)s;
