from dvd_slackbot.orchestration.state import BotState
from dvd_slackbot.database.client import DatabaseClient
from dvd_slackbot.semantic_layer.loader import SemanticLayerLoader

# Initialize globally
db_client = DatabaseClient()
loader = SemanticLayerLoader()

def data_loader(state: BotState) -> dict:
    """
    Fetches the scoped data from PostgreSQL using intent, and saves DataFrame.
    """
    intent = state.get("intent", {})
    if not intent:
        return {"error": "No intent found for data loading.", "guardrail_result": "fail"}
        
    target_name = intent.get("target_name")
    if not target_name:
        return {"error": "No target table or view identified.", "guardrail_result": "fail"}
        
    # Build query
    query = f"SELECT * FROM {target_name}"
    
    # Execute query
    try:
        df = db_client.execute_query(query)
        if df.empty:
            return {"error": "No data found for the requested query.", "guardrail_result": "fail"}
        return {"dataframe": df}
    except Exception as e:
        return {"error": f"Database error: {str(e)}", "guardrail_result": "fail"}
