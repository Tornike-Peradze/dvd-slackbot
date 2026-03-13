import os
from slack_bolt import App
from dvd_slackbot.orchestration.state import BotState

def response_formatter(state: BotState) -> dict:
    """
    Shapes answer for Slack with data source citation.
    Uploads chart image if available.
    """
    guardrail_result = state.get("guardrail_result")
    channel = state.get("channel", "")
    chart_path = state.get("chart_path")

    if guardrail_result == "fail":
        error_msg = state.get("error", "An unknown error occurred.")
        formatted_result = f"⚠️ *I couldn't answer your question:*\n{error_msg}"
        return {"result": formatted_result, "chart_path": None}

    # Success path
    result = state.get("result", "No answer generated.")
    intent = state.get("intent", {})
    target_name = intent.get("target_name", "unknown source")
    citation = f"\n\n_Source: {target_name} · dvd_rental_"
    formatted_result = f"{result}{citation}"

    # Upload chart if available
    if chart_path and os.path.exists(chart_path):
        try:
            slack_app = App(token=os.environ["SLACK_BOT_TOKEN"])
            slack_app.client.files_upload_v2(
                channel=channel,
                file=chart_path,
                title="Chart",
                initial_comment=f"_Source: {target_name} · dvd_rental_"
            )
            os.remove(chart_path)  # clean up temp file
            return {"result": formatted_result, "chart_uploaded": True}
        except Exception as e:
            # Chart upload failed — still return text answer
            return {"result": formatted_result, "chart_path": None}

    return {"result": formatted_result}