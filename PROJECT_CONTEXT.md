# PROJECT_CONTEXT.md

## Project Overview

Talk-to-Your-Data Slackbot is a natural language analytics assistant built on top of a PostgreSQL dvd_rental database. It allows non-technical users to ask plain-English questions in Slack and receive data-driven answers instantly — without writing SQL, opening a dashboard, or involving a data analyst.

The core problem it solves: business users have questions about revenue, customers, and inventory that currently require either SQL knowledge or waiting for analyst support. This bot removes that bottleneck entirely.

## System Scope

**In scope:**
- Answering natural language analytics questions about the dvd_rental dataset
- Reading data live from PostgreSQL via scoped, safe SQL queries
- Enforcing business metric definitions (e.g. revenue = SUM(payment.amount) only)
- Blocking PII exposure (customer.email, staff.email)
- Maintaining conversational context within a Slack session via LangGraph state
- Logging every request for observability and debugging

**Out of scope:**
- Writing or modifying data (SELECT only — no INSERT, UPDATE, DELETE)
- Connecting to external data sources beyond dvd_rental
- User authentication or role-based access control
- Scheduled reports or proactive alerts
- Deployment to cloud infrastructure (MVP is local only)

## Architecture Summary

The system is a **LangGraph stateful pipeline** with seven nodes, a shared TypedDict state object, and a cross-cutting semantic layer.

### LangGraph Graph Structure

```
parse_input → input_guardrails → router → data_loader → pandasai_reasoner → output_guardrails → response_formatter
```

**Conditional edges:**
- `input_guardrails` → if FAIL → `response_formatter` (error path)
- `input_guardrails` → if PASS → `router`
- `output_guardrails` → if FAIL → `response_formatter` (error path)
- `output_guardrails` → if PASS → `response_formatter` (success path)

### Nodes

- **parse_input** — extracts user, channel, session_id from the Slack event; sends immediate "🔍 On it..." acknowledgment
- **input_guardrails** — four checks: data-related, answerability, PII request, ambiguity
- **router** — LLM-based intent classifier; maps question to tables/views/metrics using the semantic layer; detects M:M fanout risk
- **data_loader** — builds scoped SQL query, prefers safe views, enforces LIMIT 100, returns DataFrame
- **pandasai_reasoner** — receives DataFrame + enriched prompt with semantic context; LLM generates and executes Python logic; returns result
- **output_guardrails** — checks for empty result, anomaly, PII leak, fanout inflation
- **response_formatter** — shapes answer for Slack with data source citation; handles both success and error paths

### Shared State (TypedDict)

All nodes read from and write to a single shared state object passed through the graph:

```python
class BotState(TypedDict):
    question: str
    user: str
    channel: str
    session_id: str
    guardrail_result: str        # "pass" or reason for failure
    intent: dict                 # tables, metrics, join paths
    dataframe: Any               # Pandas DataFrame
    result: str                  # final answer
    error: str                   # error message if any
    memory: list                 # prior turns in session
```

### Supporting Systems

- **Semantic Layer** — YAML files (metrics, entities, relationships, views, policies) loaded at startup by SemanticLayerLoader; single source of truth for all business logic
- **Memory** — session history injected into router and reasoner for follow-up resolution
- **Observability** — structured JSON logging on every request covering question, tables used, generated code, guardrail triggers, result shape, and latency

## Key Inputs and Outputs

**Input:** A plain-English question typed by a user in a Slack channel or DM
(e.g. "What were the top 5 films by revenue last month?")

**Output:** A Slack message containing a direct answer in plain English, the underlying data if relevant, and a citation line:
`Source: [table or view] · [time period] · dvd_rental`

**Failure output:** A clear, friendly Slack message explaining why the question could not be answered (out of scope, ambiguous, PII requested, no data found)

## Design Rationale

**LangGraph for orchestration:** The pipeline uses LangGraph's StateGraph to manage state passing between nodes and handle conditional routing. This makes the control flow explicit, testable node-by-node, and extensible — future additions like human-in-the-loop review or parallel tool calls can be added as new nodes without restructuring the pipeline.

**Semantic layer as single source of truth:** Business logic (metric definitions, join rules, PII policies) lives in YAML files, not in prompt strings or application code. This makes the system auditable, maintainable, and consistent across all components.

**Safe views over raw joins:** Pre-defined PostgreSQL views (sales_by_store, sales_by_film_category, customer_list, staff_list) are preferred over raw table joins to eliminate M:M fanout risk on revenue queries involving film_category and film_actor bridge tables.

**PandasAI v3 for reasoning:** Rather than building a custom SQL-to-answer layer, PandasAI handles the DataFrame reasoning step — the LLM generates Python logic against a real DataFrame, keeping revenue calculations grounded in actual payment data.

**Immediate Slack acknowledgment:** The pipeline takes 8–20 seconds end-to-end. Sending "🔍 On it..." immediately after the parse_input node ensures users are never left in silence regardless of downstream processing time.