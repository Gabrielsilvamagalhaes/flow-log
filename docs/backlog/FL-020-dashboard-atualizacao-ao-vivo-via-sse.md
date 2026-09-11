# FL-020 — Dashboard ao vivo via SSE

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Média
**Áreas:** Frontend
**Estimativa:** 1 dia
**Depende de:** `FL-016`, `FL-019`

---

## Motivação

Fecha a promessa do nível 1: ver a fila andando sem apertar F5. O painel de `FL-019` já sabe desenhar o estado; falta ele receber as mudanças.

---

## Comportamento esperado

- [ ] `EventSource` em `/api/v1/stream`, aberto ao carregar a página
- [ ] `queue_counts` atualiza os contadores do painel esquerdo, sem redesenhar a lista inteira
- [ ] `job_updated` atualiza a linha do job no painel central; se for o job aberto, atualiza o detalhe
- [ ] Job novo entra na lista respeitando o filtro ativo (estado + busca)
- [ ] Transição de estado tem destaque visual breve, para a mudança não passar batida
- [ ] Reconexão automática com backoff quando a conexão cai; ao reconectar, recarrega o estado atual pela API (o SSE não faz replay)
- [ ] Indicador de conexão: ao vivo / reconectando / offline

---

## Escopo

- [ ] Camada de eventos no `app.js`, separada da camada de render
- [ ] Recarregar estado completo no `onopen` da reconexão
- [ ] Não acumular listener a cada reconexão

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Estáticos | `src/flowlog/static/app.js` |
| Rota | `src/flowlog/routes/queue_routes.py` (`/api/v1/stream`) |

---

## Critérios de aceite

- [ ] Enfileirar um job em `FL-002` faz a linha aparecer no dashboard em menos de 2 segundos, sem reload
- [ ] Job que vai de `RUNNING` para `FAILED` muda de estado na tela sozinho
- [ ] Parar e religar o Redis deixa o indicador em "reconectando" e depois volta a "ao vivo", com dado correto
- [ ] Meia hora com a aba aberta não degrada a página (sem vazamento de listener)

---

## Fora de escopo

- Notificação do navegador em falha de job
- Som ou badge no título da aba
