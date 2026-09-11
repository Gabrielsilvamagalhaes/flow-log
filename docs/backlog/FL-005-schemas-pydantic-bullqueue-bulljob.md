# FL-005 — Schemas Pydantic `BullQueue` e `BullJob`

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend
**Estimativa:** 1 dia
**Depende de:** `FL-003`, `FL-004`

---

## Motivação

O `HGETALL` do BullMQ devolve um dict de strings: `data` e `opts` são JSON serializado, os timestamps são ms epoch, `attemptsMade` é texto. Deixar isso cru vazando para o poller e a API espalha `json.loads` e conversão de data por todo lado.

Este ticket concentra a tradução em um ponto só.

---

## Comportamento esperado

| Campo do hash | Tipo no schema | Regra |
| --- | --- | --- |
| `name` | `str` | vazio vira `"unknown"` |
| `data` | `dict \| list \| None` | `json.loads`; JSON inválido não derruba o parse (vira `{"_raw": "..."}`) |
| `opts` | `BullJobOpts` | `attempts`, `backoff`, `delay`, `priority`, `removeOnComplete` |
| `timestamp` | `datetime` | ms epoch → `datetime` |
| `processedOn` / `finishedOn` | `datetime \| None` | ms epoch → `datetime`; ausente = `None` |
| `attemptsMade` | `int` | default `0` |
| `returnvalue` | `Any \| None` | JSON tolerante |
| `failedReason` | `str \| None` | — |
| `stacktrace` | `list[str]` | array JSON; default `[]` |

Campos derivados no schema: `wait_time` (`processedOn - timestamp`) e `duration` (`finishedOn - processedOn`), ambos `None` quando faltar a ponta.

---

## Escopo

- [ ] `src/flowlog/bullmq/schemas.py` com `BullQueue` (nome, prefixo, contadores por estado, `paused: bool`) e `BullJob`
- [ ] Validators de campo para os quatro parses: JSON, ms epoch, int tolerante, array de stacktrace
- [ ] Campo `state: BullState` (`wait`, `active`, `delayed`, `paused`, `completed`, `failed`) preenchido por quem leu, não inferido do hash
- [ ] Parse resiliente: campo corrompido nunca derruba o ciclo do poller

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Schemas | `src/flowlog/bullmq/schemas.py` (novo) |
| Referência | `docs/bullmq-campos.md` (de `FL-003`) |

---

## Critérios de aceite

- [ ] Teste com os hashes reais capturados em `FL-003` (fixtures em JSON) produz `BullJob` válido nos 5 estados
- [ ] `data` com JSON inválido não levanta exceção
- [ ] `duration` de um job `completed` bate com `finishedOn - processedOn`

---

## Fora de escopo

- Sanitização do payload (é `FL-010`) — aqui o `data` ainda vem cru
