# FL-017 — Configuração tipada com `pydantic-settings`

**Tipo:** `feat`
**Status:** A fazer
**Prioridade:** Média
**Áreas:** Backend
**Estimativa:** 0,5 dia
**Depende de:** `FL-000`

---

## Motivação

Redis URL, prefixo, porta, intervalo do poller, retenção e limite de payload aparecem em quase todos os tickets. Sem um ponto único de configuração, cada um vira constante espalhada no módulo que precisou dela.

É também o item 4 da lista de conceitos do `README.md`, ainda pendente.

---

## Comportamento esperado

Precedência: **flag do CLI > variável de ambiente > `.env` > default**.

| Campo | Env | Default |
| --- | --- | --- |
| `redis_url` | `FLOWLOG_REDIS_URL` | `redis://localhost:6379` |
| `redis_prefix` | `FLOWLOG_REDIS_PREFIX` | `bull` |
| `port` | `FLOWLOG_PORT` | `4700` |
| `poll_interval` | `FLOWLOG_POLL_INTERVAL` | `1.0` |
| `retention_per_queue` | `FLOWLOG_RETENTION_PER_QUEUE` | conforme `FL-000` |
| `max_payload_bytes` | `FLOWLOG_MAX_PAYLOAD_BYTES` | `65536` |
| `database_url` | `FLOWLOG_DATABASE_URL` | `sqlite:///flowlog.db` |

---

## Escopo

- [ ] Adicionar `pydantic-settings` ao `pyproject.toml`
- [ ] `src/flowlog/settings.py` com `Settings(BaseSettings)`, prefixo `FLOWLOG_` e leitura de `.env`
- [ ] Instância única acessível por função com cache
- [ ] `.env.example` na raiz com todas as chaves comentadas
- [ ] Substituir a conexão hardcoded de `src/flowlog/server/database/connection.py` pelo `database_url` das settings

### Arquivos principais

| Camada | Arquivo |
| --- | --- |
| Settings | `src/flowlog/settings.py` (novo) |
| Conexão | `src/flowlog/server/database/connection.py` |
| Exemplo | `.env.example` (novo) |

---

## Critérios de aceite

- [ ] `FLOWLOG_PORT=5000` no ambiente muda a porta sem tocar em código
- [ ] Valor inválido (ex.: `FLOWLOG_PORT=abc`) falha na inicialização com mensagem clara
- [ ] Nenhuma URL de Redis ou caminho de banco hardcoded fora de `settings.py`

---

## Fora de escopo

- Configuração por arquivo YAML ou TOML
