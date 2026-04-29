-- Histórico de acompanhamentos (visitas/consultas) de um paciente
SELECT
    a.id,
    a.data_registro,
    a.tipo_atendimento,
    a.peso_kg,
    a.altura_m,
    a.imc,
    a.circunferencia_abdominal_cm,
    a.grau_obesidade,
    a.pressao_arterial_sistolica,
    a.pressao_arterial_diastolica,
    a.glicemia_mg_dl,
    a.observacoes,
    a.criado_em,
    -- Variação desde a medição anterior
    (
        SELECT a1.imc - a2.imc
        FROM acompanhamentos a1, acompanhamentos a2
        WHERE a1.paciente_id = %(paciente_id)s
          AND a2.paciente_id = %(paciente_id)s
          AND a1.id = a.id
          AND a2.data_registro = (
              SELECT MAX(data_registro)
              FROM acompanhamentos
              WHERE paciente_id = %(paciente_id)s
                AND data_registro < a.data_registro
          )
        LIMIT 1
    ) AS variacao_imc
FROM acompanhamentos a
WHERE a.paciente_id = %(paciente_id)s
ORDER BY a.data_registro DESC
LIMIT %(limite)s;
