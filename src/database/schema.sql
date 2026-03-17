-- ============================================================================
-- Sistema de Apoio à Decisão para Monitoramento de Idosos com Obesidade
-- PostgreSQL + PostGIS Schema
-- 
-- Autor: João Henrique de Jesus Silva
-- Instituição: IFBA - Campus Vitória da Conquista
-- Data: 2025
-- ============================================================================

-- Habilitar extensão PostGIS (caso ainda não esteja ativada)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; -- Para geração de UUIDs

-- ============================================================================
-- TABELA: territorios
-- Descrição: Armazena os polígonos dos bairros/áreas de cobertura das USF
-- ============================================================================
CREATE TABLE territorios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL UNIQUE, -- Nome do bairro/território
    codigo_ibge VARCHAR(10), -- Código IBGE se disponível
    geometria GEOMETRY(MultiPolygon, 4326), -- Polígono do território (SRID 4326 = WGS84)
    populacao_estimada INTEGER,
    area_km2 NUMERIC(10, 2),
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice espacial para otimizar consultas geográficas
CREATE INDEX idx_territorios_geometria ON territorios USING GIST(geometria);

COMMENT ON TABLE territorios IS 'Delimitação geográfica dos territórios de atuação das equipes de saúde';
COMMENT ON COLUMN territorios.geometria IS 'Polígono geográfico no formato WGS84 (EPSG:4326)';

