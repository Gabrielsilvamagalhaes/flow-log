# FL-013 — Ingerir `job.log()` nativo como `JobLog`

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Média
**Áreas:** Backend
**Estimativa:** 0,5 dia
**Depende de:** `FL-012`

---

## Motivação

`console.log` dentro do processor não está no Redis e é escopo do nível 2. Mas se a aplicação já usa o `job.log()` nativo do BullMQ, as mensagens estão em `bull:<fila>:<id>:logs` — é o único caminho para log interno sem SDK, e sai quase de graça no nível 1.

---

## Comportamento esperado

- A lista `:logs` é append-only e sem timestamp por item. O índice da lista é a chave de deduplicação: se já ingeri até o índice K, na próxima leitura ingiro de K+1 em diante.
- `level` vira `INFO` — o `job.log()` nativo não tem nível.
- `JobLog.message` tem `max_length=2000` e `min_length=5` (`src/flowlog/server/database/models/job_logs.py:11`): mensagem maior é truncada e mensagem curta demais precisa de tratamento, não de exceção.

---

## Escopo

- [ ] Ler `bull:<fila>:<id>:logs` dos jobs vivos e dos recém-concluídos
- [ ] Guardar o índice já ingerido por job (campo `logs_ingested_count` em `Job`) e usar `LRANGE <inicio> -1`
- [ ] Gravar como `JobLog` ligado ao `job.id` interno
- [ ] Respeitar os limites de tamanho do modelo sem estourar validação
- [ ] Não reler `:logs` de job finalizado e já ingerido por completo

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Sync | `src/flowlog/sync/job_sync.py` |
| Modelo | `src/flowlog/server/database/models/job_logs.py` |
| Leitor | `src/flowlog/bullmq/reader.py` (`read_job_logs`) |

---

## Critérios de aceite

- [ ] Os 3 `job.log()` do `job-lento` de `FL-002` aparecem como `JobLog`, na ordem correta
- [ ] Dez ciclos do poller não duplicam nenhuma mensagem
- [ ] Mensagem de 5000 caracteres é truncada e não derruba o ciclo

---

## Fora de escopo

- `console.log` do processor — nível 2, exige SDK Node
- Inferir `level` a partir do texto da mensagem
