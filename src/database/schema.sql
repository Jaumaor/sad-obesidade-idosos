-- ============================================================================
-- Sistema de Apoio à Decisão para Monitoramento de Idosos com Obesidade
-- PostgreSQL + PostGIS Schema
-- 
-- Autor: João Henrique de Jesus Silva
-- Instituição: IFBA - Campus Vitória da Conquista
-- Data: 2025
--
-- ARQUITETURA: Os dados clínicos vêm diretamente das tabelas do e-SUS/PEC
-- (tb_cidadao, tb_medicao, tb_problema, tb_cid10, etc.) através de uma
-- Materialized View (mv_idosos_obesos_atual). A única tabela própria do SAD
-- é risco_estratificado, que armazena o histórico de scores calculados
-- pelo modelo de Machine Learning.
-- ============================================================================

-- Habilitar extensão PostGIS (caso ainda não esteja ativada)
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- MATERIALIZED VIEW: mv_idosos_obesos_atual
-- Descrição: Consolida dados de idosos (60+) com obesidade grau II+ a partir
--            das tabelas reais do e-SUS/PEC. Traz a última medição de cada
--            cidadão com IMC >= 35, junto com comorbidades mapeadas por CID-10.
--
-- Fonte dos dados:
--   tb_medicao → medições (peso, altura, IMC, PA, glicemia)
--   tb_atend_prof / tb_atend / tb_prontuario → cadeia de joins
--   tb_cidadao → dados demográficos
--   tb_problema + tb_cid10 → diagnósticos/comorbidades
--
-- Refresh: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_idosos_obesos_atual;
-- ============================================================================

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_idosos_obesos_atual AS
WITH ultima_medicao AS (
    SELECT DISTINCT ON (c.co_seq_cidadao)
        c.co_seq_cidadao,
        MD5(c.co_seq_cidadao::text) AS codigo_anonimo,
        DATE_PART('year', AGE(CURRENT_DATE, c.dt_nascimento))::int AS idade,
        COALESCE(c.no_sexo, 'F') AS sexo,
        c.no_bairro AS bairro,
        CAST(m.nu_medicao_peso AS NUMERIC) AS peso_kg,
        CAST(m.nu_medicao_altura AS NUMERIC) AS altura_cm,
        CAST(m.nu_medicao_imc AS NUMERIC) AS imc_atual,
        m.nu_medicao_pressao_arterial AS pa_raw,
        CAST(NULLIF(SPLIT_PART(m.nu_medicao_pressao_arterial, '/', 1), '') AS NUMERIC) AS pa_sistolica,
        CAST(NULLIF(SPLIT_PART(m.nu_medicao_pressao_arterial, '/', 2), '') AS NUMERIC) AS pa_diastolica,
        CAST(m.nu_medicao_glicemia AS NUMERIC) AS glicemia,
        m.dt_medicao AS data_ultima_visita,
        (CURRENT_DATE - m.dt_medicao::date) AS dias_sem_visita,
        CASE
            WHEN CAST(m.nu_medicao_imc AS NUMERIC) >= 50 THEN 'Super Obesidade'
            WHEN CAST(m.nu_medicao_imc AS NUMERIC) >= 40 THEN 'Grau III'
            ELSE 'Grau II'
        END AS grau_obesidade
    FROM tb_medicao m
    JOIN tb_atend_prof ap ON m.co_atend_prof = ap.co_seq_atend_prof
    JOIN tb_atend a ON ap.co_seq_atend_prof = a.co_atend_prof
    JOIN tb_prontuario pr ON a.co_prontuario = pr.co_seq_prontuario
    JOIN tb_cidadao c ON pr.co_cidadao = c.co_seq_cidadao
    WHERE m.nu_medicao_peso IS NOT NULL
      AND m.nu_medicao_altura IS NOT NULL
      AND c.dt_nascimento <= CURRENT_DATE - INTERVAL '60 years'
      AND c.st_faleceu = 0
      AND CAST(m.nu_medicao_imc AS NUMERIC) BETWEEN 35 AND 70
      AND CAST(m.nu_medicao_altura AS NUMERIC) BETWEEN 100 AND 220
      AND CAST(m.nu_medicao_peso AS NUMERIC) BETWEEN 40 AND 250
    ORDER BY c.co_seq_cidadao, m.dt_medicao DESC
),
comorbidades AS (
    SELECT
        pr.co_cidadao AS co_seq_cidadao,
        COUNT(DISTINCT cid.nu_cid10) AS total_comorbidades,
        bool_or(cid.nu_cid10 SIMILAR TO 'E1[0-4]%') AS tem_diabetes,
        bool_or(cid.nu_cid10 SIMILAR TO 'I1[0-5]%') AS tem_hipertensao,
        bool_or(cid.nu_cid10 SIMILAR TO 'I(2[0-5]|48|49|50)%') AS tem_doenca_cardiaca,
        bool_or(cid.nu_cid10 LIKE 'E78%') AS tem_dislipidemia,
        bool_or(cid.nu_cid10 SIMILAR TO 'N1[89]%') AS tem_irc,
        bool_or(cid.nu_cid10 SIMILAR TO 'F3[23]%') AS tem_depressao,
        bool_or(cid.nu_cid10 SIMILAR TO 'M1[5-9]%') AS tem_artrose,
        array_agg(DISTINCT cid.nu_cid10) FILTER (WHERE cid.nu_cid10 IS NOT NULL) AS cids
    FROM tb_problema p
    JOIN tb_prontuario pr ON p.co_prontuario = pr.co_seq_prontuario
    LEFT JOIN tb_cid10 cid ON p.co_cid10 = cid.co_cid10
    GROUP BY pr.co_cidadao
)
SELECT
    um.co_seq_cidadao,
    um.codigo_anonimo,
    um.idade,
    um.sexo,
    um.bairro,
    um.peso_kg,
    um.altura_cm,
    um.imc_atual,
    um.pa_sistolica,
    um.pa_diastolica,
    um.glicemia,
    um.data_ultima_visita,
    um.dias_sem_visita,
    um.grau_obesidade,
    COALESCE(co.total_comorbidades, 0) AS total_comorbidades,
    COALESCE(co.tem_diabetes, false) AS tem_diabetes,
    COALESCE(co.tem_hipertensao, false) AS tem_hipertensao,
    COALESCE(co.tem_doenca_cardiaca, false) AS tem_doenca_cardiaca,
    COALESCE(co.tem_dislipidemia, false) AS tem_dislipidemia,
    COALESCE(co.tem_irc, false) AS tem_irc,
    COALESCE(co.tem_depressao, false) AS tem_depressao,
    COALESCE(co.tem_artrose, false) AS tem_artrose,
    co.cids,
    -- Flag de acompanhamento: sem visita há mais de 90 dias = faltoso
    (um.dias_sem_visita <= 90) AS em_acompanhamento
