# FL-019 — Dashboard: três painéis servidos pelo FastAPI

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Frontend
**Estimativa:** 2 dias
**Depende de:** `FL-014`, `FL-015`

---

## Motivação

Etapa 6. O dashboard é a entrega visível do nível 1: `flowlog watch` abre o navegador e a pessoa vê as filas. Sem build step — arquivos estáticos servidos pelo próprio FastAPI, para o usuário não precisar de Node só para ver o painel.

---

## Comportamento esperado

Layout de três painéis:

| Painel | Conteúdo | Fonte |
| --- | --- | --- |
| Esquerda | Filas com contadores por estado | `GET /api/v1/queues` |
| Centro | Jobs da fila selecionada, com filtro por estado e busca por nome | `GET /api/v1/queues/{fila}/jobs` |
| Direita | Detalhe do job selecionado | `GET /api/v1/queues/{fila}/jobs/{external_id}` |

Detalhe do job mostra: nome, estado, payload em JSON legível, `opts`, tentativas (`2/3`), tempo de espera, duração, stack trace quando falhou, e os logs do `job.log()`.

- [ ] Estado codificado em **cor e forma** (ícone/rótulo), nunca só cor — acessibilidade
- [ ] `***MASKED***` visível e destacado no payload, para ficar claro que houve sanitização
- [ ] Estado vazio tratado: nenhuma fila descoberta explica o que verificar
- [ ] Stack trace em bloco monoespaçado com rolagem própria

---

## Escopo

- [ ] `src/flowlog/static/` com `index.html`, `app.js`, `style.css` — sem bundler, sem framework com build
- [ ] Montar `StaticFiles` no app FastAPI e servir o `index.html` na raiz
- [ ] Paginação da listagem central consumindo `page`/`page_size`
- [ ] Layout responsivo o bastante para telas de notebook (três colunas colapsam para duas)

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Estáticos | `src/flowlog/static/index.html` (novo) |
| Estáticos | `src/flowlog/static/app.js` (novo) |
| App | `src/flowlog/server/server.py` |

---

## Critérios de aceite

- [ ] `flowlog watch` abre o dashboard com as filas de `FL-002` listadas
- [ ] Clicar numa fila lista os jobs; clicar num job abre o detalhe
- [ ] Job que falhou mostra o stack trace real
- [ ] Payload com `apiToken` exibe `***MASKED***`
- [ ] Em escala de cinza ainda dá para distinguir os quatro estados

---

## Fora de escopo

- Qualquer botão de ação (retry, remover, promover) — nível 1 é leitura
- Tema escuro, i18n
- Atualização ao vivo (é `FL-020`)
