# RET-C2-163 — Integration Tests: full graph compile + invoke (Cat 2)

from framework.schemas.agent_status import AgentStatus
from framework.schemas.invocation_context import InvocationContext
from framework.schemas.trust_level import TrustLevel
from src.graph.graph import Graph
from src.services.assessment_service import NOT_LEGAL_ADVICE_DISCLAIMER


def _ctx():
    return InvocationContext(
        session_id="it-1",
        caller_trust_level=TrustLevel.VERIFIED_EXTERNAL,
        caller_id="tester",
    )


class TestGraphIntegration:
    def test_high_risk_pipeline_success(self):
        agent = Graph()
        agent.compile()
        result = agent.invoke(
            "An AI-driven hiring and recruitment screening system for retail store staff.",
            ctx=_ctx(),
        )
        assert result["status"] == AgentStatus.SUCCESS.value
        assert not isinstance(result["status"], AgentStatus)
        assert len(result.get("node_history", [])) >= 5
        report = result["output"]
        assert isinstance(report, str), "the caller reads this — it must not be a raw dict"
        assert "Annex III(4)" in report
        assert NOT_LEGAL_ADVICE_DISCLAIMER in report

    def test_an_unmatched_description_requires_legal_review(self):
        agent = Graph()
        agent.compile()
        result = agent.invoke("A product recommendation engine for the online storefront.", ctx=_ctx())
        report = result["output"]
        assert "Could not determine classification" in report
        assert "Not high-risk" not in report, "an unmatched description must not read as a verdict"
        assert NOT_LEGAL_ADVICE_DISCLAIMER in report

    def test_a_request_with_nothing_to_assess_is_answered(self):
        """It ends with the reason the caller can act on, not as a failure the chat surface
        leaves spinning."""
        agent = Graph()
        agent.compile()
        result = agent.invoke("", ctx=_ctx())
        assert result["status"] == AgentStatus.SUCCESS.value
        assert not isinstance(result["status"], AgentStatus)
        assert "Could not assess" in result["output"]
        assert len(result.get("node_history", [])) >= 3
