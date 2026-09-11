# FL-018 — CLI `flowlog watch`

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Alta
**Áreas:** Backend, CLI
**Estimativa:** 1,5 dia
**Depende de:** `FL-011`, `FL-014`, `FL-017`

---

## Estado atual

`src/flowlog/__init__.py:1` é só um `print("Hello from flowlog!")`, já ligado ao entrypoint `flowlog` no `pyproject.toml`. E o `create_db_and_tables()` roda em import-time no `src/flowlog/server/server.py:9`, o que atrapalha subir o app programaticamente.

---

## Estado desejado

Um comando entrega tudo:

```
$ flowlog watch
✔ Redis conectado em redis://localhost:6379
✔ 3 filas descobertas: importacoes, notificacoes, relatorios
✔ Dashboard em http://localhost:4700
  (Ctrl+C para sair)
```

---

## Escopo

- [ ] Adicionar `typer` ao `pyproject.toml`; `flowlog:main` vira o app Typer
- [ ] Comando `watch` com as flags: `--redis`, `--prefix` (default `bull`), `--port` (default 4700), `--interval`, `--no-open`
- [ ] Flags sobrescrevem as settings de `FL-017`
- [ ] Validar a conexão com o Redis **antes** de subir o servidor
- [ ] Mover `create_db_and_tables()` do import-time para o `lifespan` do FastAPI
- [ ] Subir o poller como task no `lifespan`, na mesma event loop do uvicorn; cancelar no shutdown
- [ ] Subir o uvicorn programaticamente (`uvicorn.Server`), não por linha de comando
- [ ] Abrir o navegador com `webbrowser.open`, respeitando `--no-open`
- [ ] Erro de conexão com o Redis diz o que fazer, sem despejar traceback:

  ```
  ✖ Não foi possível conectar em redis://localhost:6379
    Verifique se o Redis está rodando: docker compose up -d
    Ou aponte para outro endereço: flowlog watch --redis redis://host:porta
  ```

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| CLI | `src/flowlog/__init__.py:1` |
| App | `src/flowlog/server/server.py:9` |
| Settings | `src/flowlog/settings.py` |

---

## Critérios de aceite

- [ ] `uv run flowlog watch` sobe API, poller e dashboard, e abre o navegador
- [ ] `--no-open` não abre navegador
- [ ] Com o Redis parado, a saída é a mensagem orientativa e exit code diferente de zero — sem traceback
- [ ] Ctrl+C encerra API e poller limpos
- [ ] `flowlog --help` documenta todas as flags

---

## Fora de escopo

- Empacotar como binário
- Múltiplos Redis simultâneos, salvo decisão em contrário em `FL-000`
