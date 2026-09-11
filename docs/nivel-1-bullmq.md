# Nível 1 — Integração automática com BullMQ

> Escopo de trabalho. Nada aqui está implementado ainda.

## O que é o nível 1

O FlowLog conecta no mesmo Redis que os workers BullMQ usam, descobre as filas sozinho e transforma cada job da fila em um *Job Run* do FlowLog.

A aplicação Node **não muda uma linha**. O FlowLog não é uma dependência dela — é um observador do Redis.

```
  App Node          Redis              FlowLog            Navegador
 ┌────────┐      ┌────────┐        ┌────────────┐      ┌───────────┐
 │ Worker │ ───► │ bull:* │ ◄───── │ poller     │ ───► │ dashboard │
 │ Queue  │grava │  keys  │   lê   │ + FastAPI  │ SSE  │  :4700    │
 └────────┘      └────────┘        └────────────┘      └───────────┘
```

### Entrega

- `flowlog watch` sobe a API, o poller e o dashboard, e abre o navegador
- Filas descobertas automaticamente, sem arquivo de configuração
- Por job: payload, nome, estado, tentativas, backoff, tempo de espera, duração, stack trace da falha
- Histórico persistido no `flowlog.db` — sobrevive à limpeza da fila pelo `removeOnComplete`

### Fora do escopo

| Fora | Por quê |
| --- | --- |
| Logs escritos dentro do processor (`console.log`) | O Redis não guarda. Exige SDK Node (nível 2). |
| Etapas intermediárias de um job longo | Idem. |
| Ações de escrita (retry, promover, remover job) | Leitura primeiro. Escrita muda o risco do produto. |
| Anexos (RN-04) e API Key (RN-07) | Independentes deste escopo. |

**Exceção parcial:** se a aplicação já usa o `job.log()` nativo do BullMQ, essas mensagens **estão** no Redis (`bull:<fila>:<id>:logs`) e o nível 1 consegue lê-las. É o único caminho para log interno sem SDK.

---

## O que já existe e será reaproveitado

| Já pronto | Onde | Como entra no nível 1 |
| --- | --- | --- |
| Modelo `Job` | [src/flowlog/server/database/models/jobs.py](../src/flowlog/server/database/models/jobs.py) | Recebe campos novos (ver Etapa 2) |
| Modelo `JobLog` | [src/flowlog/server/database/models/job_logs.py](../src/flowlog/server/database/models/job_logs.py) | Recebe os `job.log()` do BullMQ |
| Paginação + filtro de logs | [src/flowlog/services/job_service.py](../src/flowlog/services/job_service.py) | Reaproveitada na tela de detalhe |
| Exception handlers | [src/flowlog/routes/error_routes.py](../src/flowlog/routes/error_routes.py) | Sem mudança |
| Entrypoint `flowlog` | `pyproject.toml` → `flowlog:main` | Vira o CLI (Etapa 5) |

---

## Esquema de chaves do BullMQ

Base do nível 1 inteiro. Prefixo padrão `bull`, configurável no BullMQ.

### Chaves da fila

| Chave | Tipo | Conteúdo |
| --- | --- | --- |
| `bull:<fila>:meta` | hash | Metadados da fila. **Serve para descobrir filas via `SCAN MATCH bull:*:meta`** |
| `bull:<fila>:id` | string | Contador do último ID gerado |
| `bull:<fila>:wait` | list | IDs aguardando processamento |
| `bull:<fila>:active` | list | IDs sendo processados agora |
| `bull:<fila>:delayed` | zset | IDs agendados (score = timestamp de liberação) |
| `bull:<fila>:completed` | zset | IDs concluídos (score = `finishedOn`) |
| `bull:<fila>:failed` | zset | IDs que falharam definitivamente |
| `bull:<fila>:paused` | list | Presente quando a fila está pausada |
| `bull:<fila>:events` | stream | Eventos: `added`, `waiting`, `active`, `completed`, `failed`, `progress`, `stalled` |

### Chaves do job

| Chave | Tipo | Conteúdo |
| --- | --- | --- |
| `bull:<fila>:<id>` | hash | O job em si (campos abaixo) |
| `bull:<fila>:<id>:lock` | string com TTL | Token do worker que segurou o job |
| `bull:<fila>:<id>:logs` | list | Mensagens do `job.log()` nativo |

### Campos do hash do job

| Campo | Observação |
| --- | --- |
| `name` | Nome do job (`queue.add('importar-extrato', ...)`) |
| `data` | **O payload.** String JSON |
| `opts` | String JSON: `attempts`, `backoff`, `delay`, `priority`, `removeOnComplete` |
| `timestamp` | Momento da enfileiração (ms epoch) |
| `processedOn` | Momento em que o worker pegou (ms epoch) |
| `finishedOn` | Momento da conclusão ou falha final (ms epoch) |
| `attemptsMade` | Tentativas já consumidas |
| `returnvalue` | Retorno do processor, JSON |
| `failedReason` | Mensagem do erro |
| `stacktrace` | Array JSON de stack traces, um por tentativa |

