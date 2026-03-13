"""Tests for MemoryStore."""
import pytest

from dvd_slackbot.memory.store import MemoryStore


def test_add_turn_stores_correctly():
    """add_turn stores correctly."""
    store = MemoryStore()
    store.add_turn("session_1", "user", "What was revenue in 2005?")
    store.add_turn("session_1", "bot", "Total revenue was $61312.04.")
    ctx = store.get_context("session_1")
    assert len(ctx) == 2
    assert ctx[0]["role"] == "user" and ctx[0]["content"] == "What was revenue in 2005?"
    assert ctx[1]["role"] == "bot" and ctx[1]["content"] == "Total revenue was $61312.04."


def test_get_context_returns_prior_turns():
    """get_context returns prior turns."""
    store = MemoryStore()
    store.add_turn("session_2", "user", "How many rentals?")
    store.add_turn("session_2", "bot", "There were 16,044 rentals.")
    ctx = store.get_context("session_2")
    assert len(ctx) == 2
    assert ctx[0]["content"] == "How many rentals?"
    assert ctx[1]["content"] == "There were 16,044 rentals."


def test_two_sessions_do_not_share_context():
    """Two different sessions don't share context."""
    store = MemoryStore()
    store.add_turn("session_a", "user", "Revenue by store?")
    store.add_turn("session_a", "bot", "Store 1: $33k, Store 2: $28k.")
    store.add_turn("session_b", "user", "Top 5 films?")
    store.add_turn("session_b", "bot", "Here are the top 5.")
    ctx_a = store.get_context("session_a")
    ctx_b = store.get_context("session_b")
    assert len(ctx_a) == 2
    assert len(ctx_b) == 2
    assert ctx_a[0]["content"] == "Revenue by store?"
    assert ctx_b[0]["content"] == "Top 5 films?"
    assert ctx_a[0]["content"] != ctx_b[0]["content"]
