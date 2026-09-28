# RET-C2-163 — Unit Tests: inner assessment nodes

import json

from framework.schemas.agent_status import AgentStatus
from src.nodes.compliance_assess_node import ComplianceAssessNode
from src.nodes.requirement_retrieve_node import RequirementRetrieveNode
from src.nodes.system_classify_node import SystemClassifyNode


class TestSystemClassifyNode:
    def setup_method(self):
        self.node = SystemClassifyNode()

    def test_hiring_use_case_high_risk(self):
        payload = {"description": "An AI system used for hiring and recruitment decisions."}
        result = self.node.execute({"user_input": json.dumps(payload), "node_history": [], "error_log": []})
        assert result["status"] == AgentStatus.SUCCESS.value
        assert result["high_risk"] is True
        assert "Annex III" in result["risk_category"]

    def test_invalid_payload_errors(self):
        result = self.node.execute({"user_input": "not-json", "node_history": [], "error_log": []})
        assert result["status"] == AgentStatus.ERROR.value


class TestRequirementRetrieveNode:
    def test_success_retrieves_requirements(self):
        node = RequirementRetrieveNode()
        state = {
            "risk_category": "Annex III(4) — employment",
            "validated_system_description": "hiring AI",
            "node_history": [],
            "error_log": [],
        }
        result = node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        assert len(result["retrieved_requirements"]) >= 1


class TestComplianceAssessNode:
    def test_high_risk_produces_action_plan(self):
        node = ComplianceAssessNode()
        state = {
            "high_risk": True,
            "risk_category": "Annex III(4) — employment",
            "retrieved_requirements": [
                {"rule_id": "EU AI Act Article 11", "domain": "technical_documentation", "text": "..."},
                {"rule_id": "EU AI Act Article 52", "domain": "transparency", "text": "..."},
            ],
            "node_history": [],
            "error_log": [],
        }
        result = node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        assert len(result["action_plan"]) >= 1
        assert result["citations"]

    def test_not_high_risk_flags_legal_review(self):
        node = ComplianceAssessNode()
        state = {
            "high_risk": False,
            "risk_category": "",
            "retrieved_requirements": [],
            "node_history": [],
            "error_log": [],
        }
        result = node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS.value
        assert result["documentation_requirements"] == []
        assert any("legal review" in step["guidance"].lower() for step in result["action_plan"])
