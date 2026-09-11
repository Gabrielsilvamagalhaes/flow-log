# FL-014 — `GET /api/v1/queues`: filas com contadores

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend, API
**Estimativa:** 0,5 dia
**Depende de:** `FL-012`

---

## Motivação

Primeiro endpoint da Etapa 4 e fonte do painel esquerdo do dashboard (`FL-018`). Sem ele, a tela não tem por onde começar.

---

## Comportamento esperado

`GET /api/v1/queues` devolve, por fila: nome, se está pausada, e contadores por estado.

```json
{
  "items": [
    {
      "name": "importacoes",
      "paused": false,
      "counts": { "pending": 12, "running": 2, "success": 340, "failed": 3 },
      "last_activity_at": "2026-09-11T10:32:00"
    }
  ]
}
```

- [ ] Contadores lidos do banco (o que o poller sincronizou), com os contadores vivos do Redis quando divergirem — definir e documentar qual é a fonte de verdade de cada campo
- [ ] Ordenação default: filas com job em `RUNNING`/`FAILED` primeiro

---

## Escopo

- [ ] `src/flowlog/routes/queue_routes.py` com `queues_router`, irmão de `jobs_router` (`src/flowlog/routes/job_routes.py:49`)
- [ ] Registrar no `main_router` (`src/flowlog/routes/main_routes.py`)
- [ ] Service correspondente em `src/flowlog/services/queue_service.py`
- [ ] DTO de resposta em `src/flowlog/dto/`, seguindo o padrão dos DTOs existentes
- [ ] Tag própria em `src/flowlog/tags/`

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Rota | `src/flowlog/routes/queue_routes.py` (novo) |
| Service | `src/flowlog/services/queue_service.py` (novo) |
| DTO | `src/flowlog/dto/queue_dto.py` (novo) |

---

## Critérios de aceite

- [ ] Com as filas de `FL-002` populadas, o endpoint lista todas com contadores corretos
- [ ] Fila pausada aparece com `paused: true`
- [ ] Aparece no `/docs` do FastAPI com schema de resposta

---

## Fora de escopo

- Ação de pausar ou retomar fila — nível 1 é somente leitura