FROM ultima_medicao um
LEFT JOIN comorbidades co ON um.co_seq_cidadao = co.co_seq_cidadao;

-- Índice único para REFRESH CONCURRENTLY
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_idosos_pk
    ON mv_idosos_obesos_atual (co_seq_cidadao);

CREATE INDEX IF NOT EXISTS idx_mv_idosos_bairro
    ON mv_idosos_obesos_atual (bairro);

CREATE INDEX IF NOT EXISTS idx_mv_idosos_imc
    ON mv_idosos_obesos_atual (imc_atual DESC);

COMMENT ON MATERIALIZED VIEW mv_idosos_obesos_atual IS
    'Dados consolidados de idosos (60+) com obesidade grau II+ extraídos das tabelas e-SUS/PEC. '
    'Refresh com: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_idosos_obesos_atual;';

-- ============================================================================
-- TABELA: risco_estratificado
-- Descrição: Histórico de scores de risco calculados pelo modelo de ML.
--            Única tabela própria do SAD — referencia co_seq_cidadao do e-SUS.
-- ============================================================================
CREATE TABLE IF NOT EXISTS risco_estratificado (
    id SERIAL PRIMARY KEY,
    co_seq_cidadao BIGINT NOT NULL,

    data_calculo DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Score de risco (0-100, onde 100 é risco máximo)
    score_risco NUMERIC(5, 2) CHECK (score_risco >= 0 AND score_risco <= 100),

    -- Classificação categórica
    nivel_risco VARCHAR(20) CHECK (nivel_risco IN ('Baixo', 'Moderado', 'Alto', 'Critico')),

    -- Fatores que contribuíram para o score
    fatores_risco JSONB,

    -- Recomendações geradas automaticamente
    recomendacoes TEXT,

    -- Versão do modelo utilizado
    versao_modelo VARCHAR(20),

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_risco_cidadao ON risco_estratificado(co_seq_cidadao);
CREATE INDEX IF NOT EXISTS idx_risco_nivel ON risco_estratificado(nivel_risco);
CREATE INDEX IF NOT EXISTS idx_risco_data ON risco_estratificado(data_calculo DESC);

COMMENT ON TABLE risco_estratificado IS 'Histórico de scores de risco calculados pelo modelo preditivo (GradientBoosting)';
COMMENT ON COLUMN risco_estratificado.co_seq_cidadao IS 'Referencia tb_cidadao.co_seq_cidadao do e-SUS';
COMMENT ON COLUMN risco_estratificado.fatores_risco IS 'JSON com os fatores de risco identificados pelo modelo';

-- ============================================================================
-- FUNÇÃO AUXILIAR: atualizar_timestamp
-- ============================================================================
CREATE OR REPLACE FUNCTION atualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FIM DO SCHEMA
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'Schema SAD criado com sucesso!';
    RAISE NOTICE 'Materialized View: mv_idosos_obesos_atual (fonte: e-SUS)';
    RAISE NOTICE 'Tabela: risco_estratificado (scores do modelo ML)';
END $$;
