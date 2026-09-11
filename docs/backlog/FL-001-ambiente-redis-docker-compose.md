# FL-001 — Redis de desenvolvimento via docker-compose

**Tipo:** `build`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Infra
**Estimativa:** 0,5 dia
**Depende de:** Nenhuma

---

## Contexto

Todo o nível 1 depende de ler chaves reais do BullMQ no Redis. Sem um Redis local reprodutível, os tickets seguintes viram adivinhação sobre o formato dos campos.

Etapa 0 do plano ([docs/nivel-1-bullmq.md](../docs/nivel-1-bullmq.md)).

---

## Escopo

- [ ] `docker-compose.yml` na raiz subindo `redis:7-alpine` (fixar a tag, sem `latest`)
- [ ] Porta `6379` exposta; volume nomeado opcional para o dado sobreviver ao `down`
- [ ] Healthcheck com `redis-cli ping`
- [ ] Seção no `README.md` com `docker compose up -d` e como limpar (`FLUSHALL`)

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Infra | `docker-compose.yml` (novo) |
| Docs | `README.md` |

---

## Critérios de aceite

- [ ] `docker compose up -d` sobe o Redis e o healthcheck fica `healthy`
- [ ] `redis-cli -h localhost ping` responde `PONG`

---

## Fora de escopo

- Redis em produção, cluster, sentinel, TLS
