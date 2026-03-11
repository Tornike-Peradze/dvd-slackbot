from langgraph.graph import StateGraph, END
from dvd_slackbot.orchestration.state import BotState
from dvd_slackbot.orchestration.nodes.parse_input import parse_input
from dvd_slackbot.orchestration.nodes.input_guardrails import input_guardrails
from dvd_slackbot.orchestration.nodes.router import router
from dvd_slackbot.orchestration.nodes.data_loader import data_loader
from dvd_slackbot.orchestration.nodes.pandasai_reasoner import pandasai_reasoner
from dvd_slackbot.orchestration.nodes.output_guardrails import output_guardrails
from dvd_slackbot.orchestration.nodes.response_formatter import response_formatter

def check_input_guardrail(state: BotState):
    if state.get("guardrail_result") == "fail":
        return "response_formatter"
    return "router"

def check_output_guardrail(state: BotState):
    if state.get("guardrail_result") == "fail":
        return "response_formatter"
    return "response_formatter"

# Initialize graph
workflow = StateGraph(BotState)

# Add nodes
workflow.add_node("parse_input", parse_input)
workflow.add_node("input_guardrails", input_guardrails)
workflow.add_node("router", router)
workflow.add_node("data_loader", data_loader)
workflow.add_node("pandasai_reasoner", pandasai_reasoner)
workflow.add_node("output_guardrails", output_guardrails)
workflow.add_node("response_formatter", response_formatter)

# Define edges
workflow.set_entry_point("parse_input")
workflow.add_edge("parse_input", "input_guardrails")
workflow.add_conditional_edges(
    "input_guardrails",
    check_input_guardrail,
    {
        "router": "router",
        "response_formatter": "response_formatter"
    }
)

workflow.add_edge("router", "data_loader")
workflow.add_edge("data_loader", "pandasai_reasoner")
workflow.add_edge("pandasai_reasoner", "output_guardrails")
workflow.add_conditional_edges(
    "output_guardrails",
    check_output_guardrail,
    {
        "response_formatter": "response_formatter"
    }
)
workflow.add_edge("response_formatter", END)

# Compile
app_graph = workflow.compile()
