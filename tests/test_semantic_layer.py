"""Tests for SemanticLayerLoader."""
import os
import pytest

from dvd_slackbot.semantic_layer.loader import SemanticLayerLoader


# Use project root so dvd_slackbot/semantic_layer resolves when running from repo root
SEMANTIC_LAYER_DIR = os.path.join(os.path.dirname(__file__), "..", "dvd_slackbot", "semantic_layer")


@pytest.fixture
def loader():
    """SemanticLayerLoader instance pointing at project semantic_layer."""
    return SemanticLayerLoader(directory=os.path.normpath(SEMANTIC_LAYER_DIR))


def test_revenue_metric_loads_correctly(loader):
    """Revenue metric loads correctly and sql == 'SUM(payment.amount)'."""
    revenue = loader.get_metric("revenue")
    assert revenue is not None
    assert isinstance(revenue, dict)
    assert revenue.get("sql") == "SUM(payment.amount)"
    assert "amount" in revenue.get("definition", "").lower() or "payment" in revenue.get("definition", "").lower()


def test_get_join_path_payment_to_rental(loader):
    """get_join_path returns correct path for payment_to_rental."""
    path = loader.get_join_path("payment", "rental")
    assert path is not None
    assert isinstance(path, dict)
    assert path.get("name") == "payment_to_rental"
    assert path.get("from") == "payment"
    assert path.get("to") == "rental"
    join = path.get("join", {})
    assert "on" in join or "type" in join


def test_get_policies_returns_non_empty_dict(loader):
    """get_policies returns non-empty dict."""
    policies = loader.get_policies()
    assert isinstance(policies, dict)
    assert len(policies) > 0
