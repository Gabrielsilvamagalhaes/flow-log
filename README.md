# FlowLog

**FlowLog** é uma ferramenta de observabilidade para jobs assíncronos: ele registra o ciclo de vida de execuções em segundo plano, guarda os logs emitidos durante elas e expõe tudo por uma API consultável.

O projeto tem **duas portas de entrada** para os mesmos dados:

| Porta de entrada | Como funciona | Estado |
| --- | --- | --- |
| **API de ingestão (HTTP)** | A aplicação chama o FlowLog explicitamente: abre um *Job Run*, envia logs, finaliza. | Implementada |
| **Leitura automática de filas BullMQ** | O FlowLog lê o Redis onde o BullMQ guarda as filas e monta os *Job Runs* sozinho, sem nenhuma alteração no código da aplicação. | Em construção — ver [`docs/nivel-1-bullmq.md`](docs/nivel-1-bullmq.md) |

A segunda porta é o foco atual do projeto. A meta é que o usuário rode `flowlog watch` no terminal e um dashboard abra mostrando as filas, o payload de cada job e o estado de cada worker — sem configuração.

---

## 🎯 Objetivo

Quem roda filas em produção normalmente descobre que um job falhou pelo efeito colateral: o e-mail não saiu, o relatório não chegou, a conciliação ficou pela metade. O payload que causou a falha vive no Redis até ser removido, e o log do processo se perde no `stdout` do container.

O FlowLog centraliza isso: recebe (ou coleta) a execução, valida e sanitiza os payloads antes de persistir, e mantém o histórico depois que a fila já esqueceu o job.

---

## 🏗️ Arquitetura de Entidades

```
+-------------------+                   +-------------------+
|     Client /      |  ingestão HTTP    |                   |
|     API Key       | ----------------> |                   |
+-------------------+                   |     Job Run       |
                                        |  (Ciclo de Vida)  |
+-------------------+                   |                   |
|   Fila BullMQ     |  leitura Redis    |                   |
|  (Redis / Node)   | ----------------> |                   |
+-------------------+                   +-------------------+
                                                  |
                                       +----------+----------+
                                       | 1:N                 | 1:N
                                       v                     v
                             +-------------------+ +-------------------+
                             |     Log Entry     | |    Attachment     |
                             |   (Sanitizado)    | |  (Dump/Log File)  |
                             +-------------------+ +-------------------+
```

1. **Client / API Key:** Aplicação externa autorizada a registrar métricas e logs por HTTP.
2. **Fila BullMQ:** Fila lida diretamente do Redis. Vira *Job Run* sem que a aplicação saiba do FlowLog.
3. **Job Run:** Instância de execução de uma tarefa (ex: importação bancária, pipeline de ETL).
4. **Log Entry:** Registro individual de evento/telemetria emitido durante a execução do job.
5. **Attachment:** Arquivo de log bruto ou dump anexado a um job específico.

---

## 🧰 Stack

- **FastAPI** + **Pydantic v2** — API e validação
- **SQLModel** sobre **SQLite** (`flowlog.db`) — persistência
- **uv** — gerenciamento de dependências e execução

```bash
uv sync
uv run fastapi dev src/flowlog/server/server.py
```

Documentação interativa em `http://localhost:8000/docs`.

---

## 🐳 Redis de desenvolvimento

A integração com BullMQ precisa de um Redis local com chaves reais. O `docker-compose.yml` na raiz sobe um `redis:7-alpine` na porta `6379`, com AOF ligado e volume nomeado (`redis-data`), então os dados sobrevivem a um `docker compose down`.

### Subir

```bash
docker compose up -d
```

Confira se o healthcheck ficou `healthy`:

```bash
docker compose ps
```

Teste a conexão:

```bash
# com redis-cli instalado na máquina
redis-cli -h localhost ping

# sem redis-cli local, usando o do container
docker compose exec redis-flowlog-service redis-cli ping
```

