# FL-010 — Sanitização reaproveitável (RN-05) e limite de payload

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend, Segurança
**Estimativa:** 1 dia
**Depende de:** `FL-007`

---

## Motivação

A RN-05 hoje está pensada só para o `metadata` do log (`README.md:77`). O payload da fila é **exatamente** onde aparecem token e senha: um `queue.add` com `apiToken` no objeto entra inteiro no `bull:<fila>:<id>` e, sem tratamento, entra inteiro no `flowlog.db`.

Além disso, payloads de megabytes existem (base64 de PDF, dump de resposta). Persistir isso cru infla o banco e a resposta da API.

---

## Comportamento esperado

### Mascaramento

Chave contendo `password`, `token` ou `secret` (case-insensitive) tem o **valor** substituído por `***MASKED***`.

| Entrada | Saída |
| --- | --- |
| `{"apiToken": "abc123"}` | `{"apiToken": "***MASKED***"}` |
| `{"user": {"password": "x"}}` | `{"user": {"password": "***MASKED***"}}` |
| `{"items": [{"secretKey": "s"}]}` | `{"items": [{"secretKey": "***MASKED***"}]}` |
| `{"tokenCount": 42}` | `{"tokenCount": "***MASKED***"}` (a chave bate; mascarar mesmo assim) |

- [ ] Recursivo em dict e list, com profundidade limitada (proteção contra estrutura cíclica ou muito profunda)
- [ ] Lista de padrões configurável, com os três da RN-05 como default

### Truncagem

- [ ] Limite default de 64 KB por payload serializado, configurável
- [ ] Acima do limite, persistir `{"_truncated": true, "_original_size_bytes": N, "_preview": "<primeiros 2 KB>"}` — marca explícita, nunca silenciosa

---

## Escopo

- [ ] `src/flowlog/shared/utils/sanitize.py` com `sanitize_payload(dado)` e `truncate_payload(dado, limite)`
- [ ] Reapontar a sanitização de `metadata` do `JobLogValidator` (`src/flowlog/validators/job_log_validator.py:12`) para a mesma função — uma implementação só
- [ ] Testes de tabela cobrindo os casos acima, mais um payload de 1 MB

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Util | `src/flowlog/shared/utils/sanitize.py` (novo) |
| Validator | `src/flowlog/validators/job_log_validator.py` |

---

## Critérios de aceite

- [ ] O job com `apiToken` de `FL-002` chega ao banco com `***MASKED***`
- [ ] Nenhum valor sensível aparece em `SELECT payload FROM job`
- [ ] Payload de 1 MB é persistido truncado, com a marca `_truncated`
- [ ] Sanitização de `metadata` do log continua passando nos testes existentes

---

## Fora de escopo

- Criptografia de payload em repouso
- Flag para desligar a sanitização
