import os
import json
import math
import pandasai as pai
from pandasai_litellm.litellm import LiteLLM
from dvd_slackbot.orchestration.state import BotState
from dvd_slackbot.semantic_layer.loader import SemanticLayerLoader

loader = SemanticLayerLoader()

def _normalize_reasoner_result(response) -> str:
    """Ensure we never surface raw NaN/None to the user."""
    s = str(response).strip()
    if s.lower() in ("nan", "none", "<na>"):
        return "No data found for that period or filter."
    try:
        if math.isnan(float(s)):
            return "No data found for that period or filter."
    except (ValueError, TypeError):
        pass
    return s

def pandasai_reasoner(state: BotState) -> dict:
    """
    Receives DataFrame + enriched prompt with semantic context; LLM generates and executes Python logic.
    """
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
    cols_context = ", ".join(f"{k}: {v}" for k, v in important_cols.items()) if important_cols else " (check dataframe columns)"
    
    enriched_prompt = f"""
You are analyzing data for a DVD rental store.

Semantic context for metrics:
{metrics_context}

Table/view: {target_name}. {table_desc}
Important columns: {cols_context}

Rules:
- Revenue = sum of the amount column. For time ranges (e.g. "last month", "in 2005"), filter by the date column (e.g. payment_date) then sum amount.
- If there is no data for the requested period, respond with "No revenue data found for that period" (or similar), or 0. Never return "nan" or NaN.
- Use the actual column names from the dataframe. Keep the answer brief and professional.

Conversation History:
{memory}

Question: {question}

Answer the question using the provided dataframe only.
"""
    
    try:
        response = pai_df.chat(enriched_prompt)
        return {"result": _normalize_reasoner_result(response)}
    except Exception as e:
        return {"error": f"Reasoning error: {str(e)}", "guardrail_result": "fail"}
