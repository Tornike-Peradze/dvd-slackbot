"""Tests for DatabaseClient."""
import os

import pandas as pd
import pytest
from dotenv import load_dotenv

# Load .env before any code that needs DATABASE_URL
load_dotenv()

from dvd_slackbot.database.client import DatabaseClient


@pytest.fixture(scope="module")
def db_client():
    """DatabaseClient instance; requires DATABASE_URL in .env."""
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL not set; load .env or set env var to run data_loader tests")
    return DatabaseClient()


def test_select_query_returns_dataframe(db_client):
    """Run 'SELECT * FROM customer' and assert result is a DataFrame with rows > 0."""
    df = db_client.execute_query("SELECT * FROM customer")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


def test_limit_100_enforced(db_client):
    """Run 'SELECT * FROM customer' and assert len(df) <= 100."""
    df = db_client.execute_query("SELECT * FROM customer")
    assert isinstance(df, pd.DataFrame)
    assert len(df) <= 100


def test_non_select_query_raises_error(db_client):
    """Run 'DELETE FROM customer' and assert it raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        db_client.execute_query("DELETE FROM customer")
    assert "SELECT" in str(exc_info.value) or "only" in str(exc_info.value).lower()


def test_select_with_existing_limit_not_doubled(db_client):
    """Run 'SELECT * FROM customer LIMIT 10' and assert len(df) == 10."""
    df = db_client.execute_query("SELECT * FROM customer LIMIT 10")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 10
