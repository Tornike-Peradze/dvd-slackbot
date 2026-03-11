import os
from sqlalchemy import create_engine, text
import pandas as pd

class DatabaseClient:
    def __init__(self):
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL not set")
        self.engine = create_engine(database_url)
        
    def execute_query(self, query: str) -> pd.DataFrame:
        query = query.strip()
        # Enforce SELECT only
        if not query.upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed.")
            
        # Append LIMIT 100 if not present
        if "LIMIT " not in query.upper():
            query = query.rstrip(";") + " LIMIT 100"
            
        with self.engine.connect() as conn:
            return pd.read_sql(text(query), conn)
