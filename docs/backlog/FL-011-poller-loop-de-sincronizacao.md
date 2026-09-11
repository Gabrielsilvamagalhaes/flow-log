# FL-011 — Poller: loop de sincronização

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend
**Estimativa:** 1,5 dia
**Depende de:** `FL-006`, `FL-007`

---

## Motivação

Etapa 3: o laço que roda continuamente traduzindo o que o leitor devolve. É o que faz o dashboard parecer "ao vivo" sem a aplicação Node saber que o FlowLog existe.

O ponto de atenção é carga: varrer `completed` inteiro a cada segundo, numa fila com 200 mil jobs concluídos, é um problema para o Redis do usuário.

---

## Escopo

- [ ] `src/flowlog/sync/poller.py` com um loop `asyncio` de intervalo configurável (default 1s)
- [ ] Cancelável: trata `asyncio.CancelledError` e encerra limpo no shutdown do FastAPI
- [ ] Por ciclo, para cada fila descoberta:
  - [ ] `count_states()` — contadores de todos os estados
  - [ ] IDs de `wait`, `active` e `delayed` por inteiro (estados vivos e pequenos)
  - [ ] Apenas os N mais recentes de `completed` e `failed` (N = retenção decidida em `FL-000`)
- [ ] Redescobrir filas periodicamente, não só na inicialização — fila nova aparece sem restart
- [ ] Erro em uma fila não derruba o ciclo das outras: loga e segue
- [ ] Reconexão com backoff se o Redis cair, sem encerrar o processo
- [ ] Log de debug por ciclo: filas lidas, jobs lidos, duração do ciclo

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Poller | `src/flowlog/sync/poller.py` (novo) |
| Leitor | `src/flowlog/bullmq/reader.py` (de `FL-006`) |

---

## Critérios de aceite

- [ ] Com o worker de `FL-002` rodando, o ciclo completo leva menos de 2 segundos
- [ ] Parar o Redis com `docker compose stop redis` não mata o processo; ao voltar, o poller volta a sincronizar sozinho
- [ ] Encerrar com Ctrl+C não deixa traceback de task pendente

---

## Fora de escopo

- Consumir `bull:<fila>:events` via `XREAD BLOCK` — otimização só depois do polling funcionar
- O upsert em si (é `FL-012`)
