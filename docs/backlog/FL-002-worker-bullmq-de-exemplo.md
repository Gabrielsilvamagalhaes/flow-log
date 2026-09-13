# FL-002 — Worker BullMQ de exemplo com os 4 cenários

**Tipo:** `build`
**Status:** Feito  
**Prioridade:** Alta
**Áreas:** Infra, Node
**Estimativa:** 1 dia
**Depende de:** `FL-001`

---

## Contexto

O leitor de Redis (`FL-003` a `FL-006`) precisa de dados reais para ser escrito e testado. Este ticket entrega um projeto Bun + TypeScript mínimo que produz, sob demanda, todos os estados que o nível 1 precisa mapear.

A versão exata do `bullmq` importa: o formato de `attemptsMade`, do `:lock` e a existência de `prioritized` vs `priority` mudam entre versões maiores.

---

## Escopo

- [x] `examples/bullmq-test/` com `package.json`, `Queue` e `Worker` BullMQ apontando para `redis://localhost:6379`
- [x] Quatro jobs cobrindo os cenários:
  - [ ] `job-rapido` — conclui em &lt; 1s (`completed`)
  - [ ] `job-lento` — `sleep` de ~30s, para observar `active` por tempo suficiente
  - [ ] `job-que-falha` — lança erro, `attempts: 3` + `backoff` exponencial (`failed` após as tentativas)
  - [ ] `job-agendado` — enfileirado com `delay` (`delayed`)
- [x] `job-lento` usa `job.log()` nativo pelo menos 3 vezes (única fonte de log interno sem SDK)
- [x] Um dos payloads carrega `apiToken` e `password`, para exercitar a sanitização de `FL-010`
- [x] Script `bun run seed` que enfileira os 4 jobs e `bun run start` que sobe o worker
- [x] `examples/bullmq-test/README.md` anotando a **versão exata** do `bullmq` usada

### Arquivos principais


| Camada      | Arquivo                                                  |
| ----------- | -------------------------------------------------------- |
| Fila (seed) | `examples/bullmq-test/src/init-job.ts` (novo)            |
| Worker      | `examples/bullmq-test/src/workers/test-worker.ts` (novo) |
| Entrypoint  | `examples/bullmq-test/index.ts` (novo)                   |
| Docs        | `examples/bullmq-test/README.md` (novo)                  |


---

## Decisões de implementação

Ajustes em relação ao escopo original, registrados durante a implementação:

- **Caminho e linguagem:** o exemplo fica em `examples/bullmq-test/` e é escrito em TypeScript, em vez de `examples/worker/` com `.js`. O seed (`Queue`) está em `src/init-job.ts`, o `Worker` em `src/workers/test-worker.ts` e o entrypoint é `index.ts`.
- **Nomes dos jobs:** os jobs usam nomes em inglês, definidos no enum `JobTypes` (`src/shared/enums/jobs-types.ts`): `job-rapido` → `quickly-job`, `job-lento` → `slowly-job`, `job-que-falha` → `error-job`, `job-agendado` → `delay-job`. Todos vão para a fila `test-queue`.
- **Runtime:** o projeto roda com **Bun** (`>= 1.3`), não com Node puro. Os scripts do `package.json` chamam `bun`, então `npm run seed` / `npm start` só funcionam com o Bun instalado. Os comandos oficiais são `bun run seed` e `bun run start`. O Bun também carrega o `.env` sozinho.
- **Impacto no FlowLog:** nenhum. O leitor de Redis consome as chaves `bull:*`, que dependem só da versão do `bullmq`, não do runtime nem da linguagem.

---

## Critérios de aceite

- [x] Com o worker parado, `bun run seed` deixa jobs em `wait` e `delayed`
- [x] Com o worker rodando, os 4 cenários chegam aos estados esperados
- [x] `redis-cli KEYS 'bull:*'` (só em dev, manualmente) mostra `:meta`, `:wait`, `:active`, `:completed`, `:failed`, `:delayed` e `:<id>:logs`
- [x] `README.md` do exemplo declara a versão do `bullmq`

---

## Fora de escopo

- Qualquer import do FlowLog dentro do worker — a aplicação Node não muda uma linha

