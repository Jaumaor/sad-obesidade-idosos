# Módulo de Pacientes - Documentação Técnica

## 📋 Visão Geral

O módulo de pacientes fornece uma API completa para gerenciamento e consulta de informações de pacientes idosos com obesidade. Inclui busca avançada, histórico de acompanhamentos, comorbidades e alertas.

---

## 🔌 Endpoints

### 1. **Buscar Pacientes** (com filtros avançados)
```
GET /api/v1/pacientes/buscar?[filtros]
```

**Parâmetros de Query:**
- `territorio_ids` (string): IDs de territórios separados por vírgula (ex: `1,2,3`)
- `unidade_saude_ids` (string): IDs de unidades de saúde (ex: `1,2`)
- `idade_minima` (integer): Idade mínima do paciente
- `idade_maxima` (integer): Idade máxima do paciente
- `em_acompanhamento` (boolean): Filtrar por status de acompanhamento (true/false)
- `limite` (integer): Máximo de resultados (padrão: 100, máximo: 500)

**Exemplo:**
```bash
curl "http://localhost:8000/api/v1/pacientes/buscar?territorio_ids=1,2&idade_minima=60&limite=20"
```

**Resposta:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "codigo_anonimo": "4a2edaad9953236d",
    "idade": 68,
    "sexo": "F",
    "em_acompanhamento": true,
    "dias_sem_visita": 45,
    "territorio": "Centro",
    "unidade_saude": "UBS Brasil",
    "imc_atual": 42.5,
    "grau_obesidade": "Grau III",
    "total_comorbidades": 3,
    "nivel_risco": "Alto",
    "score_risco": 8.2
  }
]
```

---

### 2. **Obter Detalhes de um Paciente**
```
GET /api/v1/pacientes/{paciente_id}
```

**Parâmetros:**
- `paciente_id` (path): UUID do paciente

**Exemplo:**
```bash
curl "http://localhost:8000/api/v1/pacientes/550e8400-e29b-41d4-a716-446655440000"
```

**Resposta:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "codigo_anonimo": "4a2edaad9953236d",
  "idade": 68,
  "sexo": "F",
  "data_nascimento": "1956-03-15",
  "em_acompanhamento": true,
  "data_cadastro": "2024-01-10",
  "data_ultima_visita": "2024-10-15",
  "dias_sem_visita": 45,
  "territorio": "Centro",
  "unidade_saude": "UBS Brasil",
  "endereco": "Rua das Flores, 123",
  "imc_atual": 42.5,
  "peso_kg": 95.5,
  "altura_m": 1.50,
  "grau_obesidade_atual": "Grau III",
  "pa_sistolica": 145,
  "pa_diastolica": 92,
  "glicemia": 156,
  "total_comorbidades": 3,
  "nivel_risco": "Alto",
  "score_risco": 8.2,
  "dias_desde_calculo_risco": 7,
  "total_alertas_pendentes": 2
}
```

---

### 3. **Histórico de Acompanhamentos** (Visitas/Consultas)
```
GET /api/v1/pacientes/{paciente_id}/acompanhamentos?limite=50
```

**Parâmetros:**
- `paciente_id` (path): UUID do paciente
- `limite` (query): Máximo de registros (padrão: 50, máximo: 500)

**Exemplo:**
```bash
curl "http://localhost:8000/api/v1/pacientes/550e8400-e29b-41d4-a716-446655440000/acompanhamentos?limite=10"
```

**Resposta:**
```json
[
  {
    "id": 1,
    "data_registro": "2024-10-15",
    "tipo_atendimento": "Visita Domiciliar",
    "peso_kg": 95.5,
    "altura_m": 1.50,
    "imc": 42.5,
    "circunferencia_abdominal_cm": 118.5,
    "grau_obesidade": "Grau III",
    "pressao_arterial_sistolica": 145,
    "pressao_arterial_diastolica": 92,
    "glicemia_mg_dl": 156,
    "observacoes": "Paciente apresenta edema em membros inferiores",
    "variacao_imc": -0.5
  }
]
```

---

### 4. **Comorbidades** (Condições Crônicas)
```
GET /api/v1/pacientes/{paciente_id}/comorbidades
```

**Exemplo:**
```bash
curl "http://localhost:8000/api/v1/pacientes/550e8400-e29b-41d4-a716-446655440000/comorbidades"
```

