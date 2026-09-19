# PR: Mapeamento de campos do BullMQ validado contra o Redis real (FL-003)

**Tipo:** docs
**Escopo:** bullmq
**Branch:** `docs/ticket-03` → `main`
**Commits à frente:** 1 (`6964cb7`)
**Repositório:** flowlog
**Vinculado a:** FL-003 — `docs/backlog/FL-003-mapeamento-de-campos-do-bullmq.md` · Linear [GAB-8](https://linear.app/gabriel-silva-magalhaes/issue/GAB-8/fl-003-validar-o-mapeamento-de-campos-contra-o-bullmq-real) · depende de [[FL-002-worker-bullmq-de-exemplo-com-os-4-cenarios]]

---

## Resumo

A PR entrega `docs/bullmq-campos.md`: o raio-X do que o `bullmq@6.3.4` realmente grava no Redis. Cada campo do hash `bull:<fila>:<id>` está documentado com tipo no Redis, presença por estado, exemplo real e tipo alvo em Python, junto com as chaves da fila, o formato do `:lock` e os logs nativos. Os exemplos foram copiados de um `HGETALL` executado contra o Redis local do FL-001, com os jobs do `examples/bullmq-test/` (FL-002) — um por estado: `wait`, `wait` com prioridade, `delayed`, `active`, `completed` e `failed`.

O motivo é o alerta do plano do nível 1: nomes de campos e estruturas de chave mudam entre versões maiores do BullMQ, e escrever os schemas Pydantic (`FL-005`) em cima de suposições quebraria o parser. A inspeção encontrou três divergências relevantes em relação ao que estava em `docs/nivel-1-bullmq.md` — `attemptsMade` gravado como `atm`, jobs com prioridade em um zset `prioritized` em vez da lista `wait`, e o score de `delayed` deslocado 12 bits. Elas estão registradas na seção 5 do documento novo e corrigidas nas tabelas do `nivel-1-bullmq.md`.

---

## O que foi alterado

### Docs
- `docs/bullmq-campos.md` (novo, 196 linhas) → documento de referência com 5 seções:
  1. Tabela de campos do hash do job (`name`, `data`, `opts`, `timestamp`, `delay`, `priority`, `processedOn`, `finishedOn`, `ats`, `atm`, `returnvalue`, `failedReason`, `stacktrace`, `stc`, `rjk`, `parentKey`) com tipo Redis, presença, exemplo real, tipo alvo em Python e regra de parsing.
  2. Tabela das chaves da fila `bull:<fila>:*`, incluindo `prioritized`, `pc` e `marker`.
  3. Chaves do job: `:lock` (composição, TTL e função `extract_worker_id()`) e `:logs`.
  4. Seis blocos de `HGETALL` bruto, um por estado, com os scores observados nos zsets.
  5. Tabela de divergências contra o `nivel-1-bullmq.md`, com o impacto de cada uma no FlowLog.
- `docs/nivel-1-bullmq.md` → tabelas corrigidas com o observado:
  - Chaves da fila: `bull:<fila>:prioritized` (zset) e `bull:<fila>:pc` adicionadas; o score de `delayed` passou de "timestamp de liberação" para `timestamp_liberação * 4096 + contador`; `wait` explicitado como "sem prioridade".
  - Chave do job: `:lock` passou de "Token do worker que segurou o job" para `<worker_uuid>:<contador>`, com TTL de 30s e a nota de que só existe em `active`.
  - Campos do hash: `attemptsMade` virou `atm`; adicionados `ats`, `delay` e `priority`; `returnvalue` ganhou a nota do `"null"`.
  - O aviso "Validar no começo da Etapa 1" foi substituído por um resumo das divergências com link para o documento novo.
- `docs/backlog/FL-003-mapeamento-de-campos-do-bullmq.md` → **Status** de `A fazer` para `Feito`; todos os checkboxes de escopo e critérios de aceite marcados.

### Exemplo BullMQ
- `examples/bullmq-test/bun.lock` → entrada do `bullmq` atualizada de `^6.3.4` para `6.3.4`, alinhando o lockfile ao `package.json`, que já fixava a versão exata.

---

## Impacto na aplicação

### Para o usuário final / time que opera
| Antes | Depois |
| --- | --- |
| O formato dos campos do BullMQ era suposição documental | Cada campo tem exemplo real copiado do Redis e tipo alvo em Python definido |
| `docs/nivel-1-bullmq.md` descrevia `attemptsMade`, sem `prioritized` nem `pc` | Tabelas refletem o que o `bullmq@6.3.4` grava de fato |
| Origem do `worker_id` indefinida | `:lock` = `<worker_uuid>:<contador>`, TTL 30s, com a função de extração escrita |
| Divergências desconhecidas | Seção 5 lista as divergências com impacto classificado por ticket |

### Para a plataforma como um todo
- Destrava o `FL-005` (schemas Pydantic) com nomes e tipos de campo confirmados, em vez de adivinhados.
- Corrige o escopo de leitura do `FL-006` e do `FL-011`: para listar jobs aguardando é preciso ler `:wait` (list) **e** `:prioritized` (zset).
- Define quando o `worker_id` pode ser capturado: só enquanto o job está `active`, porque o BullMQ apaga o `:lock` ao finalizar.
- O `bull:<fila>:meta` guarda `version` = `bullmq:6.3.4`, o que abre caminho para o FlowLog detectar a versão e adaptar o parsing.
- Somente documentação e lockfile: nenhuma linha de código do FlowLog foi alterada.

### Limitações conhecidas
- Validado contra uma única versão (`bullmq@6.3.4`) e um único ambiente (Redis 7-alpine local). Outras versões maiores podem divergir de novo.
- Os campos `rjk` (repeat job key), `parentKey`/`parent` e `deid` (deduplication id) estão documentados a partir do código do BullMQ, não de captura própria: os cenários do `examples/bullmq-test/` não cobrem jobs repetidos, fluxos pai-filho nem deduplicação.
- O bloco do estado `failed` carrega o `stacktrace` bruto, com caminhos absolutos da máquina onde a captura foi feita.
- Os exemplos de `data` mostram `apiToken` e `password` com os valores fake do seed do FL-002 (`TEST-API-TOKEN`, `TEST-DB-PASSWORD`) — são justamente o caso de uso do `FL-010`.
- Nenhum teste automatizado protege o documento de ficar desatualizado se a versão do `bullmq` subir.

---

## Arquivos principais do PR

```
flowlog/
├── docs/
│   ├── bullmq-campos.md                                  (novo)
│   ├── nivel-1-bullmq.md                                 (tabelas corrigidas)
│   ├── backlog/
│   │   └── FL-003-mapeamento-de-campos-do-bullmq.md      (status: Feito)
│   └── prs/
│       └── FL-003-validar-o-mapeamento-de-campos-contra-o-bullmq-real.md
└── examples/bullmq-test/
    └── bun.lock                                          (bullmq fixado em 6.3.4)
```

---

## Como testar

- [ ] Na raiz do repo, `docker compose up -d`; `docker compose ps` mostra `redis-flowlog-service` `healthy`.
- [ ] Em `examples/bullmq-test/`, rodar `bun install` e `bun run seed` com o worker parado.
- [ ] `docker compose exec redis-flowlog-service redis-cli HGETALL bull:test-queue:1` devolve os mesmos campos da seção 4.1 do documento (`name`, `data`, `opts`, `timestamp`, `delay`, `priority`) — os valores de `timestamp` mudam a cada execução.
- [ ] `redis-cli HGETALL bull:test-queue:meta` devolve `version` = `bullmq:6.3.4`, confirmando a versão contra a qual o documento foi escrito.
- [ ] Rodar `bun run start`. Enquanto o `slowly-job` estiver rodando, `redis-cli GET bull:test-queue:<id>:lock` devolve algo no formato `<uuid>:<n>` e `redis-cli TTL` na mesma chave devolve um valor ≤ 30.
- [ ] Depois do `error-job` esgotar as 3 tentativas, `redis-cli HGETALL bull:test-queue:3` traz `atm` = `3` e **não** traz `attemptsMade` — a divergência principal da seção 5.
- [ ] Enfileirar um job com prioridade (`queue.add(nome, dados, { priority: 10 })`) sem worker rodando: `redis-cli TYPE bull:test-queue:prioritized` devolve `zset` e o ID **não** aparece em `LRANGE bull:test-queue:wait 0 -1`.
- [ ] Conferir que `docs/nivel-1-bullmq.md` não contradiz mais o `docs/bullmq-campos.md` nos pontos da seção 5.

---

## Comandos úteis

```bash
docker compose up -d
cd examples/bullmq-test && bun run seed
docker compose exec redis-flowlog-service redis-cli KEYS 'bull:test-queue:*'
docker compose exec redis-flowlog-service redis-cli HGETALL bull:test-queue:meta
docker compose exec redis-flowlog-service redis-cli HGETALL bull:test-queue:1
docker compose exec redis-flowlog-service redis-cli ZRANGE bull:test-queue:delayed 0 -1 WITHSCORES
docker compose exec redis-flowlog-service redis-cli ZRANGE bull:test-queue:prioritized 0 -1 WITHSCORES
docker compose exec redis-flowlog-service redis-cli LRANGE bull:test-queue:2:logs 0 -1
```

---

## Checklist

- [x] Documento cobre o único commit à frente de `origin/main` (`6964cb7`)
- [x] Apenas arquivos verificados foram citados (nenhum path inventado)
- [x] Sessão "Como testar" tem passos reproduzíveis
- [x] Vinculado ao ticket/backlog correspondente (FL-003 / GAB-8)

## Tags

#bcx #pr #bullmq #docs