Os dois devem responder `PONG`.

### Limpar

Apagar todas as chaves e manter o container rodando:

```bash
docker compose exec redis-flowlog-service redis-cli FLUSHALL
```

Parar o container e manter os dados:

```bash
docker compose down
```

Parar o container e apagar o volume (recomeça do zero):

```bash
docker compose down -v
```

---

## 📋 Regras de Negócio (RNs)

| ID | Regra | Estado |
| --- | --- | --- |
| **RN-01** | **Validação temporal.** `ended_at` não pode ser anterior a `started_at`. | Feito |
| **RN-02** | **Transição rígida de estados.** Fluxo permitido: `PENDING` → `RUNNING` → (`SUCCESS` \| `FAILED` \| `CANCELLED`). Job em estado final não aceita novos logs nem mudança de status. | Feito |
| **RN-03** | **Validação condicional por severidade.** Se `level == CRITICAL`, `stack_trace` e `error_code` passam a ser obrigatórios. | Feito |
| **RN-04** | **Restrição de upload.** Anexos de no máximo **10 MB**, extensões `.log` ou `.json`. | Pendente |
| **RN-05** | **Sanitização automática de metadados.** Qualquer chave de `metadata` contendo `password`, `token` ou `secret` (case-insensitive) tem o valor substituído por `***MASKED***` durante o parse da requisição (camada DTO / Pydantic). | Pendente |
| **RN-06** | **Etiquetagem automática de performance.** Job finalizado em `SUCCESS` com duração inferior a **1,0 segundo** recebe a tag `FAST_EXECUTION`. | Feito |
| **RN-07** | **Autenticação por API Key.** Rotas protegidas exigem o cabeçalho `X-API-Key`; chave ausente ou inválida retorna `401 Unauthorized`. | Pendente |

---

## 🔌 Especificação dos Endpoints (Contratos DTO)

### 1. Iniciar Job Run — *feito*

- **Método/Rota:** `POST /api/v1/jobs`
- **Headers:** `X-API-Key: <string>`
- **Entrada (Request Body — JSON):**
  - `client_identifier` (string, min: 3, max: 50, obrigatório)
  - `job_type` (enum: `ETL`, `EXPORT`, `NOTIFICATION`, `CLEANUP`, obrigatório)
  - `environment` (enum: `DEVELOPMENT`, `STAGING`, `PRODUCTION`, obrigatório)
  - `started_at` (datetime ISO-8601, opcional, default: `now()`)
- **Saída (Response 201 Created — JSON):**
  - `job_id` (UUIDv4)
  - `status` (string: `RUNNING`)
  - `started_at` (datetime ISO-8601)
  - `links` (objeto com URLs de auto-navegação: `add_log`, `finish_job`, `upload_attachment`)

---

### 2. Ingerir Log de Execução — *feito*

- **Método/Rota:** `POST /api/v1/jobs/{job_id}/logs`
- **Headers:** `X-API-Key: <string>`
- **Path Parameter:** `job_id` (UUIDv4)
- **Entrada (Request Body — JSON):**
  - `level` (enum: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, obrigatório)
  - `message` (string, min: 5, max: 2000, obrigatório)
  - `stack_trace` (string, opcional — *obrigatório se `level == CRITICAL`*)
  - `error_code` (string, opcional — *obrigatório se `level == CRITICAL`*)
  - `metadata` (dict chave-valor dinâmico, opcional)
  - `timestamp` (datetime ISO-8601, opcional, default: `now()`)
- **Saída (Response 201 Created — JSON):**
  - `log_id` (UUIDv4)
  - `job_id` (UUIDv4)
  - `level` (string)
  - `message` (string)
  - `sanitized_metadata` (dict com campos sensíveis mascarados)
  - `created_at` (datetime ISO-8601)

---

### 3. Anexar Arquivo de Dump/Log (Multipart Upload) — *pendente*

