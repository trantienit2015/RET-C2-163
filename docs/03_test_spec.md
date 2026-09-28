# RET-C2-163 — Test Specification

## Test Strategy

- Test types: Unit (per node) + Integration (full graph) + Proof-of-Boundary.
- Each node ≥1 success + ≥1 error/edge; ≥1 full-graph compile+invoke.
- LLM/retriever injected as fakes / deterministic seed KB.

## Framework Compliance Tests (TC)

| TC-ID | Test | Where | Expected |
|-------|------|-------|----------|
| TC-01 | State flat TypedDict; no Pydantic | tests/proof_of_boundary/test_state_safety.py | pass |
| TC-02a | Unmatched description → REQUIRES_LEGAL_REVIEW (never "Not high-risk") | test_post_process_node / test_graph | classification_status INCONCLUSIVE, "Could not determine classification" rendered |
| TC-02 | A request with no system to assess → answered, not failed |  test_pre_process_node / test_inner_nodes | status SUCCESS, `validation_error` set, `COULD_NOT_ASSESS` rendered; padding and greetings included |
| TC-03 | No credentials in source/state | gate-credential-scan + state_safety | pass |
| TC-04 | Secrets via provider pattern, not os.environ | src/api/server.py | pass |
| TC-05 | emit_trace_event in every node's execute() | all src/nodes/*.py | trace emitted |
| TC-06 | Node statelessness | code review | pass |
| TC-07 | No `_invoke_impl`; execute(self, state) | test_pre_process_node.test_execute_signature | pass |
| TC-08 | S-1 trust gate (VERIFIED_EXTERNAL, declared on every node) | config/agent.yaml + src/nodes/*.py | enforced |

## Proof-of-Boundary Tests (PB)

| PB-ID | Boundary | Where | Expected |
|-------|----------|-------|----------|
| PB-2 | State serialization (primitives only) | test_state_safety.py | pass |
| PB-4 | Import isolation (no Level 0) | test_import_isolation.py | 0 violations |
| PB-6 | Invoke execution order (S-1→S-4→S-2→execute→S-3→S-4) for every node | test_pb_invoke_order.py | order verified |
| PB-DISC | No-binding-legal-advice disclaimer always present (S-3) | test_post_process_node / test_graph | disclaimer present in both branches |

## Node Coverage

| Node | Success | Error/edge |
|------|---------|-----------|
| ValidateInputNode | test_success_serializes_payload | test_empty_input_is_answered_not_failed |
| SystemClassifyNode | test_hiring_use_case_high_risk | test_invalid_payload_errors |
| RequirementRetrieveNode | test_success_retrieves_requirements | — |
| ComplianceAssessNode | test_high_risk_produces_action_plan | test_not_high_risk_flags_legal_review |
| AssessmentRenderNode | test_high_risk_report | test_not_high_risk_defaults |

## Execution Summary

- Local: unit + integration + proof_of_boundary pass; ruff clean.
- CI: gate-* + run-tests on GitLab pipeline.

## 1. Deployment path tests

### TC-DEP-01 Marketplace entry point identity — `tests/unit/test_cli_entry_point.py`

| Case | Expected |
|---|---|
| Identity is concrete | `agent_name` / `namespace` are non-empty and not the runner default |
| Identity matches the HTTP entry point | the values equal what `src/api/server.py` passes to `secrets_factory`; where that entry point provisions no secrets, they equal the manifest `namespace` and the lower-cased template id |
| The runner call uses the constants | `run_agent_marketplace` is called with the module constants, not inline literals |

### TC-DEP-02 Standalone entry point boundary — `tests/proof_of_boundary/test_server_llm_injection.py`

| Case | Expected |
|---|---|
| Boots with no credential provisioned | the module imports and the app/agent objects are constructed |
| External bearer never reaches the internal level | resolves to the verified-external level |
| Staging runner credential reaches the internal level | resolves to the internal level |
| Wrong or missing bearer while auth is enabled | rejected with 401 |
