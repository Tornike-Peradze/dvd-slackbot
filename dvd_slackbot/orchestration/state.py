from typing import TypedDict, Any

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
