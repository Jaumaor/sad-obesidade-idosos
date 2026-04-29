# Implementação Módulo de Pacientes ✅

## 📊 O Que Foi Implementado

### 1️⃣ **5 Queries SQL Novas** (em `src/database/sql/queries/`)
```
✅ pacientes_busca.sql           - Busca com filtros avançados
✅ paciente_detalhes.sql         - Dados completos de 1 paciente
✅ paciente_acompanhamentos.sql  - Histórico de visitas
✅ paciente_comorbidades.sql     - Condições crônicas
✅ paciente_alertas.sql          - Alertas gerados
```

### 2️⃣ **Modelos OpenAPI** (models.py)
```
✅ paciente_detalhes      - Resposta completa de paciente
✅ acompanhamento        - Registro de visita
✅ comorbidade           - Condição crônica
✅ alerta                - Alerta do sistema
✅ paciente_busca_resultado - Item da busca
```

### 3️⃣ **Endpoints Funcionais** (namespace pacientes.py)
```
✅ GET  /api/v1/pacientes/buscar                    - Busca com 6 filtros
✅ GET  /api/v1/pacientes/<id>                      - Detalhes completos
✅ GET  /api/v1/pacientes/<id>/acompanhamentos     - Histórico de visitas
✅ GET  /api/v1/pacientes/<id>/comorbidades        - Condições crônicas
✅ GET  /api/v1/pacientes/<id>/alertas              - Alertas pendentes
✅ GET  /api/v1/pacientes/modulo-status             - Status módulo
```

### 4️⃣ **Métodos de Repository** 
```
✅ get_paciente_detalhes()
✅ get_paciente_acompanhamentos()
✅ get_paciente_comorbidades()
✅ get_paciente_alertas()
✅ buscar_pacientes()
```

### 5️⃣ **Testes e Documentação**
```
✅ test_pacientes_module.py - Script de teste automático
✅ PACIENTES_MODULE.md      - Documentação técnica completa
✅ README.md (SQL)          - Atualizado com novas queries
```

---

## 🚀 Como Usar

### **1. Iniciar a API**
```powershell
venv\Scripts\python.exe src\backend\api\app.py
```

### **2. Executar Testes**
```powershell
venv\Scripts\python.exe test_pacientes_module.py
```

### **3. Acessar Swagger**
```
http://localhost:8000/docs
```

### **4. Exemplos de Requisições**

**Buscar pacientes de um território:**
```bash
curl "http://localhost:8000/api/v1/pacientes/buscar?territorio_ids=1&limite=10"
```

**Obter detalhes de um paciente:**
```bash
curl "http://localhost:8000/api/v1/pacientes/{UUID-AQUI}"
```

**Ver histórico de visitas:**
```bash
curl "http://localhost:8000/api/v1/pacientes/{UUID-AQUI}/acompanhamentos?limite=20"
```

---

## 📋 Filtros de Busca Disponíveis

| Filtro | Exemplo | Tipo |
|--------|---------|------|
| `territorio_ids` | `1,2,3` | string (IDs separadas por vírgula) |
| `unidade_saude_ids` | `1,2` | string (IDs separadas por vírgula) |
| `idade_minima` | `60` | integer |
| `idade_maxima` | `80` | integer |
| `em_acompanhamento` | `true` / `false` | boolean |
| `limite` | `100` | integer (máx: 500) |

---

## 🎯 Próximas Etapas

### **Fase 1: Integração Frontend** (PRÓXIMO)
- [ ] Criar página `/pacientes` no frontend
- [ ] Implementar formulário de busca
- [ ] Populate tabela com resultados
- [ ] Criar modal de detalhes
- [ ] Mostrar histórico de visitas

### **Fase 2: CRUD Completo**
- [ ] POST `/api/v1/pacientes` - Criar novo paciente
- [ ] PUT `/api/v1/pacientes/<id>` - Editar dados
- [ ] DELETE `/api/v1/pacientes/<id>` - Marcar como inativo
- [ ] POST `/api/v1/pacientes/<id>/acompanhamentos` - Registrar visita

### **Fase 3: Recursos Avançados**
- [ ] Export CSV de busca
- [ ] Relatório PDF individual
- [ ] Notificações de alertas
- [ ] Histórico de edições (auditoria)
- [ ] Integração com Mapa (PostGIS)

---

## 📊 Estrutura de Dados

```
PACIENTE
├── Detalhes Pessoais
│   ├── Idade, Sexo, Data Nascimento
│   ├── Territorio, Unidade Saúde
│   └── Coordenadas (anonimizadas)
├── Medições Atuais
│   ├── Peso, Altura, IMC
│   ├── Pressão Arterial
│   └── Glicemia
├── Histórico
│   ├── Acompanhamentos (múltiplas visitas)
│   ├── Comorbidades (condições crônicas)
│   └── Alertas (sistema automático)
└── Risco
    ├── Score (0-100)
    ├── Nível (Baixo/Médio/Alto/Crítico)
    └── Data Cálculo
```

---

## 🔧 Configuração do Banco

As queries ja estão otimizadas com:
- ✅ Índices em colunas frequentes
- ✅ LIMIT obrigatório
- ✅ Avoid N+1 queries (JOINs eficientes)
- ✅ Variação de IMC calculada automaticamente
- ✅ Dias desde última visita dinâmico

---

## 💡 Dicas de Performance

1. **Usar filtros específicos** para reduzir resultados
2. **Limitar a 50-100 registros** por página
3. **Não fazer buscas sem filtros** (sem limite)
4. **Cache os resultados no frontend** para 5 minutos
5. **Use paginação** ao listar muitos pacientes

---

## ✨ Status Atual

| Componente | Status | Pronto? |
|-----------|--------|---------|
| Queries SQL | ✅ Completo | Sim |
| Modelos OpenAPI | ✅ Completo | Sim |
| Endpoints | ✅ Funcional | Sim |
| Repository | ✅ Implementado | Sim |
| Testes | ✅ Criado | Sim |
| Documentação | ✅ Detalhada | Sim |
| Frontend | ⏳ Não iniciado | Próximo |

---

## 🎓 Como Integrar no Frontend

Exemplo de chamada em JavaScript:

```javascript
// 1. Buscar pacientes
fetch('/api/v1/pacientes/buscar?territorio_ids=1&limite=50')
  .then(r => r.json())
  .then(pacientes => console.log(pacientes))

// 2. Obter detalhes de um paciente
fetch(`/api/v1/pacientes/${id}`)
  .then(r => r.json())
  .then(detalhes => console.log(detalhes))

// 3. Ver histórico
fetch(`/api/v1/pacientes/${id}/acompanhamentos?limite=20`)
  .then(r => r.json())
  .then(historico => console.log(historico))
```

---

**🎉 Módulo de Pacientes está 100% funcional e pronto para integração!**
