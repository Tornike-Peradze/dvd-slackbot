import os
import json
from litellm import completion
from dvd_slackbot.orchestration.state import BotState
from dvd_slackbot.semantic_layer.loader import SemanticLayerLoader

loader = SemanticLayerLoader()

def router(state: BotState) -> dict:
    """
    Classifies intent based on the user's question and semantic layer context.
    """
    question = state.get("question", "")
    memory = state.get("memory", [])
    
    metrics_info = json.dumps(loader.data["metrics"], indent=2)
    views_info = json.dumps(loader.data["views"], indent=2)
    tables_info = json.dumps(list(loader.data["tables"].keys()))
    
    prompt = f"""
    You are a semantic router for a PostgreSQL dvd_rental database.
    Your job is to identify which tables, views, and metrics are needed to answer the user's question.
    
    CRITICAL RULE:
    If the question asks for revenue broken down by category or actor, you MUST route to the safe view 'sales_by_film_category' or 'sales_by_store' instead of raw tables to avoid many-to-many fanout.
    
    Available metrics:
    {metrics_info}
    
    Available safe views:
    {views_info}
    
    Available tables:
    {tables_info}
    
    Conversation History:
    {memory}
    
    Question: {question}
    
    Respond ONLY with a valid JSON object containing:
    {{
        "target_type": "view" or "table",
        "target_name": "<name_of_table_or_view>",
        "metrics_used": ["<metric_names>"]
    }}
    """
    
    try:
        response = completion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            api_key=os.environ.get("OPENAI_API_KEY")
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
            
        intent = json.loads(content.strip())
        return {"intent": intent}
        
    except Exception as e:
        return {
            "guardrail_result": "fail",
            "error": f"Failed to route question: {str(e)}"
        }
