# Backlog — Nível 1 (integração automática com BullMQ)

Tickets de entrega derivados de [docs/nivel-1-bullmq.md](../docs/nivel-1-bullmq.md). Um ticket = uma fatia entregável e testável. Nada aqui está implementado.

> As tasks são gerenciadas no **Linear**, projeto [Flowlog](https://linear.app/gabriel-silva-magalhaes/project/flowlog-81fa80816c36) (team `GAB`). O ticket `FL-XXX` corresponde à issue `GAB-(XXX+5)` — ex.: `FL-000` = `GAB-5`, `FL-020` = `GAB-25`. Status e andamento ficam lá; estes arquivos são a especificação.

Cada arquivo segue a mesma estrutura: contexto/motivação, comportamento esperado, escopo com checkboxes, arquivos principais, critérios de aceite, fora de escopo e dependências.

---

## Tickets

| ID | Título | Etapa | Prioridade | Depende de |
| --- | --- | --- | --- | --- |
| [FL-000](FL-000-decisoes-tecnicas-nivel-1.md) | Decisões técnicas que travam o nível 1 | — | Alta | — |
| [FL-001](FL-001-ambiente-redis-docker-compose.md) | Redis de desenvolvimento via docker-compose | 0 | Alta | — |
| [FL-002](FL-002-worker-bullmq-de-exemplo.md) | Worker BullMQ de exemplo com os 4 cenários | 0 | Alta | FL-001 |
| [FL-003](FL-003-mapeamento-de-campos-do-bullmq.md) | Validar o mapeamento de campos contra o BullMQ real | 0/1 | Alta | FL-002 |
| [FL-004](FL-004-cliente-redis-e-construtores-de-chave.md) | Cliente Redis assíncrono e construtores de chave | 1 | Alta | FL-001 |
| [FL-005](FL-005-schemas-pydantic-bullqueue-bulljob.md) | Schemas Pydantic `BullQueue` e `BullJob` | 1 | Alta | FL-003, FL-004 |
| [FL-006](FL-006-reader-operacoes-de-leitura-do-redis.md) | `reader.py`: operações de leitura do Redis | 1 | Alta | FL-004, FL-005 |
| [FL-007](FL-007-estender-modelo-job-para-jobs-de-fila.md) | Estender o modelo `Job` para jobs de fila | 2 | Alta | FL-000, FL-003 |
| [FL-008](FL-008-unicidade-e-idempotencia-do-job-de-fila.md) | Unicidade `(source, queue_name, external_id)` | 2 | Alta | FL-007 |
| [FL-009](FL-009-rn-02-transicao-de-estado-por-origem.md) | RN-02: transição rígida só para origem `API` | 2 | Alta | FL-007 |
| [FL-010](FL-010-sanitizacao-reaproveitavel-e-limite-de-payload.md) | Sanitização reaproveitável (RN-05) e limite de payload | 3 | Alta | FL-007 |
| [FL-011](FL-011-poller-loop-de-sincronizacao.md) | Poller: loop de sincronização | 3 | Alta | FL-006, FL-007 |
| [FL-012](FL-012-upsert-idempotente-de-jobs.md) | Upsert idempotente de jobs no `flowlog.db` | 3 | Alta | FL-008, FL-010, FL-011 |
| [FL-013](FL-013-ingestao-de-logs-nativos-do-bullmq.md) | Ingerir `job.log()` nativo como `JobLog` | 3 | Média | FL-012 |
| [FL-014](FL-014-api-listagem-de-filas.md) | `GET /api/v1/queues`: filas com contadores | 4 | Alta | FL-012 |
| [FL-015](FL-015-api-listagem-e-detalhe-de-jobs-da-fila.md) | Listagem paginada e detalhe de job da fila | 4 | Alta | FL-012, FL-014 |
| [FL-016](FL-016-sse-stream-de-atualizacoes.md) | `GET /api/v1/stream`: SSE das mudanças do poller | 4 | Média | FL-012 |
| [FL-017](FL-017-configuracao-tipada-com-pydantic-settings.md) | Configuração tipada com `pydantic-settings` | 5 | Média | FL-000 |
| [FL-018](FL-018-cli-flowlog-watch.md) | CLI `flowlog watch` | 5 | Alta | FL-011, FL-014, FL-017 |
| [FL-019](FL-019-dashboard-tres-paineis.md) | Dashboard: três painéis servidos pelo FastAPI | 6 | Alta | FL-014, FL-015 |
| [FL-020](FL-020-dashboard-atualizacao-ao-vivo-via-sse.md) | Dashboard ao vivo via SSE | 6 | Média | FL-016, FL-019 |

---

## Ordem de execução

```
FL-000 ─┐
        ├─► FL-007 ─► FL-008 ─┐
FL-003 ─┘        └─► FL-009   │
                              ├─► FL-012 ─┬─► FL-013
FL-001 ─► FL-002 ─► FL-003    │           ├─► FL-014 ─► FL-015 ─► FL-019 ─► FL-020
                              │           └─► FL-016 ─────────────────────┘
FL-001 ─► FL-004 ─► FL-005 ─► FL-006 ─► FL-011 ─┘
                                                 FL-017 ─► FL-018
FL-010 ─────────────────────────────────────────┘
```

Regra do plano: **FL-001 a FL-006 vêm antes de qualquer alteração no modelo.** Elas respondem as perguntas em aberto sobre o Redis; se algo lá não funcionar como descrito, o resto do plano muda.

## Marcos

| Marco | Tickets | O que dá para demonstrar |
| --- | --- | --- |
| M1 — Leitura do Redis | FL-001 a FL-006 | Um script imprime payload, estado e stack trace de um job real |
| M2 — Persistência | FL-007 a FL-013 | O `flowlog.db` espelha as filas em < 2s, sem duplicar linha |
| M3 — API | FL-014 a FL-016 | `/docs` do FastAPI navegável, SSE emitindo evento |
| M4 — Produto | FL-017 a FL-020 | `flowlog watch` abre o dashboard ao vivo |

---

## Definição de pronto (vale para todos os tickets)

- [ ] Critérios de aceite do ticket verificados na mão, contra o ambiente de FL-001/FL-002
- [ ] Testes automatizados do que o ticket introduziu
- [ ] Nada quebrou na ingestão HTTP existente
- [ ] Sem comando de escrita no Redis do usuário
- [ ] Sem valor sensível em texto claro no banco ou na resposta da API

## Fora do nível 1 inteiro

| Fora | Por quê |
| --- | --- |
| `console.log` dentro do processor | O Redis não guarda. Exige SDK Node (nível 2). |
| Etapas intermediárias de um job longo | Idem. |
| Ações de escrita (retry, promover, remover) | Leitura primeiro. Escrita muda o risco do produto. |
| Anexos (RN-04) e API Key (RN-07) | Independentes deste escopo. |
