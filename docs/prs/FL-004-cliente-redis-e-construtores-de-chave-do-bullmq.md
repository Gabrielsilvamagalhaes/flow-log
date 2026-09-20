# PR: Cliente Redis assíncrono e construtores de chave do BullMQ (FL-004)

**Tipo:** feat
**Escopo:** bullmq
**Branch:** `feat/ticket-04` → `main`
**Commits à frente:** 5 (`6719d3a`, `d95a3e3`, `a7476da`, `0eb6f58`, `b988224`)
**Repositório:** flowlog
**Vinculado a:** FL-004 — `docs/backlog/FL-004-cliente-redis-e-construtores-de-chave.md` · Linear [GAB-9](https://linear.app/gabriel-silva-magalhaes/issue/GAB-9) · depende de [[FL-001-redis-de-desenvolvimento-via-docker-compose]] · consome [[FL-003-validar-o-mapeamento-de-campos-contra-o-bullmq-real]]

---

## Resumo

A PR entrega a primeira fatia de código do pacote `src/flowlog/bullmq/`: a conexão com o Redis e a montagem das chaves do BullMQ. O `RedisClient` é um singleton assíncrono com `decode_responses=True`, criado sob demanda e validado por `ping()` antes de ser devolvido. O `BullMQKeys` concentra toda a construção de chave — `meta`, estado da fila, job, logs e lock — sobre um prefixo parametrizado, e faz o caminho inverso com `queue_name_from_meta_key()`, que tolera `:` no nome da fila. Os estados válidos saíram para o enum `QueueState`, que espelha o que o FL-003 observou no `bullmq@6.3.4`, incluindo o `prioritized`.

O motivo é o que está na motivação do FL-004: sem essa camada, todo ticket seguinte (`FL-005`, `FL-006`, `FL-011`) repetiria f-string de chave e abriria conexão solta. O prefixo `bull` é padrão mas configurável no BullMQ, então nunca pode ficar espalhado no código. A PR também traz a infraestrutura de teste que faltava no projeto — configuração do pytest, fixtures compartilhadas e um workflow de CI — porque o critério de aceite do ticket pede cobertura de `keys.py` sem depender de Redis real.

---

## O que foi alterado

### Backend
- `src/flowlog/bullmq/client.py` (novo) → `RedisClient`, singleton de classe sobre `redis.asyncio.client.Redis`. `get_client()` cria a instância na primeira chamada com `host="localhost"`, `port=6379` e `decode_responses=True`, dá `ping()` e levanta `ConnectionError` se a resposta for falsa. `close()` fecha o cliente e zera o singleton.
- `src/flowlog/bullmq/keys.py` (novo) → `BullMQKeys(prefix="bull")` com `meta_pattern()`, `queue_key()`, `job_key()`, `job_logs_key()`, `job_lock_key()`, `queue_name_from_meta_key()` e `verify_state()`. O `queue_name_from_meta_key()` corta o primeiro e o último segmento e rejunta o resto com `:`, o que preserva nomes de fila compostos; chave com menos de 3 segmentos vira `HTTPException` 400.
- `src/flowlog/shared/enums/queue_state.py` (novo) → `QueueState(StrEnum)` com `failed`, `completed`, `delayed`, `wait` e `prioritized`.
- `src/flowlog/routes/redis_routes.py` (novo) → router `/redis` com `GET /ping`, que pega o cliente, responde o resultado do `ping()` e exercita o `BullMQKeys` de ponta a ponta.
- `src/flowlog/routes/main_routes.py` → `redis_router` incluído no `main_router`, ficando sob `/api/v1`.
- `src/flowlog/routes/job_routes.py` → imports do `fastapi` unificados numa linha só e `JSONResponse` removido por não ser usado.
- `pyproject.toml` → `redis[hiredis]>=8.1.0` nas dependências de produção; grupo `dev` com `httpx`, `pytest` e `pytest-asyncio`; bloco `[tool.pytest.ini_options]` com `testpaths=["tests"]`, `pythonpath=["src"]` e `asyncio_mode="auto"`.
- `uv.lock` → resolução atualizada (57 pacotes) com `redis`, `hiredis` e as dependências de teste.

### Testes
- `tests/conftest.py` (novo) → troca o engine de produção por um SQLite em memória com `StaticPool` antes de qualquer import do `flowlog`, recria o schema a cada teste, e expõe as fixtures `session`, `client`, `make_job`, `make_job_log`, `finished_job` e `fake_redis` (que substitui `RedisClient._client` por um `AsyncMock`, mantendo a suíte sem Redis real).
- `tests/unit/bullmq/test_keys.py` (novo) → 13 testes cobrindo prefixo padrão e customizado, os cinco estados válidos do `queue_key()`, o `ValueError` do estado inválido, `meta_pattern()`, `job_key()`, `job_logs_key()`, `job_lock_key()` e a extração `bull:payments:retry:meta` → `payments:retry`.
- `tests/__init__.py`, `tests/unit/__init__.py`, `tests/unit/bullmq/__init__.py` (novos) → pacotes da suíte.

### CI
- `.github/workflows/tests.yml` (novo) → job `unit-tests` em `ubuntu-latest`, disparado em push e pull request contra `main` e por `workflow_dispatch`, com `concurrency` cancelando execuções antigas da mesma ref. Instala o `uv` (`astral-sh/setup-uv@v7`, cache no `uv.lock`), roda `uv sync --locked --all-extras --dev` e `uv run pytest tests/unit -v` numa matriz de Python 3.11 e 3.12.

### Docs
- `docs/backlog/FL-004-cliente-redis-e-construtores-de-chave.md` → **Status** de `A fazer` para `Feito`; escopo todo marcado; dos critérios de aceite, os dois de `keys.py` marcados e o do `ping()` deixado aberto com a nota de "a confirmar".
- `docs/prs/FL-004-cliente-redis-e-construtores-de-chave-do-bullmq.md` (este documento).

---

## Impacto na aplicação

### Para o usuário final / time que opera
| Antes | Depois |
| --- | --- |
| Nenhuma conexão com o Redis no código Python | `RedisClient.get_client()` devolve um cliente único, já validado por `ping()` |
| Chaves do BullMQ existiam só como tabela no `docs/bullmq-campos.md` | `BullMQKeys` monta e desmonta as chaves, com o prefixo parametrizado |
| Estados da fila como string solta | `QueueState` recusa estado inválido com `ValueError` na montagem da chave |
| Repositório sem suíte de testes nem `pytest` configurado | `uv run pytest` roda 13 testes em ~0,6s, sem Redis e sem banco externo |
| Nenhuma verificação automática em PR | Workflow do GitHub Actions roda a suíte em Python 3.11 e 3.12 a cada push e PR para `main` |

### Para a plataforma como um todo
- Destrava o `FL-005` e o `FL-006`: os schemas e o reader passam a ter de onde tirar conexão e chave, sem duplicar f-string.
- O `prefix` parametrizado no construtor deixa o `FL-017` (configuração tipada) plugar o valor vindo do settings sem tocar em quem chama.
- O `fake_redis` do `conftest.py` estabelece o padrão para os próximos tickets: teste unitário do pacote `bullmq` não sobe container.
- A CI fixa o contrato de dependências: `uv sync --locked` falha se o `uv.lock` sair de sincronia com o `pyproject.toml`.

### Limitações conhecidas
- `RedisClient` tem `host` e `port` hardcoded em `localhost:6379`. A parametrização é escopo do `FL-017`.
- `get_client()` dá `ping()` em toda chamada, inclusive nas que reaproveitam o singleton: é um round-trip a mais por uso.
- `Redis.close()` está deprecado em favor de `aclose()` nas versões recentes do `redis-py`.
- `meta_pattern(queue_name)` devolve a chave concreta `bull:<fila>:meta`, não o padrão `bull:*:meta` que o nome sugere e que o backlog do FL-004 descreve. O `SCAN` por filas do `FL-006` vai precisar de um construtor de padrão de verdade.
- `keys.py` levanta `HTTPException` (camada HTTP do FastAPI) dentro de um módulo de domínio, o que acopla a construção de chave ao framework web.
- `GET /api/v1/redis/ping` ainda é um endpoint de sondagem: tem dois `print()` de depuração e monta um `meta_key` que não é usado.
- O critério de aceite do `ping()` contra o Redis do `FL-001` não foi validado nesta PR — o container `redis-flowlog-service` não estava de pé.
- A CI roda só `tests/unit`; não há lint nem checagem de tipos no workflow.

---

## Arquivos principais do PR

```
flowlog/
├── .github/workflows/
│   └── tests.yml                                          (novo)
├── pyproject.toml                                         (redis + dev deps + pytest)
├── uv.lock                                                (resolução atualizada)
├── src/flowlog/
│   ├── bullmq/
│   │   ├── __init__.py                                    (novo)
│   │   ├── client.py                                      (novo)
│   │   └── keys.py                                        (novo)
│   ├── routes/
│   │   ├── redis_routes.py                                (novo)
│   │   ├── main_routes.py                                 (inclui redis_router)
│   │   └── job_routes.py                                  (imports)
│   └── shared/enums/
│       └── queue_state.py                                 (novo)
├── tests/
│   ├── conftest.py                                        (novo)
│   └── unit/bullmq/test_keys.py                           (novo)
└── docs/
    ├── backlog/FL-004-cliente-redis-e-construtores-de-chave.md  (status: Feito)
    └── prs/FL-004-cliente-redis-e-construtores-de-chave-do-bullmq.md
```

---

## Como testar

- [ ] `uv sync --all-extras --dev` instala as dependências novas sem erro.
- [ ] `uv lock --check` passa, confirmando que o `uv.lock` está em dia com o `pyproject.toml`.
- [ ] `uv run pytest tests/unit -v` devolve 13 testes passando, com o Redis **desligado** — a suíte não pode depender do container.
- [ ] `uv run python -c "from flowlog.bullmq.keys import BullMQKeys; print(BullMQKeys('prod').queue_key('test-queue','wait'))"` imprime `prod:test-queue:wait`, provando o prefixo parametrizado.
- [ ] `uv run python -c "from flowlog.bullmq.keys import BullMQKeys; print(BullMQKeys().queue_name_from_meta_key('bull:pagamentos:retry:meta'))"` imprime `pagamentos:retry`.
- [ ] Com `docker compose up -d` e o `redis-flowlog-service` `healthy`, subir a API e chamar `GET /api/v1/redis/ping`: resposta `{"message": true}`.
- [ ] Derrubar o Redis (`docker compose stop redis-flowlog-service`) e repetir a chamada: o endpoint deve falhar na conexão, não responder `true`.
- [ ] Abrir a PR e conferir que o workflow **Tests** roda os dois jobs da matriz (3.11 e 3.12) e fica verde.

---

## Comandos úteis

```bash
uv sync --all-extras --dev
uv lock --check
uv run pytest tests/unit -v
docker compose up -d
curl http://localhost:8000/api/v1/redis/ping
```

---

## Checklist

- [x] Documento cobre os 5 commits à frente de `origin/main`
- [x] Apenas arquivos verificados foram citados (nenhum path inventado)
- [x] Sessão "Como testar" tem passos reproduzíveis
- [x] Vinculado ao ticket/backlog correspondente (FL-004 / GAB-9)

## Tags

#bcx #pr #bullmq #feat
