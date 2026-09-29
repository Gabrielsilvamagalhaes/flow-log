# PR: Schemas Pydantic BullQueue e BullJob (FL-005)

**Tipo:** feat
**Escopo:** bullmq
**Branch:** `feat/ticket-05` → `main`
**Commits de implementação:** 3 (`135f9d8`, `264b962`, `fb49b38`), mais o commit de documentação desta PR
**Repositório:** flowlog
**Vinculado a:** FL-005 — `docs/backlog/FL-005-schemas-pydantic-bullqueue-bulljob.md` · depende de [[FL-004-cliente-redis-e-construtores-de-chave-do-bullmq]]

---

## Resumo

Adiciona os modelos Pydantic `BullQueue` e `BullJob`, que convertem os dados crus lidos do Redis (hash do job do BullMQ) em objetos tipados. O enum `BullState` passa a representar os estados possíveis de um job (`wait`, `active`, `delayed`, `paused`, `completed`, `failed`).

O `BullJob` faz o parse dos campos serializados (`opts`, `data`, `returnvalue`, `stacktrace`, timestamps em ms) e valida a consistência conforme o estado: por exemplo, job `completed` exige `processedOn` e `finishedOn`, job `failed` exige também `failedReason`, job `delayed` exige `delay` positivo em `opts`. Também expõe `wait_time` e `duration` como campos calculados. A suíte de testes cobre cada estado com fixtures JSON válidas e inválidas.

---

## O que foi alterado

### Backend
- `src/flowlog/bullmq/schemas.py` → novos `BullQueue`, `BullJob`, `BullJobOpts`, `BackoffOptions`, `KeepJobsOptions` e validators por estado
- `src/flowlog/shared/enums/bull_state_enums.py` → novo `BullState` (`StrEnum`)

### Testes
- `tests/unit/bullmq/test_schemas.py` → 14 testes de criação de job por estado e de casos inválidos
- `tests/unit/bullmq/fixtures/*.json` → 13 payloads (válidos e inválidos) por estado

### Exemplos
- `examples/bullmq-test/src/init-job.ts` → `jobId: "error-id-2"` fixo no job de erro
- `examples/bullmq-test/src/workers/test-worker.ts` → worker retorna `"test string"` para popular `returnvalue`

---

## Impacto na aplicação

### Para o time de desenvolvimento
| Antes | Depois |
| --- | --- |
| Dados do job vinham crus do Redis, sem tipagem | Job tipado e validado por estado via `BullJob` |
| Sem enum de estados | `BullState` compartilhado |

### Para a plataforma como um todo
- Base para as camadas seguintes que leem filas/jobs do Redis
- Payload inconsistente com o estado falha na validação em vez de passar silenciosamente

### Limitações conhecidas
- `load_opts_value` usa `print` ao falhar no parse de `opts` (sem logger ainda)


---

## Arquivos principais do PR

```
src/flowlog/bullmq/schemas.py
src/flowlog/shared/enums/bull_state_enums.py
tests/unit/bullmq/test_schemas.py
tests/unit/bullmq/fixtures/
examples/bullmq-test/src/{init-job.ts,workers/test-worker.ts}
```

---

## Como testar

1. Rodar `pytest tests/unit/bullmq/test_schemas.py` → todos os testes passam
2. Subir o exemplo `examples/bullmq-test` e criar jobs → `returnvalue` aparece nos jobs concluídos

---

## Checklist

- [x] Documento cobre os 3 commits à frente de `origin/main`
- [x] Apenas arquivos verificados foram citados
- [x] Sessão "Como testar" tem passos reproduzíveis
- [x] Vinculado ao ticket/backlog correspondente (FL-005)

## Tags

#bcx #pr #bullmq #feat
