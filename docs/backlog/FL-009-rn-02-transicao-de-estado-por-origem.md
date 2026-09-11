# FL-009 — RN-02: transição rígida só para jobs de origem `API`

**Tipo:** `fix`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend
**Estimativa:** 0,5 dia
**Depende de:** `FL-007`

---

## Problema

A RN-02 (transição de estado rígida) foi escrita para a ingestão HTTP, onde a aplicação controla o fluxo: o job nasce `RUNNING` e termina uma vez. Hoje isso aparece, por exemplo, em `src/flowlog/services/job_service.py:36`, que bloqueia log em job já finalizado.

Um job sincronizado do Redis não obedece esse fluxo:

### Exemplo real

1. O FlowLog sobe depois do worker. A primeira leitura de um job já vem em `failed` — nunca passou por `RUNNING` no banco.
2. Um job com `attempts: 3` falha e volta de `active` para `wait` — ou seja, de `RUNNING` para `PENDING`, uma transição "para trás".
3. Um job `delayed` promovido vira `wait` e depois `active`.

Se a regra rígida valer para a origem `BULLMQ`, o poller começa a levantar erro no ciclo normal de retry.

---

## Comportamento esperado

| Origem | Regra |
| --- | --- |
| `API` | Transição rígida da RN-02 mantida como está hoje |
| `BULLMQ` | Estado espelha o Redis; qualquer transição é válida, inclusive regressão `RUNNING → PENDING` |

---

## Escopo

- [ ] Extrair a validação de transição para uma função única que recebe `source`
- [ ] Marcar no código, com comentário explícito, por que a origem `BULLMQ` é isenta
- [ ] Revisar `is_valid_finish_job_status` (`src/flowlog/shared/utils/is_valid_finish_job_status.py:18`) e o bloqueio de `create_job_log` para não afetarem jobs de fila
- [ ] Testes: retry (`RUNNING → PENDING → RUNNING → FAILED`) e primeira leitura já em `FAILED`

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Serviço | `src/flowlog/services/job_service.py:36` |
| Util | `src/flowlog/shared/utils/is_valid_finish_job_status.py` |

---

## Critérios de aceite

- [ ] Job `BULLMQ` aceita `RUNNING → PENDING` sem erro
- [ ] Job `API` continua rejeitando transição inválida (teste de regressão)
- [ ] Log em job `BULLMQ` finalizado é aceito (o Redis pode entregar o `:logs` depois do `finishedOn`)

---

## Fora de escopo

- Alterar a RN-02 no `README.md` sem alinhamento — a regra continua valendo para HTTP
