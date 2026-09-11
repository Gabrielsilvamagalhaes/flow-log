# FL-007 — Estender o modelo `Job` para jobs de fila

**Tipo:** `refactor`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend, Banco
**Estimativa:** 1 dia
**Depende de:** `FL-000` (decisão de migração), `FL-003`

---

## Estado atual

`Job` nasceu para a ingestão HTTP e não acomoda um job vindo de fila — `src/flowlog/server/database/models/jobs.py:10`:

```python
class Job(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    job_type: Jobtypes          # enum fechado: ETL, EXPORT, NOTIFICATION, CLEANUP
    environment: Environment
    status: JobStatus           # sem PENDING
    client_identifier: str
    started_at: datetime
    ended_at: Optional[datetime]
    summary: Optional[str]
```

| Lacuna | Hoje | Precisa |
| --- | --- | --- |
| Origem | Não existe | `source: API \| BULLMQ` |
| Identidade externa | Só UUID interno | `queue_name` + `external_id` |
| Nome do job | `job_type` é enum fechado (`src/flowlog/shared/enums/job_enums.py:4`) | Nome livre vindo do `name` do BullMQ |
| Estado `PENDING` | Ausente do `JobStatus` (`job_enums.py:11`) | Adicionar para mapear `wait` |
| Tentativas | Não existe | `attempts_made`, `max_attempts` |
| Worker | Não existe | `worker_id` |
| Payload | Não existe (só `metadata_info` em `JobLog`) | `payload: dict` sanitizado |

---

## Estado desejado

- [ ] Campos novos em `Job`, **todos opcionais**, para não quebrar a ingestão HTTP existente (`create_job` em `src/flowlog/services/job_service.py:18`):
  - [ ] `source: JobSource` com default `API`
  - [ ] `queue_name: str | None`
  - [ ] `external_id: str | None`
  - [ ] `job_name: str | None` (nome livre; `job_type` continua existindo para a origem `API`)
  - [ ] `attempts_made: int | None`, `max_attempts: int | None`
  - [ ] `worker_id: str | None`
  - [ ] `payload: dict | None` com `sa_column=Column(JSON)`, mesmo padrão de `JobLog.metadata_info` (`job_logs.py:20`)
  - [ ] `failed_reason: str | None`, `stack_trace: str | None`
- [ ] `job_type` passa a ser opcional (job de fila não tem um dos 4 tipos do enum)
- [ ] `PENDING` adicionado a `JobStatus`
- [ ] Função de mapeamento de estados, com teste:

  | BullMQ | FlowLog |
  | --- | --- |
  | `wait`, `delayed`, `paused` | `PENDING` |
  | `active` | `RUNNING` |
  | `completed` | `SUCCESS` |
  | `failed` | `FAILED` |

- [ ] Aplicar a estratégia de migração decidida em `FL-000` (`SQLModel.metadata.create_all()` em `src/flowlog/server/server.py:9` **não** altera tabela existente)

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Modelo | `src/flowlog/server/database/models/jobs.py` |
| Enums | `src/flowlog/shared/enums/job_enums.py` |
| Mapeamento | `src/flowlog/bullmq/state_mapping.py` (novo) |
| Bootstrap | `src/flowlog/server/server.py:9` |

---

## Critérios de aceite

- [ ] `POST /jobs` da ingestão HTTP continua funcionando sem enviar nenhum campo novo
- [ ] Teste do mapeamento cobre os 6 estados BullMQ
- [ ] Banco existente migra (ou é recriado) conforme a decisão de `FL-000`, documentado no `README.md`

---

## Fora de escopo

- Unicidade e idempotência (é `FL-008`)
- Flexibilizar a RN-02 (é `FL-009`)
