"""AgentCore Platform v1.0 — RET-C2-163 inner step 3: ComplianceAssess."""

from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.assessment_service import assemble_assessment


class ComplianceAssessNode(FunctionNode):
    """Inner step 3 (S-3 output gate): assess required technical documentation,
    conformity assessments, and transparency obligations (EU Art.52 + METI v1.2);
    produce a checklist + action plan. Obligations + no-legal-advice disclaimer are
    always produced — never silently suppressed.
    """

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        high_risk = state.get("high_risk", False)
        risk_category = state.get("risk_category", "")
        requirements = state.get("retrieved_requirements", [])

        result = assemble_assessment(high_risk, risk_category, requirements)

        emit_trace_event(
            "compliance_assessed",
            {"high_risk": high_risk, "action_plan_steps": len(result["action_plan"])},
            state,
        )

        return {
            "documentation_requirements": result["documentation_requirements"],
            "transparency_obligations": result["transparency_obligations"],
            "action_plan": result["action_plan"],
            "citations": result["citations"],
            "status": AgentStatus.SUCCESS.value,
        }
