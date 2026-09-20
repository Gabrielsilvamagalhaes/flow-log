# FL-004 — Cliente Redis assíncrono e construtores de chave

**Tipo:** `feat`
**Status:** Feito
**Prioridade:** Alta
**Áreas:** Backend
**Estimativa:** 0,5 dia
**Depende de:** `FL-001`

---

## Motivação

Primeira fatia do pacote `src/flowlog/bullmq/`: a conexão e a montagem de chaves. Isolar isso permite que todo o resto (`FL-005`, `FL-006`) seja escrito sem repetir string de chave nem abrir conexão solta.

O prefixo `bull` é o padrão, mas é configurável no BullMQ — nunca pode ficar hardcoded no meio do código.

---

## Escopo

- [x] Adicionar `redis[hiredis]` às dependências em `pyproject.toml`
- [x] `src/flowlog/bullmq/__init__.py`
- [x] `src/flowlog/bullmq/client.py`:
  - [x] Fábrica de conexão `redis.asyncio` com pool, `decode_responses=True`
  - [x] Uma única instância reaproveitada pelo app (criada no lifespan em `FL-017`)
  - [x] `ping()` explícito para o CLI validar a conexão antes de subir
- [x] `src/flowlog/bullmq/keys.py` — construtores com prefixo parametrizado:
  - [x] `meta_pattern()` → `bull:*:meta`
  - [x] `queue_key(fila, estado)` → `bull:<fila>:<estado>`
  - [x] `job_key(fila, id)`, `job_logs_key(fila, id)`, `job_lock_key(fila, id)`
  - [x] `queue_name_from_meta_key(chave)` — extrai a fila, tolerando `:` no nome da fila

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Conexão | `src/flowlog/bullmq/client.py` (novo) |
| Chaves | `src/flowlog/bullmq/keys.py` (novo) |
| Deps | `pyproject.toml` |

---

## Critérios de aceite

- [x] Teste unitário de `keys.py` cobrindo prefixo padrão e prefixo customizado, sem Redis
- [x] `queue_name_from_meta_key("bull:pagamentos:retry:meta")` devolve `pagamentos:retry`
- [ ] `ping()` contra o Redis de `FL-001` responde `True` — a confirmar: exposto em `GET /api/v1/redis/ping`, ainda não validado contra o container de pé

---

## Fora de escopo

- Qualquer leitura de job (é `FL-006`)
- Comandos de escrita: esta camada é somente-leitura na prática
