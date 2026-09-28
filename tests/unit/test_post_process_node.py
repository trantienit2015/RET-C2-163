# RET-C2-163 — Unit Tests: AssessmentRenderNode (post_process)

from framework.schemas.agent_status import AgentStatus
from src.nodes.post_process_node import AssessmentRenderNode


class TestAssessmentRenderNode:
    def setup_method(self):
        self.node = AssessmentRenderNode()

    def test_high_risk_report(self):
        state = {
            "classification_status": "HIGH_RISK",
            "high_risk": True,
            "risk_category": "Annex III(4) — employment",
            "classification_rationale": "hiring use case",
            "documentation_requirements": ["doc1"],
            "transparency_obligations": ["obligation1"],
            "action_plan": [{"step": "s1", "guidance": "g1"}],
            "citations": ["EU AI Act Annex III(4)"],
            "node_history": [],
            "error_log": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        out = result["assessment"]
        assert out["high_risk"] is True
        assert result["result"] == "HIGH_RISK"
        assert out["disclaimer"]

    def test_an_unmatched_description_is_reported_as_unresolved(self):
        """No Annex III match is not a finding of low risk: rendering it as one would let a
        caller act on a verdict the agent never reached."""
        result = self.node.execute({"node_history": [], "error_log": []})
        assert result["status"] == AgentStatus.SUCCESS.value
        assert result["result"] == "REQUIRES_LEGAL_REVIEW"
        report = result["formatted_output"]
        assert "Could not determine classification" in report
        assert "legal review" in report
        assert "Not high-risk" not in report
        assert "not a low-risk determination" in report
