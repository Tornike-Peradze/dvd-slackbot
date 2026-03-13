import os
import json
import math
import uuid
import tempfile
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandasai as pai
from pandasai_litellm.litellm import LiteLLM
from dvd_slackbot.orchestration.state import BotState
from dvd_slackbot.semantic_layer.loader import SemanticLayerLoader

loader = SemanticLayerLoader()

CHART_TRIGGERS = [
    "by category", "by store", "by film", "by staff",
    "top 5", "top 10", "breakdown", "distribution", "compare"
]

def _normalize_reasoner_result(response) -> str:
    s = str(response).strip()
    if s.lower() in ("nan", "none", "<na>"):
        return "No data found for that period or filter."
    try:
        if math.isnan(float(s)):
            return "No data found for that period or filter."
    except (ValueError, TypeError):
        pass
    return s

def _should_generate_chart(question: str, response) -> bool:
    question_lower = question.lower()
    has_trigger = any(trigger in question_lower for trigger in CHART_TRIGGERS)
    
    # Handle PandasAI v3 DataFrameResponse wrapper
    actual_response = response
    if hasattr(response, 'value'):
        actual_response = response.value
    
    is_dataframe = isinstance(actual_response, pd.DataFrame) and len(actual_response.columns) >= 2
    print(f"DEBUG response type: {type(response)}, is_dataframe: {is_dataframe}, has_trigger: {has_trigger}")
    return has_trigger and is_dataframe

def _generate_chart(df: pd.DataFrame, question: str) -> str | None:
    try:
        fig, ax = plt.subplots(figsize=(10, 6))

        x_col = df.columns[0]
        y_col = df.columns[1]

        bars = ax.barh(df[x_col].astype(str), df[y_col], color="#4A90D9")

        for bar, val in zip(bars, df[y_col]):
            ax.text(bar.get_width() * 1.01, bar.get_y() + bar.get_height() / 2,
                   f"{val:,.2f}", va="center", fontsize=9)

        ax.set_title(question, fontsize=12, fontweight="bold", pad=15)
        ax.set_xlabel(y_col.replace("_", " ").title())
        ax.set_ylabel(x_col.replace("_", " ").title())
        ax.invert_yaxis()

        plt.tight_layout()

        # Windows-compatible temp path
        chart_path = os.path.join(tempfile.gettempdir(), f"chart_{uuid.uuid4().hex[:8]}.png")
        plt.savefig(chart_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        print(f"DEBUG chart saved to: {chart_path}")
        return chart_path
    except Exception as e:
        print(f"DEBUG chart generation failed: {e}")
        return None

def pandasai_reasoner(state: BotState) -> dict:
    df = state.get("dataframe")
    if df is None:
        return {"error": "No DataFrame available for reasoning.", "guardrail_result": "fail"}

    question = state.get("question", "")
    intent = state.get("intent", {})
    metrics_used = intent.get("metrics_used", [])
    target_name = intent.get("target_name", "")
    memory = state.get("memory", [])

    llm = LiteLLM(model="gpt-4o-mini", api_key=os.environ.get("OPENAI_API_KEY"))
    pai.config.set({"llm": llm, "enable_cache": False})

    pai_df = pai.DataFrame(df)

    metric_definitions = []
    for m in metrics_used:
        m_def = loader.get_metric(m)
        if m_def:
            metric_definitions.append(f"{m}: {json.dumps(m_def)}")
    metrics_context = "\n".join(metric_definitions) if metric_definitions else "N/A"

    table_context = loader.get_table_context(target_name) if target_name else {}
    table_desc = table_context.get("description", "")
    important_cols = table_context.get("important_columns", {})
    cols_context = ", ".join(f"{k}: {v}" for k, v in important_cols.items()) if important_cols else "(check dataframe columns)"

    enriched_prompt = f"""
You are analyzing data for a DVD rental store.

Semantic context for metrics:
{metrics_context}

Table/view: {target_name}. {table_desc}
Important columns: {cols_context}

Rules:
- Revenue = sum of the amount column.
- If no data for the requested period, respond with "No revenue data found for that period", never return "nan".
- Use actual column names from the dataframe.
- Keep the answer brief and professional.
- Return a DataFrame when the answer involves multiple rows (e.g. breakdowns, rankings, comparisons).

Conversation History:
{memory}

Question: {question}

Answer the question using the provided dataframe only.
"""

    try:
        response = pai_df.chat(enriched_prompt)
        result_text = _normalize_reasoner_result(response)

        chart_path = None
        if _should_generate_chart(question, response):
            actual = response.value if hasattr(response, 'value') else response
            chart_path = _generate_chart(actual, question)
        else:
            print(f"DEBUG chart not triggered for response type: {type(response)}")

        return {"result": result_text, "chart_path": chart_path}
    except Exception as e:
        return {"error": f"Reasoning error: {str(e)}", "guardrail_result": "fail"}