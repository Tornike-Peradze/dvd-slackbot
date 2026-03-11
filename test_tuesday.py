from dotenv import load_dotenv
load_dotenv()

from dvd_slackbot.orchestration.graph import app_graph
from dvd_slackbot.orchestration.state import BotState

def test_routing():
    # Test valid query
    initial_state = BotState(
        question="Total revenue by store",
        user="test_user",
        channel="C123",
        session_id="S123",
        memory=[]
    )
    
    result = app_graph.invoke(initial_state)
    print("\n--- Valid Query Result ---")
    print(f"Guardrail Result: {result.get('guardrail_result')}")
    print(f"Intent: {result.get('intent')}")
    
    # Test PII query
    pii_state = BotState(
        question="What is the email of customer 123?",
        user="test_user",
        channel="C123",
        session_id="S123",
        memory=[]
    )
    
    result_pii = app_graph.invoke(pii_state)
    print("\n--- PII Query Result ---")
    print(f"Guardrail Result: {result_pii.get('guardrail_result')}")
    print(f"Error: {result_pii.get('error')}")

if __name__ == "__main__":
    test_routing()
