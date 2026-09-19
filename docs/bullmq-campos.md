# Mapeamento de Campos e Chaves do BullMQ (v6.3.4)

> **Documento de referência para implementação dos Schemas Pydantic (`FL-005`), Leitor de Redis (`FL-006`) e Modelos de Banco (`FL-007`).**  
> Validado empiricamente contra instância real do Redis com `bullmq@6.3.4` gerada pelo ambiente de teste `examples/bullmq-test/`.

---

## 1. Mapeamento de Campos do Hash do Job (`bull:<fila>:<id>`)

Todos os valores retornados pelo Redis via `HGETALL` chegam como strings (`str` em Python). O parser (`FL-005`) deve deserializar para os tipos Python alvo indicados.

| Campo no Redis | Tipo Redis | Presença | Exemplo Real | Tipo Alvo (Python) | Observações e Regras de Parsing |
| --- | --- | --- | --- | --- | --- |
| `name` | `string` | Obrigatório | `"quickly-job"` | `str` | Nome registrado do job (`queue.add(name, ...)`). |
| `data` | `string` (JSON) | Obrigatório | `{"message":"Job rápido iniciado","apiToken":"TEST-API-TOKEN","password":"TEST-DB-PASSWORD"}` | `dict[str, Any]` | Payload do job. Parsear com `json.loads()`. Se ausente/vazio, default `{}`. Contém dados sensíveis a sanitizar no `FL-010`. |
| `opts` | `string` (JSON) | Obrigatório | `{"attempts":0}` ou `{"backoff":{"delay":5000,"type":"exponential"},"attempts":3}` | `dict[str, Any]` | Opções do job (`attempts`, `delay`, `backoff`, `priority`). Parsear com `json.loads()`. |
| `timestamp` | `string` (int) | Obrigatório | `"1789437528735"` | `int` / `datetime` | Momento em que o job foi enfileirado (ms epoch). Converter com `int(val)` ou `datetime.fromtimestamp(int(val)/1000, tz=timezone.utc)`. |
| `delay` | `string` (int) | Obrigatório | `"0"` ou `"10000"` | `int` | Tempo de atraso configurado em milissegundos. `0` se imediato. |
| `priority` | `string` (int) | Obrigatório | `"0"` ou `"10"` | `int` | Nível de prioridade numérico (`0` é o padrão). |
| `processedOn` | `string` (int) | Opcional (a partir de `active`) | `"1789437349680"` | `Optional[int]` / `Optional[datetime]` | Momento em que o worker pegou o job para processar (ms epoch). Ausente em `wait` e `delayed`. |
| `finishedOn` | `string` (int) | Opcional (em `completed` / `failed`) | `"1789437349717"` | `Optional[int]` / `Optional[datetime]` | Momento em que o job terminou (sucesso ou falha final). Ausente em `wait`, `delayed` e `active`. |
| `ats` | `string` (int) | Opcional (a partir de `active`) | `"1"` ou `"3"` | `int` | **Attempts Started:** Contador de tentativas iniciadas. Ausente em `wait`/`delayed`. Default `0`. |
| `atm` | `string` (int) | Opcional (em `completed` / `failed`) | `"1"` ou `"3"` | `int` | **Attempts Made:** Tentativas consumidas. **Atenção:** no BullMQ v6 o campo é minificado para `atm` (em versões antigas era `attemptsMade`). O parser deve checar `hash.get("atm") or hash.get("attemptsMade") or 0`. |
| `returnvalue` | `string` (JSON) | Opcional (em `completed`) | `"null"` ou `"{\"resultado\":123}"` | `Optional[Any]` | Retorno retornado pela função do worker. Quando o worker retorna `void`/`undefined`, o BullMQ grava a string `"null"`. Parsear com `json.loads()` quando presente. |
| `failedReason` | `string` | Opcional (em `failed`) | `"Job de erro"` | `Optional[str]` | Mensagem da exceção capturada que levou o job a falhar. |
| `stacktrace` | `string` (JSON Array) | Opcional (em `failed`) | `["Error: Job de erro\n    at ..."]` | `list[str]` | Array JSON com uma string de stack trace para cada tentativa realizada. Parsear com `json.loads()`; se ausente, default `[]`. |
| `stc` | `string` (int) | Opcional | `"0"` | `int` | **Stalled Counter:** Contador de vezes que o job foi marcado como stalled. Minificado de `stalledCounter`. |
| `rjk` | `string` | Opcional | `"..."` | `Optional[str]` | **Repeat Job Key:** Chave de repetição para jobs agendados/cron. |
| `parentKey` / `parent` | `string` | Opcional | `"bull:parent-queue:12"` | `Optional[str]` / `Optional[dict]` | Chave e metadados do job pai em fluxos/parent-child. |

