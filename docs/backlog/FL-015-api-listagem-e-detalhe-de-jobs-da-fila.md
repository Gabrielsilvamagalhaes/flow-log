# FL-015 — Listagem paginada e detalhe de job da fila

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend, API
**Estimativa:** 1 dia
**Depende de:** `FL-012`, `FL-014`

---

## Motivação

Painéis central e direito do dashboard. A paginação já existe e não deve ser reinventada: `get_logs_by_job_id` (`src/flowlog/services/job_service.py:89`) já define o formato de resposta com `items`, `total`, `page`, `page_size`, `total_pages` via `JobLogsResponseDto`.

---

## Comportamento esperado

### `GET /api/v1/queues/{fila}/jobs`

- [ ] Paginado no mesmo formato de `JobLogsResponseDto`
- [ ] Filtro `state` (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`)
- [ ] Filtro `search` — `icontains` no `job_name`, mesmo padrão de `JobLog.message.icontains` (`job_service.py:110`)
- [ ] Ordenação: mais recentes primeiro
- [ ] Limites de `page`/`page_size` iguais aos de `get_logs` (`src/flowlog/routes/job_routes.py:77`)
- [ ] Item da lista é enxuto: sem payload, sem stack trace (a lista não pode trafegar 64 KB por linha)

### `GET /api/v1/queues/{fila}/jobs/{external_id}`

- [ ] Detalhe completo: `payload` sanitizado, `opts`, `attempts_made`/`max_attempts`, `worker_id`, tempo de espera, duração, `failed_reason`, `stack_trace`
- [ ] Inclui os `JobLog` do job (reaproveitar `get_logs_by_job_id`)
- [ ] Job inexistente devolve 404 no padrão de `is_exists_job` (`src/flowlog/shared/utils/is_exists_job.py:10`)

---

## Escopo

- [ ] Endpoints no `queues_router` de `FL-014`
- [ ] Funções no `queue_service.py`, com a contagem total em query separada (padrão de `get_total_logs_by_job_id`, `job_service.py:73`)
- [ ] DTOs de item de lista e de detalhe

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Rota | `src/flowlog/routes/queue_routes.py` |
| Service | `src/flowlog/services/queue_service.py` |
| Referência de paginação | `src/flowlog/services/job_service.py:89` |

---

## Critérios de aceite

- [ ] Listagem filtrada por `state=FAILED` devolve só os jobs que falharam da fila
- [ ] `search` casa parte do nome do job, case-insensitive
- [ ] Detalhe de um job que falhou traz o stack trace real vindo do Redis
- [ ] Payload no detalhe vem com `***MASKED***` onde havia `apiToken`
- [ ] Fila inexistente devolve 404, não lista vazia

---

## Fora de escopo

- Retry, promover ou remover job — escrita está fora do nível 1