> **Validar no começo da Etapa 1:** o formato exato de `attemptsMade`, do valor de `:lock` (para extrair o ID do worker) e a presença de `prioritized` vs `priority` variam entre versões maiores do BullMQ. Fixe a versão do worker de teste e confirme contra ela antes de escrever o mapeamento.

---

## Etapas

### Etapa 0 — Ambiente de teste

Faça esta primeira. Sem ela, todas as outras são adivinhação.

- [ ] `docker-compose.yml` na raiz subindo um Redis
- [ ] `examples/worker/` com um projeto Node mínimo: `package.json`, uma `Queue` e um `Worker` BullMQ
- [ ] O worker precisa produzir os quatro cenários: job que conclui rápido, job lento, job que falha e refaz tentativas, job agendado com `delay`
- [ ] Um dos jobs usa `job.log()` e outro tem `apiToken` no payload, para exercitar a sanitização
- [ ] Anote a versão exata do `bullmq` no `package.json` — o mapeamento de campos depende dela

### Etapa 1 — Leitor do Redis

Camada isolada. Só lê Redis e devolve objetos tipados; não conhece o banco nem a API.

Novo pacote `src/flowlog/bullmq/`:

- [ ] `client.py` — conexão Redis assíncrona (`redis.asyncio`), reaproveitada por todo o app
- [ ] `keys.py` — construtores de chave, com o prefixo parametrizado
- [ ] `schemas.py` — modelos Pydantic `BullQueue` e `BullJob` que espelham os campos do hash, com `data` e `opts` já desserializados e timestamps já convertidos para `datetime`
- [ ] `reader.py` — as operações de leitura:
  - `discover_queues()` — `SCAN MATCH bull:*:meta`, extrai o nome da fila
  - `count_states(fila)` — tamanho de cada lista/zset
  - `list_job_ids(fila, estado, limite)` — `LRANGE` para listas, `ZREVRANGE` para zsets
  - `read_jobs(fila, ids)` — `HGETALL` em pipeline, nunca um `HGETALL` por job
  - `read_job_logs(fila, id)` — `LRANGE` da chave `:logs`

**Regras desta camada:**

- Use pipeline/`MGET` para tudo. Uma fila com 500 jobs não pode virar 500 round-trips.
- **Nunca use `KEYS`.** Só `SCAN` com `COUNT`, para não travar o Redis do usuário.
- Conexão somente-leitura na prática: nenhum comando de escrita nesta camada.

**Critério de aceite:** um teste roda contra o Redis da Etapa 0 e imprime payload, estado e stack trace de um job real, sem nenhuma biblioteca de BullMQ envolvida.

### Etapa 2 — Adaptar o modelo de domínio

O modelo atual nasceu para a ingestão HTTP e não acomoda um job de fila. Lacunas:

| Lacuna | Hoje | Precisa |
| --- | --- | --- |
| Origem do job | Não existe | `source: API \| BULLMQ` |
| Identidade externa | Só UUID interno | `queue_name` + `external_id` (o ID numérico do BullMQ) |
| Nome do job | `job_type` é um enum fechado (`ETL`, `EXPORT`, …) | Nome livre vindo do `name` do BullMQ |
| Estado `PENDING` | Ausente do enum `JobStatus`, apesar da RN-02 citar | Adicionar, para mapear `wait` |
| Tentativas | Não existe | `attempts_made`, `max_attempts` |
| Worker | Não existe | `worker_id` |
| Payload | Não existe (só `metadata` no log) | `payload: dict` sanitizado |

- [ ] Estender `Job` com os campos acima, todos opcionais para não quebrar a ingestão HTTP
- [ ] Adicionar `PENDING` ao `JobStatus` e definir o mapeamento de estados:

  | BullMQ | FlowLog |
  | --- | --- |
  | `wait`, `delayed`, `paused` | `PENDING` |
  | `active` | `RUNNING` |
  | `completed` | `SUCCESS` |
  | `failed` | `FAILED` |

- [ ] Constraint de unicidade em `(source, queue_name, external_id)` — é o que torna a sincronização idempotente
- [ ] **Decidir a estratégia de migração.** `SQLModel.metadata.create_all()` cria tabelas, mas não altera as que já existem. Ou o `flowlog.db` é apagado a cada mudança de schema, ou entra Alembic. Escolha antes de mexer no modelo.

