# FL-012 — Upsert idempotente de jobs no `flowlog.db`

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend, Banco
**Estimativa:** 1 dia
**Depende de:** `FL-008`, `FL-010`, `FL-011`

---

## Motivação

O poller lê os mesmos jobs várias vezes por minuto. A persistência precisa ser idempotente por construção, não por sorte.

Este ticket também é onde o payload cru vira payload sanitizado: é o último ponto antes do disco.

---

## Comportamento esperado

Para cada `BullJob` lido:

1. Buscar por `(source=BULLMQ, queue_name, external_id)`
2. Não existe: inserir, com `payload` passado por `sanitize_payload` e `truncate_payload` de `FL-010`
3. Existe: atualizar só o que mudou — `status`, `attempts_made`, `ended_at`, `failed_reason`, `stack_trace`, `worker_id`, `payload` (o `data` pode mudar entre tentativas)
4. Nada mudou: não escrever, para evitar `UPDATE` inútil a cada segundo
5. Registrar quais jobs mudaram no ciclo — é o insumo do SSE de `FL-016`

- [ ] Gravar em lote por fila, uma transação por lote, nunca uma por job
- [ ] `started_at` recebe `processedOn`; `ended_at` recebe `finishedOn`; `job_name` recebe `name`; `max_attempts` recebe `opts.attempts`
- [ ] `worker_id` extraído do `:lock` conforme confirmado em `FL-003`; se não for viável, deixar nulo em vez de inventar

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Sync | `src/flowlog/sync/job_sync.py` (novo) |
| Modelo | `src/flowlog/server/database/models/jobs.py` |
| Sanitização | `src/flowlog/shared/utils/sanitize.py` |

---

## Critérios de aceite

- [ ] Com o worker de `FL-002` rodando, o `flowlog.db` reflete o estado das filas em menos de 2 segundos
- [ ] Rodar o poller duas vezes seguidas não duplica nenhuma linha: um `GROUP BY queue_name, external_id HAVING COUNT(*) > 1` volta vazio
- [ ] Um job que falha e refaz tentativa tem `attempts_made` crescendo na mesma linha
- [ ] Ciclo sem mudança nenhuma não emite `UPDATE` (verificar com log de SQL ativado)

---

## Fora de escopo

- Purga por retenção — ticket próprio, depois da decisão de `FL-000`