-- ============================================================================
-- TABELA: unidades_saude
-- Descrição: Unidades de Saúde da Família (USF) de Vitória da Conquista
-- ============================================================================
CREATE TABLE unidades_saude (
    id SERIAL PRIMARY KEY,
    cnes VARCHAR(20) UNIQUE, -- Cadastro Nacional de Estabelecimentos de Saúde
    nome VARCHAR(255) NOT NULL,
    endereco TEXT,
    territorio_id INTEGER REFERENCES territorios(id),
    localizacao GEOMETRY(Point, 4326), -- Coordenadas da unidade
    telefone VARCHAR(20),
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_unidades_localizacao ON unidades_saude USING GIST(localizacao);

COMMENT ON TABLE unidades_saude IS 'Unidades Básicas de Saúde (UBS) cadastradas';
COMMENT ON COLUMN unidades_saude.cnes IS 'Código CNES do Ministério da Saúde';

-- ============================================================================
-- TABELA: pacientes
-- Descrição: Cadastro ANONIMIZADO de pacientes idosos com obesidade grau II/III
-- ============================================================================
CREATE TABLE pacientes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_anonimo VARCHAR(50) UNIQUE NOT NULL, -- Identificador anonimizado (ex: hash SHA256)
    
    -- Dados demográficos
    idade INTEGER NOT NULL CHECK (idade >= 60), -- Pacientes idosos
    sexo CHAR(1) CHECK (sexo IN ('M', 'F', 'O')),
    data_nascimento DATE,
    
    -- Localização
    territorio_id INTEGER REFERENCES territorios(id),
    unidade_saude_id INTEGER REFERENCES unidades_saude(id),
    localizacao_residencia GEOMETRY(Point, 4326), -- Coordenadas aproximadas (nunca exatas por privacidade)
    
    -- Status de acompanhamento
    em_acompanhamento BOOLEAN DEFAULT TRUE,
    data_cadastro DATE NOT NULL,
    data_ultima_visita DATE,
    
    -- Metadados
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pacientes_territorio ON pacientes(territorio_id);
CREATE INDEX idx_pacientes_unidade ON pacientes(unidade_saude_id);
CREATE INDEX idx_pacientes_localizacao ON pacientes USING GIST(localizacao_residencia);

COMMENT ON TABLE pacientes IS 'Cadastro anonimizado de pacientes idosos (≥60 anos) com obesidade grau II ou III';
COMMENT ON COLUMN pacientes.codigo_anonimo IS 'Hash irreversível do CPF ou CNS do paciente';
COMMENT ON COLUMN pacientes.localizacao_residencia IS 'Coordenadas com precisão reduzida (aproximação por quadrícula) para preservar privacidade';

-- ============================================================================
-- TABELA: acompanhamentos
-- Descrição: Histórico de consultas e medições antropométricas
-- ============================================================================
CREATE TABLE acompanhamentos (
    id SERIAL PRIMARY KEY,
    paciente_id UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    
    -- Data da consulta/visita
    data_registro DATE NOT NULL,
    
    -- Medidas antropométricas
    peso_kg NUMERIC(5, 2) CHECK (peso_kg > 0 AND peso_kg < 300),
    altura_m NUMERIC(3, 2) CHECK (altura_m > 0.50 AND altura_m < 2.50),
    imc NUMERIC(5, 2) GENERATED ALWAYS AS (peso_kg / (altura_m * altura_m)) STORED,
    circunferencia_abdominal_cm NUMERIC(5, 2),
    
    -- Classificação de obesidade
    grau_obesidade VARCHAR(20) CHECK (grau_obesidade IN ('Grau II', 'Grau III')),
    
    -- Dados clínicos adicionais
    pressao_arterial_sistolica INTEGER,
    pressao_arterial_diastolica INTEGER,
    glicemia_mg_dl INTEGER,
    
    -- Tipo de atendimento
    tipo_atendimento VARCHAR(50) CHECK (tipo_atendimento IN ('Consulta UBS', 'Visita Domiciliar', 'Teleatendimento')),
    
    -- Observações clínicas
    observacoes TEXT,
    
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_acompanhamentos_paciente ON acompanhamentos(paciente_id);
CREATE INDEX idx_acompanhamentos_data ON acompanhamentos(data_registro DESC);

COMMENT ON TABLE acompanhamentos IS 'Registros históricos de consultas e medições dos pacientes';
COMMENT ON COLUMN acompanhamentos.imc IS 'Índice de Massa Corporal calculado automaticamente (peso/altura²)';

-- ============================================================================
-- TABELA: comorbidades
-- Descrição: Condições crônicas associadas (diabetes, hipertensão, etc.)
-- ============================================================================
CREATE TABLE comorbidades (
    id SERIAL PRIMARY KEY,
    paciente_id UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    
    condicao VARCHAR(100) NOT NULL CHECK (condicao IN (
        'Diabetes Mellitus Tipo 2',
        'Hipertensão Arterial',
        'Dislipidemia',
        'Doença Cardiovascular',
        'Fibrilação Atrial',
        'Insuficiência Cardíaca',
        'Doença Renal Crônica',
        'Osteoartrite',
        'Sarcopenia',
        'Apneia do Sono',
        'Depressão',
        'Outra'
    )),
    
    data_diagnostico DATE,
    ativo BOOLEAN DEFAULT TRUE, -- Se a condição está controlada/inativa
    descricao_adicional TEXT,
    
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(paciente_id, condicao) -- Evita duplicação da mesma comorbidade
);

CREATE INDEX idx_comorbidades_paciente ON comorbidades(paciente_id);

COMMENT ON TABLE comorbidades IS 'Comorbidades e condições crônicas associadas aos pacientes';

-- ============================================================================
-- TABELA: risco_estratificado
-- Descrição: Scores de risco calculados pelo modelo de Machine Learning
-- ============================================================================
CREATE TABLE risco_estratificado (
    id SERIAL PRIMARY KEY,
    paciente_id UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    
    data_calculo DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Score de risco (0-100, onde 100 é risco máximo)
    score_risco NUMERIC(5, 2) CHECK (score_risco >= 0 AND score_risco <= 100),
    
    -- Classificação categórica
    nivel_risco VARCHAR(20) CHECK (nivel_risco IN ('Baixo', 'Moderado', 'Alto', 'Crítico')),
    
    -- Fatores que contribuíram para o score
    fatores_risco JSONB, -- Exemplo: {"dias_sem_visita": 90, "comorbidades": 3, "imc": 42.5}
    
    -- Recomendações geradas automaticamente
    recomendacoes TEXT,
    
    -- Versão do modelo utilizado
    versao_modelo VARCHAR(20),
    
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_risco_paciente ON risco_estratificado(paciente_id);
CREATE INDEX idx_risco_nivel ON risco_estratificado(nivel_risco);
CREATE INDEX idx_risco_data ON risco_estratificado(data_calculo DESC);

COMMENT ON TABLE risco_estratificado IS 'Histórico de scores de risco calculados pelo modelo preditivo';
COMMENT ON COLUMN risco_estratificado.fatores_risco IS 'JSON com as variáveis que influenciaram o score';

-- ============================================================================
-- TABELA: alertas
-- Descrição: Alertas e notificações para os Agentes Comunitários de Saúde
-- ============================================================================
CREATE TABLE alertas (
    id SERIAL PRIMARY KEY,
    paciente_id UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    
    tipo_alerta VARCHAR(50) CHECK (tipo_alerta IN (
        'Visita Pendente',
        'Risco Elevado',
        'Abandono de Tratamento',
        'Comorbidade Descompensada',
        'IMC Crítico'
    )),
    
    prioridade VARCHAR(20) CHECK (prioridade IN ('Baixa', 'Média', 'Alta', 'Urgente')),
    
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    
    data_geracao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_visualizacao TIMESTAMP,
    data_resolucao TIMESTAMP,
    
    resolvido BOOLEAN DEFAULT FALSE,
    observacoes_resolucao TEXT,
    
    CONSTRAINT chk_resolucao CHECK (
        (resolvido = FALSE AND data_resolucao IS NULL) OR
        (resolvido = TRUE AND data_resolucao IS NOT NULL)
    )
);

CREATE INDEX idx_alertas_paciente ON alertas(paciente_id);
CREATE INDEX idx_alertas_resolvido ON alertas(resolvido) WHERE resolvido = FALSE;
CREATE INDEX idx_alertas_prioridade ON alertas(prioridade);

COMMENT ON TABLE alertas IS 'Sistema de alertas para notificação dos profissionais de saúde';

-- ============================================================================
-- VIEWS: Consultas pré-montadas para facilitar análises
-- ============================================================================

-- View: Pacientes com dados consolidados
CREATE OR REPLACE VIEW vw_pacientes_completos AS
SELECT 
    p.id,
    p.codigo_anonimo,
    p.idade,
    p.sexo,
    p.em_acompanhamento,
    p.data_ultima_visita,
    CURRENT_DATE - p.data_ultima_visita AS dias_sem_visita,
    
    t.nome AS territorio,
    us.nome AS unidade_saude,
    
    -- Último acompanhamento
    (SELECT imc FROM acompanhamentos WHERE paciente_id = p.id ORDER BY data_registro DESC LIMIT 1) AS imc_atual,
    (SELECT grau_obesidade FROM acompanhamentos WHERE paciente_id = p.id ORDER BY data_registro DESC LIMIT 1) AS grau_obesidade_atual,
    
    -- Contagem de comorbidades
    (SELECT COUNT(*) FROM comorbidades WHERE paciente_id = p.id AND ativo = TRUE) AS total_comorbidades,
    
    -- Último risco calculado
    (SELECT nivel_risco FROM risco_estratificado WHERE paciente_id = p.id ORDER BY data_calculo DESC LIMIT 1) AS nivel_risco_atual,
    (SELECT score_risco FROM risco_estratificado WHERE paciente_id = p.id ORDER BY data_calculo DESC LIMIT 1) AS score_risco_atual,
    
    p.localizacao_residencia,
    p.criado_em,
    p.atualizado_em
FROM pacientes p
LEFT JOIN territorios t ON p.territorio_id = t.id
LEFT JOIN unidades_saude us ON p.unidade_saude_id = us.id;

COMMENT ON VIEW vw_pacientes_completos IS 'Visão consolidada com todos os dados relevantes dos pacientes';

-- View: Pacientes em risco crítico/alto
CREATE OR REPLACE VIEW vw_pacientes_alto_risco AS
SELECT 
    pc.*,
    r.score_risco,
    r.fatores_risco,
    r.recomendacoes
FROM vw_pacientes_completos pc
JOIN risco_estratificado r ON pc.id = r.paciente_id
WHERE r.nivel_risco IN ('Alto', 'Crítico')
  AND r.data_calculo = (
      SELECT MAX(data_calculo) 
      FROM risco_estratificado 
      WHERE paciente_id = pc.id
  )
ORDER BY r.score_risco DESC;

COMMENT ON VIEW vw_pacientes_alto_risco IS 'Pacientes com nível de risco Alto ou Crítico (para priorização de visitas)';

-- View: Estatísticas por território
CREATE OR REPLACE VIEW vw_estatisticas_territorio AS
SELECT 
    t.id AS territorio_id,
    t.nome AS territorio,
    t.geometria,
    COUNT(DISTINCT p.id) AS total_pacientes,
    COUNT(DISTINCT p.id) FILTER (WHERE p.em_acompanhamento = TRUE) AS pacientes_ativos,
    COUNT(DISTINCT p.id) FILTER (
        WHERE (CURRENT_DATE - p.data_ultima_visita) > 60
    ) AS pacientes_faltosos,
    AVG(r.score_risco) AS media_score_risco
FROM territorios t
LEFT JOIN pacientes p ON t.id = p.territorio_id
LEFT JOIN LATERAL (
    SELECT score_risco 
    FROM risco_estratificado 
    WHERE paciente_id = p.id 
    ORDER BY data_calculo DESC 
    LIMIT 1
) r ON TRUE
GROUP BY t.id, t.nome, t.geometria;

COMMENT ON VIEW vw_estatisticas_territorio IS 'Agregação de indicadores por território (para mapa de calor)';

-- ============================================================================
-- FUNÇÕES: Lógica auxiliar
-- ============================================================================

-- Função para calcular distância entre paciente e unidade de saúde
CREATE OR REPLACE FUNCTION calcular_distancia_paciente_unidade(
    p_paciente_id UUID
) RETURNS NUMERIC AS $$
DECLARE
    distancia_metros NUMERIC;
BEGIN
    SELECT ST_Distance(
        p.localizacao_residencia::geography,
        us.localizacao::geography
    )
    INTO distancia_metros
    FROM pacientes p
    JOIN unidades_saude us ON p.unidade_saude_id = us.id
    WHERE p.id = p_paciente_id;
    
    RETURN ROUND(distancia_metros, 2);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calcular_distancia_paciente_unidade IS 'Retorna a distância em metros entre a residência do paciente e sua UBS';

-- Função para atualizar timestamp de atualização
CREATE OR REPLACE FUNCTION atualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para atualização automática de timestamps
CREATE TRIGGER trg_territorios_atualizado
    BEFORE UPDATE ON territorios
    FOR EACH ROW EXECUTE FUNCTION atualizar_timestamp();

CREATE TRIGGER trg_pacientes_atualizado
    BEFORE UPDATE ON pacientes
    FOR EACH ROW EXECUTE FUNCTION atualizar_timestamp();

CREATE TRIGGER trg_comorbidades_atualizado
    BEFORE UPDATE ON comorbidades
    FOR EACH ROW EXECUTE FUNCTION atualizar_timestamp();

CREATE TRIGGER trg_unidades_atualizado
    BEFORE UPDATE ON unidades_saude
    FOR EACH ROW EXECUTE FUNCTION atualizar_timestamp();

-- ============================================================================
-- DADOS DE EXEMPLO (SEED - OPCIONAL, APENAS PARA TESTES)
-- ============================================================================

-- Descomentar as linhas abaixo para inserir dados fictícios de teste

/*
-- Inserir território de exemplo
INSERT INTO territorios (nome, codigo_ibge, geometria, populacao_estimada, area_km2)
VALUES (
    'Centro',
    '2933307',
    ST_GeomFromText('MULTIPOLYGON(((-40.8400 -14.8600, -40.8300 -14.8600, -40.8300 -14.8500, -40.8400 -14.8500, -40.8400 -14.8600)))', 4326),
    15000,
    2.5
);

-- Inserir unidade de saúde de exemplo
INSERT INTO unidades_saude (cnes, nome, endereco, territorio_id, localizacao)
VALUES (
    '1234567',
    'USF Centro',
    'Rua Exemplo, 100',
    1,
    ST_SetSRID(ST_MakePoint(-40.8350, -14.8550), 4326)
);
*/

-- ============================================================================
-- FIM DO SCHEMA
-- ============================================================================

-- Mensagem de confirmação
DO $$
BEGIN
    RAISE NOTICE 'Schema criado com sucesso!';
    RAISE NOTICE 'Total de tabelas: 8';
    RAISE NOTICE 'Total de views: 3';
    RAISE NOTICE 'PostGIS habilitado: %', (SELECT PostGIS_Version());
END $$;
