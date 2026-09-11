# FL-003 — Validar o mapeamento de campos contra o BullMQ real

**Tipo:** `docs`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend
**Estimativa:** 0,5 dia
**Depende de:** `FL-002`

---

## Contexto

O plano avisa: o formato de `attemptsMade`, o valor de `bull:<fila>:<id>:lock` (de onde sai o `worker_id`) e a presença de `prioritized` vs `priority` variam entre versões maiores do BullMQ. Escrever `schemas.py` (`FL-005`) antes de confirmar isso gera parsing quebrado em produção.

---

## Escopo

- [ ] Com o ambiente de `FL-002` rodando, capturar o `HGETALL` bruto de um job em cada estado (`wait`, `active`, `completed`, `failed`, `delayed`)
- [ ] Documentar em `docs/bullmq-campos.md`: nome do campo, tipo no Redis, exemplo real, tipo alvo em Python
- [ ] Confirmar o formato de `attemptsMade` (string numérica?), `stacktrace` (array JSON?), `timestamp`/`processedOn`/`finishedOn` (ms epoch)
- [ ] Confirmar o conteúdo do `:lock` e se dá para extrair um identificador de worker estável
- [ ] Confirmar se a versão usada grava `prioritized` (zset) e/ou `priority`
- [ ] Listar divergências entre o documentado em `docs/nivel-1-bullmq.md` e o observado

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Docs | `docs/bullmq-campos.md` (novo) |
| Docs | `docs/nivel-1-bullmq.md` (corrigir se divergir) |

---

## Critérios de aceite

- [ ] `docs/bullmq-campos.md` tem um exemplo real por estado, copiado do Redis
- [ ] Cada campo do hash tem tipo alvo definido em Python
- [ ] Divergências encontradas estão escritas, não só corrigidas em silêncio

---

## Fora de escopo

- Escrever o parser (é `FL-005`)
