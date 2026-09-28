"""AgentCore Platform v1.0 — RET-C2-163 outer graph (Cat 2).

Retail AI System EU AI Act High-Risk Assessment & Compliance Q&A Agent.
L1 Base: AgentBaseGraph (Level 1 direct inheritance).

Outer backbone (fixed):
    initialize → pre_process(ValidateInput) → main(GraphNode)
              → post_process(AssessmentRender) → finalize
"""

from typing import Any, ClassVar

from framework.graph.agent_base_graph import AgentBaseGraph
from shared.services.events import emitter
from shared.services.events.types import EventType
from framework.nodes.graph_node import GraphNode
from framework.schemas.agent_state import AgentState
from framework.schemas.agent_status import AgentStatus

from src.nodes.post_process_node import AssessmentRenderNode
from src.nodes.pre_process_node import ValidateInputNode
from src.schemas.state import State


class AssessmentGraphNode(GraphNode):
    """Wraps the inner EU AI Act assessment subgraph (`main` slot)."""

    error_strategy: ClassVar[str] = "propagate"
    propagate_hitl: ClassVar[bool] = False

    def __init__(
        self, llm: Any | None = None, retriever: Any | None = None, top_k: int = 8, hybrid_search: bool = True
    ):
        super().__init__()
        self._llm = llm
        self._retriever = retriever
        self._top_k = top_k
        self._hybrid_search = hybrid_search

    def execute(self, state: AgentState) -> dict[str, Any]:
        # Nothing to assess: skip the subgraph rather than run it on an empty description.
        if state.get("validation_error"):
            return {"status": AgentStatus.SUCCESS.value}
        result: dict[str, Any] = super().execute(state)
        return result

    def get_subgraph(self) -> AgentBaseGraph:
        from src.graph.domain_workflow_graph import EuAiActWorkflowGraph

        sg = EuAiActWorkflowGraph(config=self._parent_config())
        sg.compile()
        return sg

    def extract_input(self, state: AgentState) -> str:
        # Progress (non-terminal) event for the caller, emitted as the subgraph step
        # begins. Outside the Marketplace runtime this is a no-op emitter.
        emitter().emit_event(
            event_type=EventType.PROGRESS_UPDATE,
            message="Working on the request...",
            metadata={"step": "main"},
        )
        value = state.get("validated_input", state.get("user_input", ""))
        return value if isinstance(value, str) else str(value)

    def merge_output(self, state: AgentState, sub_result: dict[str, Any]) -> dict[str, Any]:
        return {
            "classification_status": sub_result.get("classification_status", "INCONCLUSIVE"),
            "high_risk": sub_result.get("high_risk", False),
            "risk_category": sub_result.get("risk_category", ""),
            "classification_rationale": sub_result.get("classification_rationale", ""),
            "retrieved_requirements": sub_result.get("retrieved_requirements", []),
            "documentation_requirements": sub_result.get("documentation_requirements", []),
            "transparency_obligations": sub_result.get("transparency_obligations", []),
            "action_plan": sub_result.get("action_plan", []),
            "citations": sub_result.get("citations", []),
            "status": sub_result.get("status"),
        }

    def _parent_config(self) -> dict[str, Any]:
        return {
            "llm": self._llm,
            "retriever": self._retriever,
            "top_k": self._top_k,
            "hybrid_search": self._hybrid_search,
        }


class EuAiActAssessmentAgent(AgentBaseGraph):
    """Cat 2 outer graph — Retail EU AI Act High-Risk Assessment."""

    @property
    def name(self) -> str:
        return "ret-c2-163"

    @property
    def state_schema(self) -> type:
        return State

    def register_nodes(self) -> None:
        super().register_nodes()  # injects initialize + finalize
        cfg = self.config if hasattr(self, "config") and self.config else {}
        self._nodes["pre_process"] = ValidateInputNode()
        self._nodes["main"] = AssessmentGraphNode(
            llm=cfg.get("llm"),
            retriever=cfg.get("retriever"),
            top_k=cfg.get("top_k", 8),
            hybrid_search=cfg.get("hybrid_search", True),
        )
        self._nodes["post_process"] = AssessmentRenderNode()

    # add_edges() is NOT overridden — backbone wiring belongs to the framework.


# Stable alias for the standalone entry point import (src/api/server.py).
Graph = EuAiActAssessmentAgent
