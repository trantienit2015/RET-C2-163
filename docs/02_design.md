# RET-C2-163 — Design Specification

Retail AI System EU AI Act High-Risk Assessment & Compliance Q&A Agent.

## Position in AgentCore Architecture

- **Agent Class**: `EuAiActAssessmentAgent`
- **L1 Base**: `AgentBaseGraph` (Level 1 direct inheritance).
- **Category**: Cat 2 (multi-step classify → retrieve → assess pipeline for a specific job).
- **Three-Layer Separation**:
  - State: flat `TypedDict` extending `AgentState`.
  - Node: L1 inheritance (`FunctionNode.execute(self, state) -> dict`).
  - Graph: outer `AgentBaseGraph` + `GraphNode` (`main`) + inner `BaseGraph` subgraph.

## Architecture (Cat 2)

```
OUTER (AgentBaseGraph — src/graph/graph.py):
  initialize → pre_process(ValidateInput) → main(GraphNode) → post_process(AssessmentRender) → finalize
                                                 │ get_subgraph().invoke(validated_input, ctx)
                                                 ▼
INNER (BaseGraph — src/graph/domain_workflow_graph.py):
  START → system_classify → requirement_retrieve → compliance_assess → END
```

### Node Configuration

| Node | Layer | Responsibility | Output |
|------|-------|----------------|--------|
| ValidateInputNode | outer pre_process | S-1 trust; hold back a request with no system to assess; serialize JSON | validated_system_description, validated_input |
| AssessmentGraphNode | outer main (GraphNode) | invoke inner subgraph; merge results | merged output |
| SystemClassifyNode | inner | classify high-risk under EU AI Act Annex III using retail use-case context | high_risk, risk_category, classification_rationale |
| RequirementRetrieveNode | inner | hybrid retrieval (e5 + BM25) over EU AI Act + METI v1.2 KB, scoped to risk category | retrieved_requirements |
| ComplianceAssessNode | inner | S-3 output gate: documentation/transparency obligations + action plan; disclaimer always produced | documentation_requirements, transparency_obligations, action_plan, citations |
| AssessmentRenderNode | outer post_process | assemble report + mandatory no-binding-legal-advice disclaimer | formatted_output |

### Cat 2 data flow note

Inner subgraph receives only the `user_input` string (serialized `validated_input` JSON)
plus `InvocationContext`. `SystemClassifyNode` `json.loads` the payload. Config (`top_k`,
`hybrid_search`, `llm`, `retriever`) reaches inner nodes via `AssessmentGraphNode._parent_config()`.

### State Definition (agent-specific fields)

validated_system_description, validation_error, classification_status, high_risk, risk_category,
classification_rationale, retrieved_requirements, documentation_requirements,
transparency_obligations, action_plan, citations. Flat TypedDict only; no
credentials/Pydantic/InvocationContext.

All of them are optional in the schema. Nodes return the fields they changed rather than the
whole state, and a request carrying nothing to assess stops before the inner workflow runs, so
a field exists only once its step has run. Declaring them required would state a contract the
pipeline does not keep.

`classification_status` is `HIGH_RISK` when an Annex III category matched and `INCONCLUSIVE`
when none did. `INCONCLUSIVE` is never rendered as a low-risk finding: the caller is told the
classification could not be determined and that legal review is required, and the structured
result is `REQUIRES_LEGAL_REVIEW` rather than `NOT_HIGH_RISK`.

`validation_error` is set when the request carries no system to assess. It short-circuits the
pipeline: the subgraph is skipped, and the render node reports `COULD_NOT_ASSESS` instead of a
verdict — a request that was never examined must not be answered with one.

## Security Model (5-layer)

- **S-1**: `required_trust_level: VERIFIED_EXTERNAL` declared explicitly on every node
  (agent.yaml carries the agent-level default), framework-enforced.
- **S-2**: a request carrying no system to assess is held back at ValidateInputNode — it does
  not reach classification or retrieval. The run ends normally with `validation_error` and the
  render node reports `COULD_NOT_ASSESS`, rather than as a failure the caller cannot read.
  Substance, not length, decides: distinct content words that are not merely salutations.
- **S-3 Secret Isolation**: `bound_secrets()`/`secrets_factory()`/`provision_secrets()`; no `os.environ`.
  **Output discipline**: required obligations + no-binding-legal-advice disclaimer always
  produced — never silently suppressed. Ambiguous systems are flagged for legal review
  rather than defaulted to low-risk.
- **S-4**: `emit_trace_event()` called at least once inside every node's `execute()`
  (input_validated, system_classified, requirements_retrieved, compliance_assessed,
  assessment_rendered) — regardless of side effects.
- **S-5**: import-time credential scan; no credentials in source/state.
- **Import isolation**: no agenticstar / mediator / other-agent imports.

## Composition Pattern

- **Pattern**: GraphNode (inner subgraph), `error_strategy = "propagate"`, `propagate_hitl = False`.

## Import Isolation Confirmation

- No Level 0 imports; only `framework/` + `shared/`.

## Design Decision Record

| Decision | Chosen | Rationale |
|----------|--------|-----------|
| L1 base type | AgentBaseGraph | Cat 2 fixed pipeline |
| Composition | GraphNode + inner BaseGraph | Cat 2 multi-step (gate-composition) |
| Retrieval | hybrid (e5 + BM25) | article-number + semantic recall over EU AI Act + METI v1.2 |
| Classification | deterministic keyword baseline + LLM hook, ambiguous → legal-review flag | avoid false low-risk defaults on ambiguous systems |
| Assessment | always cited + disclaimer, never suppressed | S-3 compliance-evidence discipline |
| Unmatched description | `INCONCLUSIVE` → `REQUIRES_LEGAL_REVIEW`, never rendered as low-risk | a verdict the agent did not reach must not be actionable |

## 1. Deployment entry points

The agent is reachable through two entry points, and both resolve their runtime inputs the same way.

| Entry point | File | Used by |
|---|---|---|
| Standalone HTTP | `src/api/server.py` | staging rehearsal, direct invocation |
| Marketplace one-shot Pod | `cli.py` | the platform runner (container `CMD`) |

Both read runtime parameters from `config/config.yaml` — the manifest carries discovery metadata
only — and both scope secrets to the same location (`namespace=ret`, `agent_name=ret-c2-163`), so a
secret provisioned for one path resolves identically on the other.

**No LLM client is constructed at either entry point.** The pipeline is deterministic; a client
may still be injected through `config["llm"]` by a caller that has one.

**Progress events.** Each pipeline stage emits a non-terminal progress event at its start, so a
caller sees the run advancing. Outside the Marketplace runtime the emitter resolves to a no-op, so
the same code is safe on every path. Terminal events belong to the platform runner and are never
emitted by this agent.

**Caller authentication at the standalone entry point.** A caller that no upstream middleware
vouched for stays anonymous unless it presents a deployment-level credential: the external bearer
token grants the verified-external level, and a separate staging-only runner credential is the only
way to reach the internal level. Trust established upstream is never changed.
