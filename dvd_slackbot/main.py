import os
import uuid
from dotenv import load_dotenv

load_dotenv()

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dvd_slackbot.orchestration.graph import app_graph
from dvd_slackbot.orchestration.state import BotState
from dvd_slackbot.observability.logger import get_logger, log_request
from dvd_slackbot.memory.store import MemoryStore

app = App(token=os.environ["SLACK_BOT_TOKEN"])
logger = get_logger()
memory_store = MemoryStore()

@app.message()
def handle_message(message, say):
    """Handle incoming message and run the LangGraph pipeline."""
    user = message.get("user", "unknown")
    text = message.get("text", "")
    channel = message.get("channel", "unknown")
    
    # Use thread_ts if in a thread, else use user to track session context
    session_key = message.get("thread_ts", user)
    
    # Step 1: Immediate acknowledgment
    say("🔍 On it...")
    
    # Retrieve memory context
    conversation_history = memory_store.get_context(session_key)
    
    # Generate a unique session ID for this request
    session_id = str(uuid.uuid4())
    
    # Prepare initial state
    initial_state = BotState(
        question=text,
        user=user,
        channel=channel,
        session_id=session_id,
        memory=conversation_history
    )
    
    # Step 2: Run pipeline
    try:
        final_state = app_graph.invoke(initial_state)
        
        # Log request
        intent = final_state.get("intent", {})
        log_request(
            logger=logger,
            user=user,
            question=text,
            tables_used=[intent.get("target_name")] if intent else [],
            guardrail_triggers=[final_state.get("error")] if final_state.get("guardrail_result") == "fail" else [],
        )
        
        # Step 3: Return result
        final_result = final_state.get("result", "⚠️ No result was generated.")
        
        # Add to memory
        memory_store.add_turn(session_key, "user", text)
        memory_store.add_turn(session_key, "bot", final_result)
        
        say(final_result)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        say(f"⚠️ *An unexpected error occurred:* {str(e)}")

if __name__ == "__main__":
    print("🤖 DataBot starting...")
    handler = SocketModeHandler(
        app,
        os.environ["SLACK_APP_TOKEN"]
    )
    handler.start()
