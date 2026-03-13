# dvd-slackbot

## 1. Project Overview

**dvd-slackbot** is a Slack-based natural language analytics assistant over a PostgreSQL `dvd_rental` database. Users ask questions in plain English; the bot returns data insights without writing SQL or opening dashboards.

**Who it's for:** Analysts, product owners, or anyone who needs quick answers from the DVD rental dataset (revenue, rentals, customers, films, stores, etc.) via Slack.

---

## 2. Architecture

The bot is built on **LangGraph**: a single state graph with **7 nodes** that process each message:

1. **parse_input** — Normalizes the question and sends an immediate “On it…” acknowledgment to Slack.
2. **input_guardrails** — Blocks destructive SQL, PII requests, and off-topic questions (e.g. weather, simple math).
3. **router** — Classifies intent and picks which table/view and metrics to use (semantic routing).
4. **data_loader** — Runs a read-only query against PostgreSQL and loads the result into a DataFrame.
5. **pandasai_reasoner** — Uses **PandasAI v3** to answer the question over the loaded data (with semantic layer context).
6. **output_guardrails** — Validates the answer before sending.
7. **response_formatter** — Formats the reply and adds a source citation (e.g. `Source: payment · dvd_rental`).

Business logic is centralized in a **semantic layer** (YAML in `dvd_slackbot/semantic_layer/`): metrics, tables, views, join paths, and policies. The router and reasoner use this layer instead of hardcoded logic.

---

## 3. Setup

### Prerequisites

- **Python 3.11**
- **PostgreSQL** (with the `dvd_rental` sample database loaded)
- **Poetry** (for dependency and environment management)

### Step-by-step

1. **Clone the repo**
   ```bash
   git clone <repo-url>
   cd dvd-slackbot
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```
   For development and tests:
   ```bash
   poetry install --extras dev
   ```

3. **Configure environment**
   - Copy `.env.example` to `.env` (or create `.env` with the variables below).
   - Fill in every variable.

   | Variable | Description |
   |----------|-------------|
   | `SLACK_BOT_TOKEN` | Bot token (starts with `xoxb-`). From [Slack API](https://api.slack.com/apps) → Your App → OAuth & Permissions → “Bot User OAuth Token”. |
   | `SLACK_SIGNING_SECRET` | Signing secret for request verification. From Slack API → Your App → Basic Information → “Signing Secret”. |
   | `SLACK_APP_TOKEN` | Socket Mode token (starts with `xapp-`). From Slack API → Your App → Basic Information → “App-Level Tokens” (enable Socket Mode and create a token). |
   | `DATABASE_URL` | PostgreSQL connection string, e.g. `postgresql://user:password@localhost:5432/dvd_rental`. Use the DB where the `dvd_rental` sample is loaded. |
   | `OPENAI_API_KEY` | API key from [OpenAI](https://platform.openai.com/api-keys). Used by LiteLLM for routing, guardrails, and PandasAI. |
   | `LOG_LEVEL` | Optional. e.g. `INFO` or `DEBUG`. |
   | `ENVIRONMENT` | Optional. e.g. `development` or `production`. |

4. **Database**
   - Ensure the **dvd_rental** sample database is restored in PostgreSQL (e.g. from [postgresqltutorial.com](https://www.postgresqltutorial.com/postgresql-getting-started/postgresql-sample-database/) or your own dump).

---

## 4. Running the bot

From the project root:

```bash
poetry run python dvd_slackbot/main.py
```

The bot starts in Socket Mode and listens for messages. Invite it to a channel or DM it to ask questions.

---

## 5. Running tests

Run the full test suite:

```bash
poetry run python -m pytest tests/ -v
```

Data-loader tests require `DATABASE_URL` in `.env`; if it’s missing, those tests are skipped.

---

## 6. Example questions to ask the bot

- What was total revenue in 2005?
- How many rentals per store?
- Top 5 films by revenue
- How many active customers do we have?
- Revenue by film category

Keep questions about the DVD rental business (rentals, revenue, customers, films, staff, stores, inventory, categories). Off-topic or destructive requests are blocked by guardrails.

---

## 7. Known limitations

- **Data range:** The sample data is from **2005–2006**. Queries like “revenue last month” or “last year” will typically return no data or empty results.
- **Single table/view per question:** The router selects one table or view per question. Complex multi-table joins are not supported in one query.
- **Local only:** The project is set up for local development and Socket Mode. There is no cloud deployment or HTTP endpoint configuration in this repo.

---

## 8. Tech stack

- **Python 3.11**
- **LangGraph** — orchestration and state graph
- **PandasAI v3** — natural language over DataFrames
- **Slack Bolt** — Slack app and Socket Mode
- **PostgreSQL** — `dvd_rental` database
- **LiteLLM** — LLM calls (e.g. OpenAI) for routing, guardrails, and PandasAI backend
