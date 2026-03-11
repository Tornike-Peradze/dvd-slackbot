# AGENTS.md — Cursor AI Rules for dvd-slackbot

## Project Overview
Slack-based natural language analytics assistant over a PostgreSQL dvd_rental database.
Users ask plain-English questions; the bot returns data insights without SQL or dashboards.
Orchestration is handled by **LangGraph StateGraph**. All nodes share a single BotState TypedDict.

---

## Orchestration Framework — CRITICAL
**This project uses LangGraph. Never suggest plain sequential Python for the pipeline.**

### Graph structure:
```
parse_input → input_guardrails → router → data_loader → pandasai_reasoner → output_guardrails → response_formatter
```

### Conditional edges:
- `input_guardrails` FAIL → `response_formatter`
- `input_guardrails` PASS → `router`
- `output_guardrails` FAIL → `response_formatter`
- `output_guardrails` PASS → `response_formatter`

### Shared state schema:
```python
class BotState(TypedDict):
    question: str
    user: str
    channel: str
    session_id: str
    guardrail_result: str
    intent: dict
    dataframe: Any
    result: str
    error: str
    memory: list
```

Graph is defined in `dvd_slackbot/orchestration/graph.py`.
Each node is a pure function that takes BotState and returns a partial BotState update.

---

## PandasAI Version — CRITICAL
**Always use PandasAI v3. Never use v1/v2 patterns.**

✅ CORRECT imports:
```python
import pandasai as pai
from pandasai_litellm.litellm import LiteLLM

llm = LiteLLM(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"))
pai.config.set({"llm": llm})
df = pai.DataFrame(your_dataframe)
response = df.chat("Your question here")
```

❌ NEVER use (v1/v2 — deprecated):
- `SmartDataframe`
- `SmartDatalake`
- `from pandasai import PandasAI`

---

## Semantic Layer — CRITICAL
**The semantic layer is the single source of truth. Never hardcode business logic in prompt strings.**

- All YAML files live in `dvd_slackbot/semantic_layer/`
- The `SemanticLayerLoader` class reads all YAMLs at startup
- Router, Data Loader, and PandasAI prompt builder must all load context via `SemanticLayerLoader`
- Exposed methods: `get_metric()`, `get_table_context()`, `get_join_path()`, `get_policies()`

---

## Revenue Metric — CRITICAL
**Revenue = SUM(payment.amount) ONLY.**
- ❌ Never use `film.rental_rate` for revenue calculations
- ❌ Never join through `film_category` or `film_actor` for revenue (M:M fanout risk)
- ✅ Always prefer safe views: `sales_by_store`, `sales_by_film_category`, `customer_list`, `staff_list`

---

## Database Rules
- **SELECT only** — never generate INSERT, UPDATE, DELETE, DROP, or any destructive SQL
- Default LIMIT 100 on all queries unless user specifies otherwise
- PII fields — NEVER expose in responses: `customer.email`, `staff.email`
- Prefer `customer.activebool` over `customer.active`
- Two "store" concepts: `inventory.store_id` (operational) vs `customer.store_id` (home store) — do not conflate

---

## M:M Join Warning
`film_category` and `film_actor` are bridge tables. Joining through them on revenue queries causes fanout inflation.
Always route revenue + category questions to the `sales_by_film_category` safe view instead of raw joins.

---

## Slack UX Rule
**Always send an immediate acknowledgment to Slack in the `parse_input` node, before the graph continues.**
Example: `"🔍 On it..."``
The pipeline takes 8–20 seconds. Users must not see silence.

---

## Observability — Every Request Must Log
- User + timestamp
- Question received
- Tables/views used
- Generated SQL or PandasAI code
- Guardrail triggers (if any)
- Result shape (rows × columns)
- Latency (ms)

Use structured JSON logging via `dvd_slackbot/observability/logger.py`.

---

## Response Format
Every data response must include a citation line:
`Source: [table or view name] · [time period if relevant] · dvd_rental`

---

## Environment Variables (load via python-dotenv)
```
SLACK_BOT_TOKEN
SLACK_SIGNING_SECRET
SLACK_APP_TOKEN
DATABASE_URL
OPENAI_API_KEY
LOG_LEVEL
ENVIRONMENT
```