**Resposta:**
```json
[
  {
    "id": 1,
    "condicao": "Diabetes Mellitus Tipo 2",
    "data_diagnostico": "2015-05-20",
    "ativo": true,
    "descricao_adicional": "Controlada com Metformina"
  },
  {
    "id": 2,
    "condicao": "Hipertensão Arterial",
    "data_diagnostico": "2012-08-10",
    "ativo": true,
    "descricao_adicional": null
  }
]
```

---

### 5. **Alertas Gerados**
```
GET /api/v1/pacientes/{paciente_id}/alertas?limite=50
```

**Parâmetros:**
- `paciente_id` (path): UUID do paciente
- `limite` (query): Máximo de alertas (padrão: 50, máximo: 500)

**Exemplo:**
```bash
curl "http://localhost:8000/api/v1/pacientes/550e8400-e29b-41d4-a716-446655440000/alertas?limite=10"
```

**Resposta:**
```json
[
  {
    "id": 1,
    "tipo_alerta": "Visita Pendente",
    "prioridade": "Alta",
    "titulo": "Paciente sem visita há 60 dias",
    "descricao": "Última visita foi em 15/08/2024",
    "data_geracao": "2024-10-15T10:30:00",
    "resolvido": false,
    "dias_alerta": 3
  },
  {
    "id": 2,
    "tipo_alerta": "Risco Elevado",
    "prioridade": "Urgente",
    "titulo": "Score de risco crítico",
    "descricao": "Paciente com score de risco 9.2 - requer intervenção imediata",
    "data_geracao": "2024-10-18T14:20:00",
    "resolvido": false,
    "dias_alerta": 0
  }
]
```

---

### 6. **Status do Módulo**
```
GET /api/v1/pacientes/modulo-status
```

**Resposta:**
```json
{
  "modulo": "pacientes",
  "status": "ativo",
  "mensagem": "Módulo funcional com busca, detalhes, histórico e alertas."
}
```

---

## 📊 Queries SQL

### Arquivos de Query

| Arquivo | Descrição |
|---------|-----------|
| `pacientes_busca.sql` | Busca avançada com múltiplos filtros |
| `paciente_detalhes.sql` | Informações completas de um paciente |
| `paciente_acompanhamentos.sql` | Histórico de visitas/consultas |
| `paciente_comorbidades.sql` | Condições crônicas ativas/inativas |
| `paciente_alertas.sql` | Alertas gerados e resolvidos |

---

## 🔍 Filtros de Busca - Exemplos

### Buscar por Território
```bash
curl "http://localhost:8000/api/v1/pacientes/buscar?territorio_ids=1"
```

### Buscar por Faixa Etária
```bash
curl "http://localhost:8000/api/v1/pacientes/buscar?idade_minima=70&idade_maxima=80"
```

### Buscar Pacientes em Acompanhamento
```bash
curl "http://localhost:8000/api/v1/pacientes/buscar?em_acompanhamento=true"
```

### Busca Combinada
```bash
curl "http://localhost:8000/api/v1/pacientes/buscar?territorio_ids=1,2&idade_minima=60&em_acompanhamento=true&limite=50"
```

---

## 🏗️ Arquitetura

```
API Request
    ↓
Namespace (pacientes.py)
    ↓
ApiDependencies (injeção)
    ↓
DashboardService
    ↓
DashboardRepository
    ↓
SQL Queries (em arquivos)
    ↓
PostgreSQL + PostGIS
```

---

## ✅ Testes

Execute o script de testes:
```bash
python test_pacientes_module.py
```

Isso testará todos os 6 endpoints do módulo automaticamente.

---

## 🔒 Segurança

- IDs de pacientes são **UUIDs** (impossível enumerar sequencialmente)
- Dados identificadores são **anonimizados** (apenas `codigo_anonimo`)
- Localizações têm **precisão reduzida** (por quadrícula, não coordenada exata)
- Requer **autenticação** no futuro (JWT token)

---

## 📈 Performance

- Queries otimizadas com **índices** nas colunas frequentes
- **Materialized views** para agregações complexas
- **LIMIT** obrigatório em buscas
- Máximo de **500 registros** por requisição

---

## 🚀 Próximos Passos

1. ✅ [x] Implementar endpoints de busca e detalhes
2. ⏳ [ ] Implementar criação/edição de pacientes (POST/PUT)
3. ⏳ [ ] Integração com frontend
4. ⏳ [ ] Autenticação e autorização
5. ⏳ [ ] Cache de resultados (Redis)
6. ⏳ [ ] Auditoria de acessos

