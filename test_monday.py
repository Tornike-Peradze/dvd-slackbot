from dotenv import load_dotenv
load_dotenv()

from dvd_slackbot.semantic_layer.loader import SemanticLayerLoader
from dvd_slackbot.database.client import DatabaseClient
from dvd_slackbot.observability.logger import get_logger, log_request

def main():
    # 1. Test SemanticLayerLoader
    print("--- Testing SemanticLayerLoader ---")
    loader = SemanticLayerLoader()
    revenue_metric = loader.get_metric("revenue")
    print(f"Revenue Metric: {revenue_metric}")
    
    # 2. Test DatabaseClient
    print("\n--- Testing DatabaseClient ---")
    client = DatabaseClient()
    df = client.execute_query("SELECT * FROM customer")
    print(f"Returned {len(df)} rows from customer table (expecting 100 max)")
    print(df.head(2))
    
    # 3. Test Logger
    print("\n--- Testing Logger ---")
    logger = get_logger("test")
    log_request(logger, "test_user", "What is the revenue?", ["customer"], "SELECT ...", [], "100x10", 150)
    print("Logger test complete.")

if __name__ == "__main__":
    main()
