# FL-008 — Unicidade `(source, queue_name, external_id)`

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend, Banco
**Estimativa:** 0,5 dia
**Depende de:** `FL-007`

---

## Motivação

O poller relê as mesmas filas a cada ciclo (padrão: 1s). Sem uma chave natural, cada ciclo insere linhas novas e o `flowlog.db` vira lixo em minutos.

`(source, queue_name, external_id)` é o que torna a sincronização idempotente: o poller faz upsert por essa tripla, não por UUID.

---

## Escopo

- [ ] `UniqueConstraint("source", "queue_name", "external_id")` em `Job` via `__table_args__`
- [ ] Índice composto `(queue_name, status)` — é o filtro da listagem de `FL-014`
- [ ] Índice em `(queue_name, external_id)` para o lookup do upsert
- [ ] A constraint não pode bloquear jobs de origem `API`, que têm `queue_name`/`external_id` nulos (validar o comportamento de `NULL` em UNIQUE no SQLite)
- [ ] Migração correspondente conforme `FL-000`

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Modelo | `src/flowlog/server/database/models/jobs.py` |

---

## Critérios de aceite

- [ ] Inserir duas vezes o mesmo `(BULLMQ, fila, id)` viola a constraint
- [ ] Inserir 10 jobs de origem `API` (com `queue_name`/`external_id` nulos) não viola nada
- [ ] `EXPLAIN QUERY PLAN` da listagem por fila + estado usa o índice

---

## Fora de escopo

- A lógica de upsert em si (é `FL-012`)