---

## 2. Estrutura de Chaves da Fila (`bull:<fila>:*`)

Além das chaves previamente esperadas, o BullMQ v6 utiliza estruturas adicionais para priorização e controle:

| Chave | Tipo Redis | Conteúdo | Observações |
| --- | --- | --- | --- |
| `bull:<fila>:meta` | `hash` | Metadados da fila | Contém `version` (ex: `"bullmq:6.3.4"`) e `opts.maxLenEvents` (`"10000"`). Usada para descoberta de filas via `SCAN MATCH bull:*:meta`. |
| `bull:<fila>:id` | `string` | Inteiro atômico | Contador incremental para geração do ID dos jobs. |
| `bull:<fila>:wait` | `list` | Lista de IDs | IDs dos jobs normais aguardando processamento (FIFO). |
| `bull:<fila>:prioritized` | `zset` | ZSet de IDs | **Chave crítica:** Armazena jobs com `priority > 0` aguardando worker. Score = `(priority * 2^32) + counter`. |
| `bull:<fila>:pc` | `string` | Inteiro | **Priority Counter:** Contador atômico usado para compor o score do ZSet `:prioritized`. |
| `bull:<fila>:active` | `list` | Lista de IDs | IDs dos jobs em execução no momento por algum worker. |
| `bull:<fila>:delayed` | `zset` | ZSet de IDs | IDs de jobs agendados. Score = `(timestamp_ms * 4096) + counter` (onde 4096 desloca 12 bits para desempate). |
| `bull:<fila>:completed` | `zset` | ZSet de IDs | IDs de jobs concluídos com sucesso. Score = `finishedOn` (timestamp ms epoch). |
| `bull:<fila>:failed` | `zset` | ZSet de IDs | IDs de jobs que falharam definitivamente. Score = `finishedOn` (timestamp ms epoch). |
| `bull:<fila>:events` | `stream` | Stream de eventos | Eventos publicados pelo BullMQ (`waiting`, `active`, `completed`, `failed`, etc.). |
| `bull:<fila>:stalled-check` | `string` | Timestamp | Timestamp da última verificação de jobs travados/stalled. |
| `bull:<fila>:marker` | `string` | String `"1"` | Marcador de sinalização interno do BullMQ. |

---

## 3. Chaves Específicas do Job

### 3.1. Lock do Worker (`bull:<fila>:<id>:lock`)
- **Tipo Redis:** `string`
- **Existência:** Apenas enquanto o job estiver no estado `active`. É automaticamente removida pelo BullMQ ao concluir (`completed`) ou falhar (`failed`).
- **TTL:** Padrão de 30 segundos (`30000ms`), renovado periodicamente a cada ~15 segundos pelo Worker ativo.
- **Valor Observado:** `7319eadf-98ca-477f-a3d4-5812161377f8:1`
- **Composição do Valor:** `<worker_uuid>:<postfix>`
  - `<worker_uuid>`: UUID gerado no construtor do `Worker` (`worker.id`). É estável durante toda a vida do processo do worker.
  - `<postfix>`: Contador inteiro sequencial de jobs atendidos por esse worker.
- **Extração do `worker_id` no FlowLog:**
  ```python
  def extract_worker_id(lock_value: str | None) -> str | None:
      if not lock_value:
          return None
      return lock_value.split(":")[0]
  ```
  > [!IMPORTANT]
  > Como a chave de lock é deletada na finalização do job, o FlowLog deve capturar e registrar o `worker_id` enquanto o job estiver no estado `active`.

### 3.2. Logs Nativos (`bull:<fila>:<id>:logs`)
- **Tipo Redis:** `list`
- **Existência:** Criada sob demanda quando o processador chama `await job.log("mensagem")`.
- **Exemplo Real:**
  ```
  1) "Job lento iniciado (etapa 1/3)"
  2) "Job lento em andamento (etapa 2/3)"
  3) "Job lento finalizando (etapa 3/3)"
  ```
- **Leitura:** `LRANGE bull:<fila>:<id>:logs 0 -1`. Cada item é uma string de log crua.

