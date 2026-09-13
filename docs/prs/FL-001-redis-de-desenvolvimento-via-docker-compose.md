# PR: Redis de desenvolvimento via docker compose no FlowLog (FL-001)

**Tipo:** feat
**Escopo:** infra
**Branch:** `config/ticket-01` → `main`
**Commits à frente:** 3
**Repositório:** flowlog
**Vinculado a:** FL-001 — `docs/backlog/FL-001-ambiente-redis-docker-compose.md`

---

## Resumo

A PR adiciona um `docker-compose.yml` na raiz do FlowLog que sobe um Redis local (`redis:7-alpine`) com persistência AOF, volume nomeado e healthcheck. O `README.md` ganhou uma seção explicando como subir, testar a conexão e limpar esse Redis. No ticket FL-001, os checkboxes de escopo e os critérios de aceite foram marcados.

O motivo é a Etapa 0 do plano de integração com BullMQ (nível 1): os próximos tickets precisam ler chaves reais que o BullMQ grava no Redis. Sem um Redis local reprodutível, o formato desses campos fica na adivinhação. Agora qualquer pessoa do time sobe o mesmo ambiente com um comando.

---

## O que foi alterado

### Infra
- `docker-compose.yml` (novo) → serviço `redis-flowlog-service` com imagem `redis:7-alpine` (tag fixa), porta `6379:6379`, volume `redis-data:/data`, `command: redis-server --appendonly yes`, healthcheck `redis-cli ping` (interval 10s, timeout 5s, retries 3, start_period 10s) e `restart: unless-stopped`.

### Docs
- `README.md:69` → nova seção **🐳 Redis de desenvolvimento**, com subsections *Subir* (`docker compose up -d`, `docker compose ps`, `ping` pelo host ou pelo container) e *Limpar* (`FLUSHALL`, `docker compose down`, `docker compose down -v`).
- `docs/backlog/FL-001-ambiente-redis-docker-compose.md` → os 4 itens de escopo e os 2 critérios de aceite marcados como `[x]`; a tabela "Arquivos principais" foi reformatada (alinhamento de colunas). O campo **Status** continua `A fazer` no commit.

---

## Impacto na aplicação

### Para o usuário final / time que opera
| Antes | Depois |
| --- | --- |
| Não havia Redis padronizado no projeto; cada dev precisava instalar ou subir o seu | `docker compose up -d` sobe um Redis 7 idêntico para todos |
| Nenhuma forma documentada de checar se o Redis está saudável | Healthcheck do compose + `docker compose ps` mostra `healthy` |
| Limpar os dados de teste dependia de cada um saber o comando | README documenta `FLUSHALL`, `down` e `down -v` |

### Para a plataforma como um todo
- Libera os tickets seguintes do nível 1 do BullMQ, que precisam de chaves reais no Redis.
- AOF + volume nomeado fazem os dados sobreviverem a `docker compose down`.
- Nenhuma mudança no código Python nem na API.

### Limitações conhecidas
- A porta é publicada em `0.0.0.0:6379` e o Redis roda sem senha: qualquer máquina na mesma rede consegue acessar. Serve só para desenvolvimento.
- Redis em produção, cluster, sentinel e TLS estão fora de escopo (definido no FL-001).
- O **Status** do FL-001 continua `A fazer`, mesmo com todos os checkboxes marcados.

---

## Arquivos principais do PR

```
flowlog/
├── docker-compose.yml                                  (novo)
├── README.md                                           (seção Redis)
└── docs/backlog/
    └── FL-001-ambiente-redis-docker-compose.md         (checkboxes)
```

---

## Como testar

- [ ] Na raiz do repo, rodar `docker compose up -d`. O container `redis-flowlog-service` sobe sem erro.
- [ ] Rodar `docker compose ps` e esperar ~10s. A coluna STATUS mostra `Up ... (healthy)`.
- [ ] Rodar `docker compose exec redis-flowlog-service redis-cli ping`. Resposta: `PONG`.
- [ ] Se tiver `redis-cli` instalado na máquina, rodar `redis-cli -h localhost ping`. Resposta: `PONG`.
- [ ] Gravar uma chave (`docker compose exec redis-flowlog-service redis-cli SET teste 1`), rodar `docker compose down` e depois `docker compose up -d`. `GET teste` ainda retorna `"1"`.
- [ ] Rodar `docker compose exec redis-flowlog-service redis-cli FLUSHALL` e depois `GET teste`. Retorna `(nil)`.
- [ ] Rodar `docker compose down -v`. O volume é removido; no próximo `up`, o Redis começa vazio.

---

## Comandos úteis

```bash
docker compose up -d
docker compose ps
docker compose logs -f redis-flowlog-service
docker compose exec redis-flowlog-service redis-cli ping
docker compose exec redis-flowlog-service redis-cli FLUSHALL
docker compose down -v
```

---

## Checklist

- [x] Documento cobre todos os commits à frente de `origin/main` (`0452076`, `0ebcb87`, `4b95efb`)
- [x] Apenas arquivos verificados foram citados (nenhum path inventado)
- [x] Sessão "Como testar" tem passos reproduzíveis
- [x] Vinculado ao ticket/backlog correspondente (FL-001)

## Tags

#bcx #pr #infra #feat
