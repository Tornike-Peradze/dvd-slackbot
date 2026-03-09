import os
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])

@app.message()
def handle_message(message, say):
    """Handle any incoming message — echo for now."""
    user = message.get("user", "unknown")
    text = message.get("text", "")
    
    # Step 1: Immediate acknowledgment
    say("🔍 On it...")
    
    # Step 2: Echo (pipeline goes here next session)
    say(f"✅ Received: *{text}*\n_Full pipeline coming soon._")

if __name__ == "__main__":
    print("🤖 DataBot starting...")
    handler = SocketModeHandler(
        app,
        os.environ["SLACK_APP_TOKEN"]
    )
    handler.start()