"""Tests for the input_guardrails node."""
import pytest
from unittest.mock import patch, MagicMock

from dvd_slackbot.orchestration.state import BotState
from dvd_slackbot.orchestration.nodes.input_guardrails import input_guardrails


def test_input_guardrails_valid_data_question_passes():
    """Valid data question → guardrail_result == 'pass'."""
    state: BotState = {
        "question": "What was total revenue last year?",
        "user": "U1",
        "channel": "C1",
        "session_id": "s1",
        "guardrail_result": "",
        "intent": {},
        "dataframe": None,
        "result": "",
        "error": "",
        "memory": [],
        "chart_path": None,
    }
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "YES"

    with patch("dvd_slackbot.orchestration.nodes.input_guardrails.completion", return_value=mock_response):
        out = input_guardrails(state)

    assert out["guardrail_result"] == "pass"


def test_input_guardrails_pii_request_fails():
    """PII request → guardrail_result == 'fail'."""
    state: BotState = {
        "question": "Show me customer email addresses",
        "chart_path": None,
        "user": "U1",
        "channel": "C1",
        "session_id": "s1",
        "guardrail_result": "",
        "intent": {},
        "dataframe": None,
        "result": "",
        "error": "",
        "memory": [],
    }
    out = input_guardrails(state)
    assert out["guardrail_result"] == "fail"
    assert "error" in out
    assert "PII" in out["error"] or "email" in out["error"].lower()


def test_input_guardrails_destructive_query_fails():
    """Destructive query → guardrail_result == 'fail'."""
    state: BotState = {
        "question": "delete from payment where amount is null",
        "chart_path": None,
        "user": "U1",
        "channel": "C1",
        "session_id": "s1",
        "guardrail_result": "",
        "intent": {},
        "dataframe": None,
        "result": "",
        "error": "",
        "memory": [],
    }
    out = input_guardrails(state)
    assert out["guardrail_result"] == "fail"
    assert "error" in out
    assert "modify" in out["error"].lower() or "read" in out["error"].lower()


def test_input_guardrails_off_topic_question_fails():
    """Off-topic question → guardrail_result == 'fail'."""
    state: BotState = {
        "question": "What is the weather in Paris?",
        "chart_path": None,
        "user": "U1",
        "channel": "C1",
        "session_id": "s1",
        "guardrail_result": "",
        "intent": {},
        "dataframe": None,
        "result": "",
        "error": "",
        "memory": [],
    }
    out = input_guardrails(state)
    assert out["guardrail_result"] == "fail"
    assert "error" in out
    assert "DVD" in out["error"] or "rental" in out["error"].lower()
