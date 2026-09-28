"""AgentCore Platform v1.0 — RET-C2-163 inner domain workflow graph (Cat 2).

Linear: START → system_classify → requirement_retrieve → compliance_assess → END
"""

from typing import Any

from framework.graph.base_graph import BaseGraph
from framework.schemas.agent_state import AgentState
from framework.schemas.agent_status import AgentStatus
from langgraph.graph import END, START

from src.nodes.compliance_assess_node import ComplianceAssessNode
from src.nodes.requirement_retrieve_node import RequirementRetrieveNode
from src.nodes.system_classify_node import SystemClassifyNode
from src.schemas.state import State


class EuAiActWorkflowGraph(BaseGraph):
    """Inner graph for the retail EU AI Act high-risk assessment workflow."""

    @property
    def name(self) -> str:
        return "ret_eu_ai_act_workflow"

    @property
    def state_schema(self) -> type:
        return State

    def _validate_config(self) -> None:
        pass

    def register_nodes(self) -> None:
        cfg = self.config if hasattr(self, "config") and self.config else {}
        llm = cfg.get("llm")
        retriever = cfg.get("retriever")
        top_k = cfg.get("top_k", 8)
        hybrid_search = cfg.get("hybrid_search", True)

        self._nodes["system_classify"] = SystemClassifyNode(llm=llm)
        self._nodes["requirement_retrieve"] = RequirementRetrieveNode(
            retriever=retriever, top_k=top_k, hybrid_search=hybrid_search
        )
        self._nodes["compliance_assess"] = ComplianceAssessNode()

    def add_edges(self) -> None:
        self._sg.add_edge(START, "system_classify")
        self._sg.add_edge("system_classify", "requirement_retrieve")
        self._sg.add_edge("requirement_retrieve", "compliance_assess")
        self._sg.add_edge("compliance_assess", END)

    def route(self, state: AgentState) -> str:
        return END if state.get("status") == AgentStatus.ERROR.value else "compliance_assess"

    def get_output(self, state: AgentState) -> dict[str, Any]:
        return {
            "classification_status": state.get("classification_status", "INCONCLUSIVE"),
            "high_risk": state.get("high_risk", False),
            "risk_category": state.get("risk_category", ""),
            "classification_rationale": state.get("classification_rationale", ""),
            "retrieved_requirements": state.get("retrieved_requirements", []),
            "documentation_requirements": state.get("documentation_requirements", []),
            "transparency_obligations": state.get("transparency_obligations", []),
            "action_plan": state.get("action_plan", []),
            "citations": state.get("citations", []),
            "status": state.get("status"),
            "trace_id": state.get("trace_id"),
            "correlation_id": state.get("correlation_id"),
            "node_history": state.get("node_history", []),
        }