---

## 4. Exemplos Reais Brutos Copiados do Redis (HGETALL por Estado)

### 4.1. Estado `wait`
Capturado de `bull:test-queue:1` imediatamente após `bun run seed`:
```json
{
  "name": "quickly-job",
  "data": "{\"message\":\"Job rápido iniciado\",\"apiToken\":\"TEST-API-TOKEN\",\"password\":\"TEST-DB-PASSWORD\"}",
  "opts": "{\"attempts\":0}",
  "timestamp": "1789437528735",
  "delay": "0",
  "priority": "0"
}
```

### 4.2. Estado `delayed`
Capturado de `bull:test-queue:4` após `bun run seed` com `{ delay: 10000 }`:
```json
{
  "name": "delay-job",
  "data": "{\"message\":\"Job com delay iniciado\"}",
  "opts": "{\"delay\":10000,\"attempts\":0}",
  "timestamp": "1789437528795",
  "delay": "10000",
  "priority": "0"
}
```
*Score no ZSet `bull:test-queue:delayed`: `7329536158904320` (`(1789437528795 + 10000) * 4096`).*

### 4.3. Estado `active`
Capturado de `bull:test-queue:2` (`slowly-job`) enquanto o worker executava o processamento:
```json
{
  "name": "slowly-job",
  "data": "{\"message\":\"Job lento iniciado\"}",
  "opts": "{\"attempts\":0}",
  "timestamp": "1789437312357",
  "delay": "0",
  "priority": "0",
  "processedOn": "1789437349695",
  "ats": "1"
}
```
*Chave de lock ativa no Redis: `bull:test-queue:2:lock` = `"7319eadf-98ca-477f-a3d4-5812161377f8:1"` (TTL: 30s).*

### 4.4. Estado `completed`
Capturado de `bull:test-queue:1` (`quickly-job`) após finalização com sucesso:
```json
{
  "name": "quickly-job",
  "data": "{\"message\":\"Job rápido iniciado\",\"apiToken\":\"TEST-API-TOKEN\",\"password\":\"TEST-DB-PASSWORD\"}",
  "opts": "{\"attempts\":0}",
  "timestamp": "1789437312277",
  "delay": "0",
  "priority": "0",
  "processedOn": "1789437349680",
  "finishedOn": "1789437349717",
  "ats": "1",
  "atm": "1",
  "returnvalue": "null"
}
```
*Score no ZSet `bull:test-queue:completed`: `1789437349717` (igual ao `finishedOn`).*

### 4.5. Estado `failed`
Capturado de `bull:test-queue:3` (`error-job`) após esgotar 3 tentativas com backoff exponencial:
```json
{
  "name": "error-job",
  "data": "{\"message\":\"Job de erro iniciado\"}",
  "opts": "{\"backoff\":{\"delay\":5000,\"type\":\"exponential\"},\"attempts\":3}",
  "timestamp": "1789437312361",
  "delay": "0",
  "priority": "0",
  "processedOn": "1789437364860",
  "finishedOn": "1789437364905",
  "ats": "3",
  "atm": "3",
  "failedReason": "Job de erro",
  "stacktrace": "[\"Error: Job de erro\\n    at <anonymous> (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\src\\\\workers\\\\test-worker.ts:25:17)\\n    at <anonymous> (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\node_modules\\\\bullmq\\\\dist\\\\cjs\\\\classes\\\\worker.js:582:43)\\n    at processJob (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\node_modules\\\\bullmq\\\\dist\\\\cjs\\\\classes\\\\worker.js:565:21)\\n    at mainLoop (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\node_modules\\\\bullmq\\\\dist\\\\cjs\\\\classes\\\\worker.js:330:41)\\n    at async run (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\node_modules\\\\bullmq\\\\dist\\\\cjs\\\\classes\\\\worker.js:263:19)\\n    at async main (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\capture.ts:8:16)\\n    at processTicksAndRejections (native:7:39)\",\"Error: Job de erro\\n    at <anonymous> (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\src\\\\workers\\\\test-worker.ts:25:17)\\n    at <anonymous> (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\node_modules\\\\bullmq\\\\dist\\\\cjs\\\\classes\\\\worker.js:582:43)\\n    at processJob (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\node_modules\\\\bullmq\\\\dist\\\\cjs\\\\classes\\\\worker.js:565:21)\\n    at mainLoop (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\node_modules\\\\bullmq\\\\dist\\\\cjs\\\\classes\\\\worker.js:330:41)\\n    at async run (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\node_modules\\\\bullmq\\\\dist\\\\cjs\\\\classes\\\\worker.js:263:19)\\n    at async main (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\capture.ts:8:16)\\n    at processTicksAndRejections (native:7:39)\",\"Error: Job de erro\\n    at <anonymous> (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\src\\\\workers\\\\test-worker.ts:25:17)\\n    at <anonymous> (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\node_modules\\\\bullmq\\\\dist\\\\cjs\\\\classes\\\\worker.js:582:43)\\n    at processJob (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\node_modules\\\\bullmq\\\\dist\\\\cjs\\\\classes\\\\worker.js:565:21)\\n    at mainLoop (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\node_modules\\\\bullmq\\\\dist\\\\cjs\\\\classes\\\\worker.js:330:41)\\n    at async run (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\node_modules\\\\bullmq\\\\dist\\\\cjs\\\\classes\\\\worker.js:263:19)\\n    at async main (C:\\\\Users\\\\geris\\\\orca\\\\workspaces\\\\flowlog\\\\docs-ticket-03\\\\examples\\\\bullmq-test\\\\capture.ts:8:16)\\n    at processTicksAndRejections (native:7:39)\"]"
}
```
*Score no ZSet `bull:test-queue:failed`: `1789437364905` (igual ao `finishedOn`).*

