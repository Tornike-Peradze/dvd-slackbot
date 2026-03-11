import re
from dvd_slackbot.orchestration.state import BotState

def output_guardrails(state: BotState) -> dict:
    """
    Checks for empty result, anomaly, PII leak, fanout inflation.
    """
    # If a previous node already failed, skip
    if state.get("guardrail_result") == "fail":
        return {}
        
    result = state.get("result", "")
    if not result:
        return {"error": "Reasoning engine returned an empty result.", "guardrail_result": "fail"}
        
    # Check for PII leaks
    pii_regex = r'[\w\.-]+@[\w\.-]+'
    if re.search(pii_regex, str(result)):
        return {"error": "Blocked potential PII (email) in the response.", "guardrail_result": "fail"}
        
    if "billion" in str(result).lower() or "trillion" in str(result).lower():
        return {"error": "Anomalous value detected (potential fanout inflation).", "guardrail_result": "fail"}
        
    return {"guardrail_result": "pass"}
