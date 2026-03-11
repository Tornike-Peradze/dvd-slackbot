import os
import re
from litellm import completion
from dvd_slackbot.orchestration.state import BotState

def input_guardrails(state: BotState) -> dict:
    """
    Checks for data modifications, out-of-scope queries, and explicit PII.
    """
    question = state.get("question", "").lower().strip()

    # 1. Block destructive operations (keyword check — fast)
    destructive_terms = ["insert", "update", "delete", "drop", "create table", "alter"]
    if any(term in question for term in destructive_terms):
        return {
            "guardrail_result": "fail",
            "error": "I can only answer questions and read data. I cannot modify the database."
        }

    # 2. Block PII (keyword check — fast)
    pii_terms = ["email", "password", "social security", "credit card"]
    if any(term in question for term in pii_terms):
        return {
            "guardrail_result": "fail",
            "error": "I cannot provide PII such as email addresses."
        }

    # 3. Simple answerability check
    if len(question.split()) < 2:
        return {
            "guardrail_result": "fail",
            "error": "Please provide a more detailed question."
        }

    # 4. Fast off-topic checks (weather, simple arithmetic, general knowledge)
    off_topic_terms = ["weather", "temperature", "forecast", "rain", "snow", "humidity"]
    if any(term in question for term in off_topic_terms):
        return {
            "guardrail_result": "fail",
            "error": "I can only answer questions about the DVD rental business data (rentals, revenue, films, etc.), not weather or general knowledge."
        }
    # Simple arithmetic pattern (e.g. "what is 2+2", "3 + 5")
    if re.search(r"\d+\s*[\+\-\*\/x]\s*\d+", question) or re.match(r"^\s*what\s+is\s+\d+\s*[\+\-\*\/x]?\s*\d+\s*\??\s*$", question):
        return {
            "guardrail_result": "fail",
            "error": "I'm an analytics bot for the DVD rental database. For simple math or general knowledge, please use a calculator or search."
        }

    # 5. LLM-based relevance check — catches other off-topic questions
    try:
        response = completion(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""You are a guardrail for a DVD rental store analytics bot.
The bot can ONLY answer questions about: rentals, revenue, customers, films, staff, stores, inventory, and categories.

Answer NO for: weather, sports, news, simple math, general knowledge, or anything not in the DVD rental database.

Is this question specifically about DVD rental business data (tables, metrics, reports)?
Question: "{question}"

Reply with ONLY one word: YES or NO."""
            }],
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        answer = response.choices[0].message.content.strip().upper()
        if answer != "YES":
            return {
                "guardrail_result": "fail",
                "error": "I can only answer questions about the DVD rental business data."
            }
    except Exception:
        pass  # If LLM check fails, let it through — fail open

    return {"guardrail_result": "pass"}
