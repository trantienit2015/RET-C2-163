"""AgentCore Platform v1.0 — RET-C2-163 inner step 2: RequirementRetrieve."""

from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.eu_act_retrieval_service import hybrid_retrieve


class RequirementRetrieveNode(FunctionNode):
    """Inner step 2: hybrid retrieval (dense e5 + BM25 for article numbers) over the
    EU AI Act + METI v1.2 KB, scoped to the classified risk category.
    """

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def __init__(self, retriever: Any | None = None, top_k: int = 8, hybrid_search: bool = True):
        self._retriever = retriever
        self._top_k = top_k
        self._hybrid_search = hybrid_search

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        risk_category = state.get("risk_category", "")
        description = state.get("validated_system_description", "")

        query = risk_category or description
        requirements = hybrid_retrieve(
            query,
            top_k=self._top_k,
            hybrid_search=self._hybrid_search,
            retriever=self._retriever,
        )

        emit_trace_event(
            "requirements_retrieved",
            {"requirement_count": len(requirements)},
            state,
        )

        return {"retrieved_requirements": requirements, "status": AgentStatus.SUCCESS.value}
