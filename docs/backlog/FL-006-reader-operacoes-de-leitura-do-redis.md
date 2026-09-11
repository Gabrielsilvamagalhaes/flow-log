# FL-006 — `reader.py`: operações de leitura do Redis

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend
**Estimativa:** 1,5 dia
**Depende de:** `FL-004`, `FL-005`

---

## Motivação

Coração da Etapa 1: a camada que sabe falar BullMQ. Ela só lê Redis e devolve objetos tipados — não conhece o banco, nem a API, nem o poller. Isso é o que permite testá-la contra o Redis de `FL-001` sem subir o FastAPI.

O risco aqui é de performance no Redis **do usuário**: uma implementação ingênua vira 500 round-trips por ciclo ou trava o servidor com `KEYS`.

---

## Escopo

- [ ] `src/flowlog/bullmq/reader.py` com:
  - [ ] `discover_queues()` — `SCAN MATCH bull:*:meta COUNT 100`, extrai o nome da fila
  - [ ] `count_states(fila)` — `LLEN`/`ZCARD` de cada estado em **um pipeline**, mais `EXISTS` do `:paused`
  - [ ] `list_job_ids(fila, estado, limite)` — `LRANGE` para listas, `ZREVRANGE` para zsets (mais recentes primeiro)
  - [ ] `read_jobs(fila, ids)` — `HGETALL` em pipeline, um round-trip para N jobs
  - [ ] `read_job_logs(fila, id)` — `LRANGE` de `bull:<fila>:<id>:logs`
- [ ] Todas as funções assíncronas, recebendo o client de `FL-004`
- [ ] Devolver `BullQueue`/`BullJob` de `FL-005`, nunca dicts crus

### Regras da camada

- [ ] **Nunca usar `KEYS`** — só `SCAN` com `COUNT`
- [ ] Pipeline/`MGET` para tudo; proibido um `HGETALL` por job em laço
- [ ] Nenhum comando de escrita nesta camada
- [ ] Job que sumiu entre o `LRANGE` e o `HGETALL` (hash vazio) é ignorado, não quebra

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Leitor | `src/flowlog/bullmq/reader.py` (novo) |

---

## Critérios de aceite

- [ ] Um teste roda contra o Redis de `FL-001` com o worker de `FL-002` e imprime payload, estado e stack trace de um job real — **sem nenhuma biblioteca de BullMQ envolvida**
- [ ] `discover_queues()` encontra as filas de `FL-002` sem arquivo de configuração
- [ ] Leitura de 100 jobs faz no máximo 2 round-trips (verificar com `MONITOR` ou contagem de chamadas)
- [ ] `grep -r "KEYS" src/flowlog/bullmq/` não retorna nada

---

## Fora de escopo

- Persistir qualquer coisa (é `FL-011`)
- Consumir o stream `bull:<fila>:events` (otimização pós-polling)
