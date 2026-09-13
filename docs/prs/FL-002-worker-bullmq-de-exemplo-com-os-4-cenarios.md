# PR: Worker BullMQ de exemplo com os 4 cenários de job (FL-002)

**Tipo:** feat
**Escopo:** bullmq-test
**Branch:** `feat/ticket-02` → `main`
**Commits à frente:** 12 (8 do FL-002 + 4 herdados de `config/ticket-01` / FL-001, ainda não mergeados em `origin/main`)
**Repositório:** flowlog
**Vinculado a:** FL-002 — `docs/backlog/FL-002-worker-bullmq-de-exemplo.md` · depende de [[FL-001-redis-de-desenvolvimento-via-docker-compose]]

---

## Resumo

A PR cria `examples/bullmq-test/`, um projeto mínimo em **Bun + TypeScript** com uma `Queue` e um `Worker` do BullMQ (`bullmq` fixado em `6.3.4`) apontando para o Redis de desenvolvimento do FL-001. Um script `seed` limpa a fila `test-queue` e enfileira 4 jobs que cobrem os estados que o leitor de Redis precisa mapear: `completed`, `active` (com `job.log()`), `failed` após retentativas e `delayed`. Um script `start` sobe o worker com `concurrency: 4`. A conexão com o Redis é configurável por `REDIS_HOST` / `REDIS_PORT`.

O motivo é o mesmo da Etapa 0 do nível 1: os tickets `FL-003` a `FL-006` precisam de chaves `bull:*` reais para serem escritos e testados, e o `FL-010` precisa de um payload com dados sensíveis para exercitar a sanitização. O backlog do FL-002 foi atualizado para registrar as decisões tomadas na implementação (caminho `examples/bullmq-test/`, TypeScript e runtime Bun em vez de Node/`.js`).

> **Atenção:** a branch foi criada a partir de `config/ticket-01`. Os commits `0452076`, `0ebcb87`, `4b95efb` e `9083770` (FL-001) aparecem no diff contra `origin/main` e já estão documentados em `docs/prs/FL-001-redis-de-desenvolvimento-via-docker-compose.md`. Este documento cobre só os commits do FL-002. Mergear a PR do FL-001 antes deixa o diff desta PR limpo.

---

## O que foi alterado

### Exemplo BullMQ (`examples/bullmq-test/`)
- `package.json` (novo) → scripts `seed` (`bun run ./src/init-job.ts`) e `start` (`bun index.ts`); dependências `bullmq` `6.3.4` (exata), `ioredis` `^6.0.0`, `@types/ioredis` `^5.0.0`; dev `@biomejs/biome` `2.5.13` e `@types/bun`.
- `bun.lock` (novo) → lockfile com as versões resolvidas.
- `tsconfig.json`, `biome.json`, `.gitignore` (novos) → tooling padrão de projeto Bun (strict, `noEmit`, formatter com tab e aspas duplas; `.env` ignorado).
- `.env.example` (novo) → `REDIS_HOST=localhost` e `REDIS_PORT=6379`, com comentários.
- `src/server/config/redis.ts:3` → `getRedisConfig()` lê `REDIS_PORT` / `REDIS_HOST` (padrões `6379` / `localhost`) e lança `"REDIS_PORT must be a number"` se a porta não for numérica; `src/server/config/redis.ts:15` exporta uma instância `IORedis` compartilhada com `maxRetriesPerRequest: null` (exigido pelo `Worker` do BullMQ).
- `src/shared/enums/jobs-types.ts` → enum `JobTypes`: `quickly-job`, `slowly-job`, `error-job`, `delay-job`.
- `src/shared/enums/queue-names.ts` → enum `QueueNames`: `test-queue`.
- `src/service/clean-jobs.ts:3` → `cleanAllJobsFromQueue()` chama `queue.obliterate({ force: true })`.
- `src/init-job.ts:13` → `initJobs()`: limpa a fila e enfileira os 4 jobs:
  - `quickly-job` com payload `{ message, apiToken, password }`;
  - `slowly-job`;
  - `error-job` com `attempts: 3` e `backoff: { type: "exponential", delay: 5000 }`;
  - `delay-job` com `delay: 10000`.
  Depois fecha a `Queue` e a conexão Redis.
- `src/workers/test-worker.ts:8` → `Worker` da `test-queue` com `autorun: false` e `concurrency: 4`. `slowly-job` grava 3 `job.log()` intercalados com `sleep` de 10s (~30s em `active`); `error-job` lança `Error("Job de erro")`; os demais concluem na hora. Handlers de `active`, `failed`, `completed` e `ready` logam no console (com `console.time` por job).
- `index.ts` → entrypoint: importa o `worker` e chama `worker.run()`.
- `README.md` (novo) → versões (bullmq `6.3.4`, Bun `1.3.14`, Redis `7-alpine`), pré-requisitos, configuração, comandos, tabela de cenários, inspeção via `redis-cli` e estrutura de pastas.

### Docs
- `docs/backlog/FL-002-worker-bullmq-de-exemplo.md` → contexto trocado de "projeto Node" para "Bun + TypeScript"; caminhos `examples/worker/*.js` substituídos por `examples/bullmq-test/*.ts`; comandos `npm run seed` / `npm start` viraram `bun run seed` / `bun run start`; nova seção **Decisões de implementação**. Checkboxes de escopo/critérios e o **Status** (`A fazer`) não foram alterados.

