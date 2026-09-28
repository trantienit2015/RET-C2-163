# RET-C2-163 — Unit Tests: ValidateInputNode (pre_process)

import json

from framework.schemas.agent_status import AgentStatus
from src.nodes.pre_process_node import ValidateInputNode


class TestValidateInputNode:
    def setup_method(self):
        self.node = ValidateInputNode()

    def test_success_serializes_payload(self):
        state = {
            "user_input": "A recommendation engine used for hiring decisions.",
            "input_context": {},
            "node_history": [],
            "error_log": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        payload = json.loads(result["validated_input"])
        assert "description" in payload

    def test_empty_input_is_answered_not_failed(self):
        """An ERROR run ends as a terminal failure event, which the chat surface leaves
        spinning — so a caller who sent nothing gets told what to send instead."""
        result = self.node.execute({"user_input": "  ", "node_history": [], "error_log": []})
        assert result["status"] == AgentStatus.SUCCESS.value
        assert "validation_error" in result
        assert result.get("validated_system_description") is None

    def test_execute_signature(self):
        import inspect

        params = list(inspect.signature(ValidateInputNode.execute).parameters.keys())
        assert params[1] == "state"
        assert "_invoke_impl" not in ValidateInputNode.__dict__


def test_a_one_word_probe_is_not_assessed():
    """"test" is not a system description; answering it with a verdict would present
    "not high-risk" as a finding about something that was never examined."""
    from src.nodes.pre_process_node import ValidateInputNode

    result = ValidateInputNode().execute({"user_input": "test", "node_history": [], "error_log": []})
    assert "validation_error" in result
    assert result.get("validated_system_description") is None


import pytest

from src.nodes.pre_process_node import _is_assessable


@pytest.mark.parametrize(
    "text",
    [
        "test",
        "hello hello hello",
        "hello hello hello hello hello",
        "こんにちは こんにちは こんにちは",
        "aaaaaaaaaaaaaaaaaaaaaaaa",
        "ありがとうございます。よろしくお願いします。",
        "はじめまして。よろしくお願いします。",
        "thanks thanks thanks thanks",
    ],
)
def test_padding_and_greetings_are_not_assessed(text):
    """Length alone does not make a description: a greeting repeated is long enough and still
    names no system, and answering it with "not high-risk" would be a verdict on nothing."""
    assert _is_assessable(text) is False


@pytest.mark.parametrize(
    "text",
    [
        "採用の合否を自動で判定するシステムを EU 向けに提供します。",
        "An AI-driven hiring and recruitment screening system for retail store staff.",
        "A product recommendation engine for the online storefront.",
        "店舗の在庫を予測して発注量を決める仕組みを社内で使います。",
    ],
)
def test_a_real_description_is_assessed(text):
    assert _is_assessable(text) is True
