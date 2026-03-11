from dvd_slackbot.orchestration.state import BotState

def parse_input(state: BotState) -> dict:
    """
    Extracts basic info, initializes the state.
    Note: The immediate Slack acknowledgment 'On it...' should be sent before the graph starts,
    usually in the Slack event handler (e.g. main.py) as it requires the 'say' function.
    This node simply passes the state forward or formats it.
    """
    return {"guardrail_result": "pending"}
