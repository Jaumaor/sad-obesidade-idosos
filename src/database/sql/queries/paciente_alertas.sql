-- Alertas gerados automaticamente com base nos dados clínicos atuais
-- (não usa tabela de alertas - gera on-the-fly a partir da MV)
SELECT * FROM (
    SELECT 1 AS id, 'Visita Pendente' AS tipo_alerta, 'Alta' AS prioridade,
           'Paciente sem visita há ' || mv.dias_sem_visita || ' dias' AS titulo,
           'Última visita registrada em ' || mv.data_ultima_visita::text AS descricao,
           CURRENT_TIMESTAMP AS data_geracao, FALSE AS resolvido,
           mv.dias_sem_visita AS dias_alerta
    FROM mv_idosos_obesos_atual mv
    WHERE mv.co_seq_cidadao = %(paciente_id)s AND mv.dias_sem_visita > 60

    UNION ALL

    SELECT 2, 'IMC Crítico', 'Urgente',
           'IMC de ' || ROUND(mv.imc_atual, 1) || ' (Grau III+)',
           'Paciente com obesidade ' || mv.grau_obesidade,
           CURRENT_TIMESTAMP, FALSE, 0
    FROM mv_idosos_obesos_atual mv
    WHERE mv.co_seq_cidadao = %(paciente_id)s AND mv.imc_atual >= 40

    UNION ALL

    SELECT 3, 'Risco Elevado', 'Urgente',
           'Score de risco: ' || r.score_risco || ' (' || r.nivel_risco || ')',
           r.recomendacoes,
           r.criado_em, FALSE,
           EXTRACT(DAY FROM CURRENT_TIMESTAMP - r.criado_em)::int
    FROM risco_estratificado r
    WHERE r.co_seq_cidadao = %(paciente_id)s
      AND r.nivel_risco IN ('Alto', 'Critico')
    ORDER BY r.data_calculo DESC
    LIMIT 1
) alertas
ORDER BY prioridade DESC, dias_alerta DESC
LIMIT %(limite)s;
