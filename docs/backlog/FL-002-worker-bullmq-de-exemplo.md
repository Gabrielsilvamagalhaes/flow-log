# FL-002 — Worker BullMQ de exemplo com os 4 cenários

**Tipo:** `build`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Infra, Node
**Estimativa:** 1 dia
**Depende de:** `FL-001`

---

## Contexto

O leitor de Redis (`FL-003` a `FL-006`) precisa de dados reais para ser escrito e testado. Este ticket entrega um projeto Node mínimo que produz, sob demanda, todos os estados que o nível 1 precisa mapear.

A versão exata do `bullmq` importa: o formato de `attemptsMade`, do `:lock` e a existência de `prioritized` vs `priority` mudam entre versões maiores.

---

## Escopo

- [ ] `examples/worker/` com `package.json`, `Queue` e `Worker` BullMQ apontando para `redis://localhost:6379`
- [ ] Quatro jobs cobrindo os cenários:
  - [ ] `job-rapido` — conclui em < 1s (`completed`)
  - [ ] `job-lento` — `sleep` de ~30s, para observar `active` por tempo suficiente
  - [ ] `job-que-falha` — lança erro, `attempts: 3` + `backoff` exponencial (`failed` após as tentativas)
  - [ ] `job-agendado` — enfileirado com `delay` (`delayed`)
- [ ] `job-lento` usa `job.log()` nativo pelo menos 3 vezes (única fonte de log interno sem SDK)
- [ ] Um dos payloads carrega `apiToken` e `password`, para exercitar a sanitização de `FL-010`
- [ ] Script `npm run seed` que enfileira os 4 jobs e `npm start` que sobe o worker
- [ ] `examples/worker/README.md` anotando a **versão exata** do `bullmq` usada

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Fila | `examples/worker/src/queue.js` (novo) |
| Worker | `examples/worker/src/worker.js` (novo) |
| Docs | `examples/worker/README.md` (novo) |

---

## Critérios de aceite

- [ ] Com o worker parado, `npm run seed` deixa jobs em `wait` e `delayed`
- [ ] Com o worker rodando, os 4 cenários chegam aos estados esperados
- [ ] `redis-cli KEYS 'bull:*'` (só em dev, manualmente) mostra `:meta`, `:wait`, `:active`, `:completed`, `:failed`, `:delayed` e `:<id>:logs`
- [ ] `README.md` do exemplo declara a versão do `bullmq`

---

## Fora de escopo

- Qualquer import do FlowLog dentro do worker — a aplicação Node não muda uma linha
