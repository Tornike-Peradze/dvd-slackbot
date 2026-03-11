from dvd_slackbot.orchestration.state import BotState

def response_formatter(state: BotState) -> dict:
    """
    Shapes answer for Slack with data source citation. Handles both success and error paths.
    """
    guardrail_result = state.get("guardrail_result")
    
    if guardrail_result == "fail":
        error_msg = state.get("error", "An unknown error occurred.")
        formatted_result = f"⚠️ *I couldn't answer your question:*\n{error_msg}"
        return {"result": formatted_result}
        
    # Success path
    result = state.get("result", "No answer generated.")
    intent = state.get("intent", {})
    target_name = intent.get("target_name", "unknown source")
    
    citation = f"\n\n_Source: {target_name} · dvd_rental_"
    formatted_result = f"{result}{citation}"
    
    return {"result": formatted_result}
