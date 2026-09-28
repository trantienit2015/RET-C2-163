"""AgentCore Platform v1.0 — RET-C2-163 state schema."""

# ADR-005: State must be a flat TypedDict — never Pydantic BaseModel.
# LangGraph checkpoints use msgpack serialization; Pydantic objects
# cause silent corruption. Extend AgentState with agent-specific
# fields only. Do NOT add credentials, secrets, or Pydantic models.

from typing import Any, NotRequired

from framework.schemas.agent_state import AgentState


class State(AgentState):
    """Retail EU AI Act high-risk assessment state.

    Shared fields (user_input, status, session_id, node_history, error_log,
    validated_input, hitl_*, etc.) inherited from AgentState. Only
    assessment-specific fields below — flat, JSON-serializable primitives only.

    Every field here is written by the step that produces it and is absent until then.
    Nodes return the fields they changed, not the whole state, and a request that carries
    nothing to assess stops before the inner workflow runs at all — so declaring these
    required states a contract the pipeline does not keep, and hides which field exists
    only after which step.
    """

    # pre_process (ValidateInput) output
    validated_system_description: NotRequired[str]

    # Set when the request carried nothing to assess; the render node reports it instead of
    # a verdict.
    validation_error: NotRequired[str]

    # inner: SystemClassify
    # HIGH_RISK when an Annex III category matched; INCONCLUSIVE when none did — which is not
    # a finding of low risk, and is never rendered as one.
    classification_status: NotRequired[str]
    high_risk: NotRequired[bool]
    risk_category: NotRequired[str]
    classification_rationale: NotRequired[str]

    # inner: RequirementRetrieve
    retrieved_requirements: NotRequired[list[dict[str, Any]]]

    # inner: ComplianceAssess
    documentation_requirements: NotRequired[list[str]]
    transparency_obligations: NotRequired[list[str]]
    action_plan: NotRequired[list[dict[str, Any]]]
    citations: NotRequired[list[str]]
