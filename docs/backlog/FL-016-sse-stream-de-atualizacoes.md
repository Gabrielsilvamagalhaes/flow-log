# FL-016 — `GET /api/v1/stream`: SSE das mudanças do poller

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Média
**Áreas:** Backend, API
**Estimativa:** 1 dia
**Depende de:** `FL-012`

---

## Motivação

Sem SSE, o dashboard vira polling em cima de polling: o navegador bate na API a cada segundo perguntando o que o poller já sabe. O item 5 da entrega do nível 1 é o dashboard atualizar sem recarregar a página.

---

## Comportamento esperado

- [ ] O poller publica as mudanças do ciclo (item 5 de `FL-012`) em um broadcaster em memória
- [ ] O endpoint devolve `text/event-stream` consumindo esse broadcaster
- [ ] Tipos de evento: `queue_counts` (contadores mudaram) e `job_updated` (job entrou ou mudou de estado)
- [ ] Payload do evento é enxuto: identidade do job e os campos que mudaram, não o job inteiro com payload
- [ ] Heartbeat (comentário SSE) a cada ~15s, para proxy não derrubar a conexão ociosa
- [ ] Cliente que desconecta é removido; fila por cliente é limitada e descarta evento antigo em vez de crescer sem limite
- [ ] Nenhum cliente conectado não pode travar o poller

---

## Escopo

- [ ] `src/flowlog/sync/broadcaster.py` — pub/sub em memória com `asyncio.Queue` por assinante
- [ ] Endpoint `GET /api/v1/stream` com `StreamingResponse`
- [ ] Filtro opcional por fila via query string

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Broadcaster | `src/flowlog/sync/broadcaster.py` (novo) |
| Rota | `src/flowlog/routes/queue_routes.py` |
| Poller | `src/flowlog/sync/job_sync.py` |

---

## Critérios de aceite

- [ ] `curl -N http://localhost:4700/api/v1/stream` imprime evento quando um job de `FL-002` muda de estado
- [ ] Duas abas conectadas recebem os mesmos eventos
- [ ] Fechar o cliente não deixa task nem fila órfã (checar com `asyncio.all_tasks()`)
- [ ] Poller mantém o ritmo com zero clientes conectados

---

## Fora de escopo

- WebSocket — SSE basta para fluxo unidirecional
- Replay de eventos perdidos durante desconexão; o cliente recarrega o estado via `FL-014`/`FL-015`
