# SQL do projeto SAD

Esta pasta centraliza SQL versionado da aplicacao.

## Estrutura

- `queries/`: consultas usadas pela aplicacao
- `views/`: views tradicionais
- `materialized_views/`: views materializadas
- `functions/`: funcoes de banco
- `indexes/`: indices complementares
- `seeds/`: massa de dados de exemplo

## Queries Disponíveis

### Dashboard
- `kpis.sql` - Indicadores principais (total pacientes, ativos, faltosos, territórios)
- `pacientes_lista.sql` - Lista priorizada de pacientes
- `grau_distribuicao.sql` - Contagem por grau de obesidade
- `risco_distribuicao.sql` - Contagem por nível de risco
- `territorio_estatisticas.sql` - Agregação por território

### Módulo de Pacientes
- `pacientes_busca.sql` - Busca avançada com múltiplos filtros
- `paciente_detalhes.sql` - Informações completas de um paciente específico
- `paciente_acompanhamentos.sql` - Histórico de visitas/consultas
- `paciente_comorbidades.sql` - Condições crônicas ativas/inativas
- `paciente_alertas.sql` - Alertas gerados e resolvidos

## Uso no app

As consultas em `queries/` sao carregadas pelo repositorio do dashboard ou do módulo de pacientes.

## Materialized views

Para atualizar manualmente:

```powershell
c:/Users/joaoh/Documents/pasta/sad-obesidade-idosos/venv/Scripts/python.exe src/database/refresh_materialized_views.py
```

## Documentação

Para documentação detalhada do módulo de pacientes, veja:
- `src/backend/api/docs/PACIENTES_MODULE.md`