**Cuidado com a RN-02:** a transição rígida foi escrita para a ingestão HTTP, onde a aplicação controla o fluxo. Um job sincronizado do Redis pode ser lido pela primeira vez já em `failed`, e um job com `retry` volta de `active` para `wait`. A regra precisa valer para jobs de origem `API` e não bloquear os de origem `BULLMQ` — deixe isso explícito no código.

### Etapa 3 — Sincronizador

`src/flowlog/sync/poller.py`. Loop assíncrono que traduz o que o leitor devolve para o banco.

- [ ] Loop com intervalo configurável (padrão sugerido: 1s), cancelável no shutdown
- [ ] Por ciclo, para cada fila: ler contadores, ler os IDs de `wait`/`active`/`delayed` por inteiro, e apenas os N mais recentes de `completed`/`failed`
- [ ] Upsert por `(queue_name, external_id)`: insere o que é novo, atualiza estado/tentativas/duração do que mudou
- [ ] Ingerir `bull:<fila>:<id>:logs` como `JobLog`, sem duplicar o que já foi gravado
- [ ] **Aplicar a RN-05 ao `data` do job antes de persistir.** O payload da fila é exatamente onde aparecem token e senha. Extraia o mascaramento para uma função reaproveitável — hoje ele está pensado só para `metadata`.
- [ ] Limitar o tamanho do payload persistido (payloads de MBs existem); truncar com marca explícita

**Critério de aceite:** com o worker da Etapa 0 rodando, o `flowlog.db` reflete o estado das filas em menos de 2 segundos, e rodar o poller duas vezes seguidas não duplica nenhuma linha.

**Possível otimização, não obrigatória:** consumir o stream `bull:<fila>:events` via `XREAD BLOCK` em vez de varrer as filas a cada ciclo. Reduz carga e latência, mas exige tratar reconexão e lacunas no stream. Só vale depois do polling funcionar.

### Etapa 4 — API de leitura

Novo router, irmão de `jobs_router`:

- [ ] `GET /api/v1/queues` — filas com contadores por estado
- [ ] `GET /api/v1/queues/{fila}/jobs` — paginado, filtros por `state` e `search` no nome
- [ ] `GET /api/v1/queues/{fila}/jobs/{external_id}` — detalhe com payload, `opts`, tentativas e stack trace
- [ ] `GET /api/v1/stream` — SSE emitindo as mudanças que o poller detectou

A paginação já existe em `get_logs_by_job_id`; siga o mesmo formato de resposta (`items`, `total`, `page`, `page_size`, `total_pages`).

### Etapa 5 — CLI `flowlog watch`

Hoje `src/flowlog/__init__.py` só tem um `print`. Ele vira o CLI.

- [ ] Adicionar `typer` e implementar `flowlog watch`
- [ ] Flags: `--redis`, `--prefix` (padrão `bull`), `--port` (padrão 4700), `--interval`, `--no-open`
- [ ] Configuração tipada com `pydantic-settings`, lendo `.env` — é o item 4 da lista de conceitos do README, ainda pendente
- [ ] Subir uvicorn programaticamente e o poller no `lifespan` do FastAPI, na mesma event loop
- [ ] Na saída esperada: Redis conectado, filas descobertas, URL do dashboard
- [ ] Abrir o navegador com `webbrowser.open`, respeitando `--no-open`
- [ ] Erro de conexão com o Redis precisa dizer o que fazer, não despejar traceback

### Etapa 6 — Dashboard

- [ ] Arquivos estáticos servidos pelo próprio FastAPI (`StaticFiles`), sem build step
- [ ] Três painéis: filas à esquerda, jobs no centro, detalhe do job selecionado à direita
- [ ] Consumir o SSE da Etapa 4; sem recarregar a página
- [ ] Estado codificado em cor **e** forma, para não depender só de cor
- [ ] Payload com JSON legível e o `***MASKED***` visível onde houve sanitização

Referência visual: o artifact da proposta, com o mockup dos três painéis.

---

## Ordem sugerida

```
Etapa 0 ──► Etapa 1 ──► Etapa 2 ──► Etapa 3 ──► Etapa 4 ──► Etapa 6
                                                    └──────► Etapa 5
```

As etapas 0 e 1 respondem todas as perguntas em aberto sobre o Redis. Se algo lá não funcionar como descrito, o resto do plano muda — por isso elas vêm antes de qualquer alteração no modelo.

---

## Decisões a tomar antes de começar

1. **Migração de schema.** Apagar o `flowlog.db` a cada mudança, ou adotar Alembic?
2. **Retenção.** Quantos jobs concluídos manter por fila? Sem limite, o `flowlog.db` cresce sem controle.
3. **Autenticação (RN-07).** O dashboard local exige `X-API-Key`? Se exigir, o CLI precisa gerar e injetar a chave.
4. **Múltiplos Redis.** Uma instância por execução, ou vários `--redis` de uma vez?