### 4.6. Estado `wait` com prioridade (`prioritized`)
Capturado de `bull:test-queue:6` após `queue.add("job-prioritario-2", { prio: true }, { priority: 10 })`, sem worker rodando. O ID **não** aparece em `bull:test-queue:wait`:
```json
{
  "name": "job-prioritario-2",
  "data": "{\"prio\":true}",
  "opts": "{\"priority\":10,\"attempts\":0}",
  "timestamp": "1789437493711",
  "delay": "0",
  "priority": "10"
}
```
*`TYPE bull:test-queue:prioritized` = `zset`. Score: `42949672961` (`10 * 2^32 + 1`). `bull:test-queue:pc` = `"1"`.*

---

## 5. Divergências em Relação a `docs/nivel-1-bullmq.md`

| Item | Previsto originalmente em `nivel-1-bullmq.md` | Comportamento real observado (`bullmq@6.3.4`) | Impacto no FlowLog |
| --- | --- | --- | --- |
| **Nome de `attemptsMade`** | Campo `attemptsMade` no hash | Minificado para **`atm`** (e `attemptsStarted` gravado como **`ats`**) | **Alto:** se o parser Pydantic (`FL-005`) procurar apenas `attemptsMade`, receberá `None`/`0`. Deve checar `raw.get("atm") or raw.get("attemptsMade") or 0`. |
| **Fila com Prioridade** | Jobs aguardando apenas em `bull:<fila>:wait` (lista) | Jobs com `priority > 0` vão para o ZSet **`bull:<fila>:prioritized`**, com contador auxiliar **`bull:<fila>:pc`** | **Alto:** o Poller (`FL-011`) e Reader (`FL-006`) precisam consultar tanto `:wait` (List) quanto `:prioritized` (ZSet) para listar os jobs aguardando. |
| **Scores de `delayed`** | Score = timestamp de liberação simples | Score = `(timestamp_liberacao * 4096) + counter` | **Médio:** ao inspecionar o timestamp de um job em `delayed` direto pelo score do ZSet, deve-se dividir por `4096` (`score >> 12`). Porém, para o job em si, a data exata pode ser obtida por `int(timestamp) + int(delay)` do próprio hash. |
| **Metadados de Versão** | `bull:<fila>:meta` como hash genérico | Contém explicitamente `version` com o valor `"bullmq:6.3.4"` | **Positivo:** permite detecção da versão do BullMQ diretamente pelo FlowLog para adaptar compatibilidade automaticamente. |
| **Formato do `:lock`** | "Token do worker que segurou o job" | Formato `<worker-uuid>:<job-counter>` com TTL de 30s | **Baixo / Esclarecido:** `lock.split(":")[0]` fornece um identificador estável da instância do worker durante toda a sua execução. |
| **Outras minificações** | Não previstas | `stc` (`stalledCounter`), `rjk` (`repeatJobKey`), `deid` (`deduplicationId`) | **Baixo:** documentadas para suporte nos schemas opcionais. |
