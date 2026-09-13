# bullmq-test

Projeto mínimo que produz, sob demanda, os estados de job do BullMQ que o leitor de Redis do FlowLog precisa mapear (ticket `FL-002`).

> Nenhum código do FlowLog é importado aqui — o worker é uma aplicação Node/Bun comum.

## Versões

| Pacote | Versão |
| --- | --- |
| **`bullmq`** | **`6.3.4`** (exata, resolvida em `bun.lock`) |
| `ioredis` | `^6.0.0` |
| Bun | `1.3.14` |
| Redis | `7-alpine` (via `docker-compose.yml` da raiz) |

A versão do `bullmq` importa: o formato de `attemptsMade`, do `:lock` e a existência de `prioritized` vs `priority` mudam entre versões maiores.

## Pré-requisitos

- [Bun](https://bun.com) `>= 1.3`
- Redis rodando em `localhost:6379`. Na raiz do repositório:

```bash
docker compose up -d
```

## Configuração

```bash
bun install
cp .env.example .env
```

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `REDIS_HOST` | `localhost` | Host do Redis |
| `REDIS_PORT` | `6379` | Porta do Redis (numérica) |

Detalhes em [`.env.example`](./.env.example).

## Execução

| Comando | O que faz |
| --- | --- |
| `bun run seed` | Limpa a fila (`obliterate`) e enfileira os 4 jobs |
| `bun run start` | Sobe o worker (`concurrency: 4`) |

Para observar os jobs parados em `wait`/`delayed`, rode o `seed` **com o worker parado**; depois suba o worker.

## Cenários

Todos os jobs vão para a fila `test-queue`.

| Job | Opções | Estado esperado |
| --- | --- | --- |
| `quickly-job` | `removeOnComplete` | `completed` em < 1s. Payload carrega `api-token` e `db-password` (sanitização do `FL-010`) |
| `slowly-job` | `removeOnComplete` | `active` por ~30s, com `job.log()` |
| `error-job` | `attempts: 3`, `backoff: 5000` | `failed` após 3 tentativas |
| `delay-job` | `delay: 10000`, `removeOnComplete` | `delayed` por 10s, depois `completed` |

## Inspecionando o Redis (apenas dev)

```bash
docker compose exec redis-flowlog-service redis-cli KEYS 'bull:test-queue:*'
```

Chaves esperadas: `:meta`, `:wait`, `:active`, `:completed`, `:failed`, `:delayed` e `:<id>:logs`.

## Estrutura

```
index.ts                        # entrypoint do worker (npm start)
src/
  init-job.ts                   # seed: cria a Queue e enfileira os jobs
  server/config/redis.ts        # conexão IORedis a partir do .env
  service/clean-jobs.ts         # obliterate da fila
  shared/enums/jobs-types.ts    # nomes dos jobs
  shared/enums/queue-names.ts   # nomes das filas
  workers/test-worker.ts        # Worker e handlers de eventos
```