- **Método/Rota:** `POST /api/v1/jobs/{job_id}/attachments`
- **Headers:** `X-API-Key: <string>`
- **Path Parameter:** `job_id` (UUIDv4)
- **Entrada (Form-Data):**
  - `file` (UploadFile / binário — máx 10 MB, ext: `.log` ou `.json`)
  - `description` (string, opcional, max: 200)
- **Saída (Response 202 Accepted — JSON):**
  - `attachment_id` (UUIDv4)
  - `file_name` (string)
  - `size_bytes` (integer)
  - `content_type` (string)
  - `processed` (boolean: `false`)

---

### 4. Finalizar Job Run — *feito*

- **Método/Rota:** `PATCH /api/v1/jobs/{job_id}/finish`
- **Headers:** `X-API-Key: <string>`
- **Path Parameter:** `job_id` (UUIDv4)
- **Entrada (Request Body — JSON):**
  - `final_status` (enum: `SUCCESS`, `FAILED`, `CANCELLED`, obrigatório)
  - `ended_at` (datetime ISO-8601) — preenchido automaticamente pelo Pydantic; o cliente não envia
  - `summary` (string, opcional, max: 500)
- **Saída (Response 200 OK — JSON):**
  - `job_id` (UUIDv4)
  - `status` (string)
  - `duration_seconds` (float, calculado)
  - `total_logs_count` (integer)
  - `tags` (array de strings, ex: `["FAST_EXECUTION"]`)

---

### 5. Consultar Logs Paginados — *feito*

- **Método/Rota:** `GET /api/v1/jobs/{job_id}/logs`
- **Headers:** `X-API-Key: <string>`
- **Path Parameter:** `job_id` (UUIDv4)
- **Query Parameters:**
  - `level` (enum de severidade, opcional)
  - `page` (integer, min: 1, default: 1)
  - `page_size` (integer, min: 1, max: 100, default: 20)
  - `search` (string, opcional, busca substring na mensagem)
- **Saída (Response 200 OK — JSON):**
  - `items` (array de objetos `Log Entry`)
  - `total` (integer)
  - `page` (integer)
  - `page_size` (integer)
  - `total_pages` (integer)

---

## 🔭 Próxima etapa: integração com BullMQ (nível 1)

O escopo completo — etapas, lacunas do modelo atual, esquema de chaves do Redis e critérios de aceite — está em **[`docs/nivel-1-bullmq.md`](docs/nivel-1-bullmq.md)**.

Resumo do que o nível 1 entrega:

- Descoberta automática das filas a partir do Redis, sem arquivo de configuração
- Payload, estado, tentativas, duração e stack trace de cada job
- Dashboard local servido por `flowlog watch`, atualizando em tempo real

E o que ele **não** entrega (depende de um SDK Node, fora deste escopo):

- Logs escritos dentro do processor da aplicação
- Etapas intermediárias de um job longo

---

## 🛠️ Conceitos de FastAPI e Pydantic v2 exercitados

1. **Validação de modelo (`@field_validator` e `@model_validator`):** validações dependentes entre campos (ex: exigir `stack_trace` quando `level == CRITICAL`) e validação raiz (`mode='after'`) comparando `started_at` e `ended_at`.
2. **Transformadores no parse (`@field_validator(mode='before')`):** interceptação de `metadata` para mascarar senhas e tokens antes do payload chegar ao controller.
3. **Injeção de dependências (`Depends`):** extração do header `X-API-Key` e validação da sessão do job.
4. **Configuração tipada (`pydantic-settings`):** carregamento de `.env` para segredos, chaves de API e limites de upload.
5. **Upload e streams (`UploadFile`):** leitura em chunks para validar tamanho sem carregar o arquivo inteiro em memória.
6. **Exception handlers customizados:** sobrescrita do `RequestValidationError` do FastAPI para padronizar o formato de erro.
