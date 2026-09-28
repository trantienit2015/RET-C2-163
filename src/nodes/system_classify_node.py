"""AgentCore Platform v1.0 — RET-C2-163 inner step 1: SystemClassify."""

import json
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.classification_service import classify_system


class SystemClassifyNode(FunctionNode):
    """Inner step 1: classify whether the described retail AI system is high-risk
    under EU AI Act Annex III, using retail use-case context.
    """

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def __init__(self, llm: Any | None = None) -> None:
        self._llm = llm

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        raw = state.get("user_input", "")
        try:
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except (ValueError, TypeError):
            payload = None

        if not isinstance(payload, dict) or not payload.get("description"):
            return {
                "status": AgentStatus.ERROR.value,
                "error_log": ["SystemClassifyNode: missing/invalid inner payload"],
            }

        result = classify_system(payload["description"], llm=self._llm)

        emit_trace_event(
            "system_classified",
            {"classification_status": result.get("classification_status"), "high_risk": result["high_risk"]},
            state,
        )

        return {
            "validated_system_description": payload["description"],
            "classification_status": result.get("classification_status", "INCONCLUSIVE"),
            "high_risk": result["high_risk"],
            "risk_category": result["risk_category"],
            "classification_rationale": result["rationale"],
            "status": AgentStatus.SUCCESS.value,
        }
