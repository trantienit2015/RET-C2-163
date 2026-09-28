"""AgentCore Platform v1.0 — RET-C2-163 outer pre_process node (ValidateInput)."""

import json
import re
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from shared.services.events import emitter
from shared.services.events.types import EventType
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event


# An assessment needs a system to assess. Length alone does not establish that: a greeting
# repeated three times is long enough and still says nothing to classify. What a description
# has to carry is some substance — enough distinct words, and not merely a salutation.
_MIN_DESCRIPTION_CHARS = 15
_MIN_DISTINCT_WORDS = 4

_GREETINGS = frozenset(
    {
        "hello",
        "hi",
        "hey",
        "test",
        "testing",
        "ping",
        "thanks",
        "thank",
        "you",
        "こんにちは",
        "こんばんは",
        "おはよう",
        "はじめまして",
        "テスト",
        "よろしく",
        "お願いします",
    }
)

_LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z'-]*")
# Japanese does not separate words with spaces, so distinct characters stand in for distinct
# words: kanji and katakana carry the content, kana alone mostly carries grammar.
_JA_CONTENT = re.compile(r"[ァ-ヶ一-鿿]")


def _units(text: str) -> set[str]:
    return {w.lower() for w in _LATIN_WORD.findall(text)} | set(_JA_CONTENT.findall(text))


def _is_assessable(user_input: str | None) -> bool:
    """Whether the request carries a system description worth classifying.

    Answering a greeting with "not high-risk" would present a verdict about something that
    was never examined, so the bar is substance rather than length: distinct words that are
    not all salutations.
    """
    text = (user_input or "").strip()
    if len(text) < _MIN_DESCRIPTION_CHARS:
        return False
    units = _units(text) - _units(" ".join(_GREETINGS))
    return len(units) >= _MIN_DISTINCT_WORDS


def _no_description_message(user_input: str | None) -> str:
    if re.search(r"[぀-ヿ㐀-\u4dbf一-\u9fff]", user_input or ""):
        return (
            "評価する対象の記述がありません。対象の AI システムについて、"
            "何を判断するのか・どのように提供するのか・利用者はどこにいるのかを"
            "一〜二文で書いてください。その記述に対して評価します。"
        )
    return (
        "There is no system description here to assess. Describe the AI system in a "
        "sentence or two — what it decides, how it is deployed, and where its users are — "
        "and the assessment will run against that description."
    )


class ValidateInputNode(FunctionNode):
    """Outer pre_process: S-1 trust (framework), reject empty/malformed input, and
    serialize a JSON payload into ``validated_input`` for the inner assessment subgraph.
    """

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        # Progress (non-terminal) event for the caller. Outside the Marketplace runtime
        # this resolves to a no-op emitter, so it is safe on every entry path.
        emitter().emit_event(
            event_type=EventType.PROGRESS_UPDATE,
            message="Checking the request...",
            metadata={"step": "pre_process"},
        )
        user_input = state.get("user_input", "")
        input_context = state.get("input_context", {})  # read-only

        if not _is_assessable(user_input):
            # An empty request is answered, not raised: an ERROR run ends as a terminal
            # failure event, which the chat surface leaves spinning.
            emit_trace_event("input_missing", {"node": "ValidateInputNode"}, state)
            return {
                "validation_error": _no_description_message(user_input),
                "status": AgentStatus.SUCCESS.value,
            }

        description = user_input.strip()
        payload = {"description": description}

        emit_trace_event(
            "input_validated",
            {"description_length": len(description)},
            state,
        )

        return {
            "validated_system_description": description,
            "validated_input": json.dumps(payload, ensure_ascii=False),
            "enriched_context": {
                "source": "ret-c2-163",
                "channel": input_context.get("channel", "unknown"),
            },
            "status": AgentStatus.SUCCESS.value,
        }