---

## Impacto na aplicação

### Para o usuário final / time que opera
| Antes | Depois |
| --- | --- |
| Não havia como gerar chaves `bull:*` reais no Redis local | `bun run seed` + `bun run start` produzem os estados `wait`, `delayed`, `active`, `completed` e `failed` sob demanda |
| Formato das chaves do BullMQ só por documentação/adivinhação | Versão exata do `bullmq` (`6.3.4`) fixada no `package.json` e declarada no README |
| Nenhum payload com dado sensível para testar sanitização | `quickly-job` carrega `apiToken` e `password` |
| — | `seed` sempre começa de fila zerada (`obliterate`), cenário reproduzível |

### Para a plataforma como um todo
- Destrava os tickets do leitor de Redis (`FL-003` a `FL-006`) e a sanitização (`FL-010`).
- Projeto isolado em `examples/`: nenhuma linha de código do FlowLog é importada ou alterada.
- Introduz Bun como pré-requisito **apenas** para rodar o exemplo.

### Limitações conhecidas
- Nenhum job usa `removeOnComplete`/`removeOnFail`: jobs concluídos e falhos se acumulam em `:completed` / `:failed` até o próximo `seed` (desejável para o leitor).
- `src/init-job.ts` guarda os retornos de `testQueue.add()` em constantes não usadas e mantém uma linha comentada (`// const connection = ...`).
- `@types/ioredis` `^5` em `dependencies` com `ioredis` `^6` — necessidade a confirmar.
- `seed` faz `obliterate({ force: true })` sem confirmação: apaga tudo da `test-queue`, inclusive jobs ativos.
- Checkboxes e **Status** do FL-002 continuam `A fazer`.

---

## Arquivos principais do PR

```
flowlog/
├── docs/backlog/
│   └── FL-002-worker-bullmq-de-exemplo.md     (decisões de implementação)
└── examples/bullmq-test/                      (novo)
    ├── .env.example
    ├── README.md
    ├── package.json · bun.lock · tsconfig.json · biome.json
    ├── index.ts                               (entrypoint do worker)
    └── src/
        ├── init-job.ts                        (seed dos 4 jobs)
        ├── server/config/redis.ts             (conexão IORedis)
        ├── service/clean-jobs.ts              (obliterate)
        ├── shared/enums/jobs-types.ts
        ├── shared/enums/queue-names.ts
        └── workers/test-worker.ts             (Worker + eventos)
```

---

## Como testar

- [ ] Na raiz do repo, `docker compose up -d`. `docker compose ps` mostra `redis-flowlog-service` `healthy`.
- [ ] Em `examples/bullmq-test/`, rodar `bun install` e `cp .env.example .env`. Instala sem erro.
- [ ] Com o worker **parado**, rodar `bun run seed`. Console mostra `All jobs been removed` e `Jobs iniciados com sucesso!`.
- [ ] `docker compose exec redis-flowlog-service redis-cli LLEN bull:test-queue:wait` retorna `3` e `ZCARD bull:test-queue:delayed` retorna `1`.
- [ ] Rodar `bun run start`. Console mostra `Worker pronto para processar jobs.` e `quickly-job` concluído em < 1s.
- [ ] Durante ~30s, `redis-cli LLEN bull:test-queue:active` ≥ `1` (o `slowly-job`); `redis-cli LRANGE bull:test-queue:<id-do-slowly-job>:logs 0 -1` mostra as 3 etapas.
- [ ] Após ~10s, `delay-job` sai de `delayed` e conclui.
- [ ] `error-job` loga falha nas tentativas 1, 2 e 3 (espera exponencial de 5s e 10s entre elas); ao final `redis-cli ZCARD bull:test-queue:failed` retorna `1`.
- [ ] `redis-cli KEYS 'bull:test-queue:*'` mostra `:meta`, `:completed`, `:failed` e `:<id>:logs` (`:wait`, `:active`, `:delayed` só enquanto houver jobs nesses estados).
- [ ] Rodar `REDIS_PORT=abc bun run seed`. Falha com `REDIS_PORT must be a number`.
- [ ] Rodar `bun run seed` de novo com o worker parado. Fila volta a ter só os 4 jobs novos (obliterate).

---

## Comandos úteis

```bash
docker compose up -d
cd examples/bullmq-test
bun install
cp .env.example .env
bun run seed
bun run start
docker compose exec redis-flowlog-service redis-cli KEYS 'bull:test-queue:*'
docker compose exec redis-flowlog-service redis-cli ZRANGE bull:test-queue:failed 0 -1
bunx biome check .
```

---

## Checklist

- [x] Documento cobre todos os commits do FL-002 à frente de `origin/main` (`7ed168b`, `f27fadd`, `480c097`, `a08e3a4`, `24d274e`, `d7afba6`, `0d661ae`, `87cef39`); commits do FL-001 referenciados ao doc próprio
- [x] Apenas arquivos verificados foram citados (nenhum path inventado)
- [x] Sessão "Como testar" tem passos reproduzíveis
- [x] Vinculado ao ticket/backlog correspondente (FL-002)

## Tags

#bcx #pr #bullmq-test #feat
