# FL-000 — Decisões técnicas que travam o nível 1

**Tipo:** `chore`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend, Arquitetura
**Estimativa:** 0,5 dia (discussão + registro)
**Depende de:** Nenhuma

---

## Contexto

O plano do nível 1 ([docs/nivel-1-bullmq.md](../docs/nivel-1-bullmq.md)) lista quatro decisões em aberto que mudam o desenho de tickets posteriores. Fechar isso antes de escrever código evita retrabalho em `FL-007`, `FL-008` e `FL-012`.

Este ticket não entrega código: entrega decisões registradas em `docs/`.

---

## Escopo

- [ ] **Migração de schema** — apagar `flowlog.db` a cada mudança vs. adotar Alembic. Recomendação: Alembic já no nível 1, porque `FL-007` altera uma tabela existente e `SQLModel.metadata.create_all()` não faz `ALTER TABLE`.
- [ ] **Retenção** — quantos jobs `completed`/`failed` manter por fila (sugestão: 500 por fila, configurável). Define o `limite` de `FL-011` e se entra rotina de purga.
- [ ] **Autenticação (RN-07)** — dashboard local exige `X-API-Key`? Se sim, `FL-017` precisa gerar e injetar a chave no front.
- [ ] **Múltiplos Redis** — uma instância por execução do `flowlog watch` ou vários `--redis`? Define a assinatura do CLI em `FL-017` e se `queue_name` precisa de um prefixo de conexão.
- [ ] Registrar o resultado em `docs/decisoes-nivel-1.md` (uma seção por decisão: opção escolhida, alternativa descartada, motivo).

---

## Critérios de aceite

- [ ] `docs/decisoes-nivel-1.md` existe com as 4 decisões fechadas e justificadas
- [ ] Tickets afetados (`FL-007`, `FL-008`, `FL-011`, `FL-017`) atualizados com a decisão

---

## Fora de escopo

- Implementar as decisões (cada uma vive no seu ticket)
