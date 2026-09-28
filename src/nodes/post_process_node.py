"""AgentCore Platform v1.0 — RET-C2-163 outer post_process node (AssessmentRender)."""

import re
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from shared.services.events import emitter
from shared.services.events.types import EventType
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.assessment_service import NOT_LEGAL_ADVICE_DISCLAIMER


_JA = re.compile(r"[぀-ヿ㐀-\u4dbf一-\u9fff]")


def _is_japanese(text: str) -> bool:
    return bool(_JA.search(text or ""))


def _render_unassessable(reason: str, japanese: bool) -> str:
    head = "評価できませんでした" if japanese else "Could not assess"
    return f"## {head}\n\n{reason}\n\n{NOT_LEGAL_ADVICE_DISCLAIMER}"


def _short(item: Any) -> str:
    """One line per obligation: what it is and where it comes from, not the full article."""
    if not isinstance(item, dict):
        return str(item)
    title = item.get("title") or item.get("step") or item.get("requirement_id") or ""
    where = item.get("article") or item.get("framework") or ""
    detail = item.get("guidance") or ""
    line = f"{title} ({where})" if title and where else (title or where or "")
    return f"{line} — {detail}" if detail else line


def _section(title: str, items: list[Any]) -> list[str]:
    if not items:
        return []
    return [f"**{title}**", *[f"- {_short(i)}" for i in items], ""]


def _render_report(report: dict[str, Any], japanese: bool) -> str:
    """What the caller needs first: the verdict, then what it obliges them to do.

    The full article text is deliberately left out — it is long, it is the same for every
    system in a category, and the citation says where to read it.
    """
    high = report.get("classification_status") == "HIGH_RISK"
    if japanese:
        verdict = "高リスクに該当します" if high else "分類を判定できませんでした — 法務確認が必要です"
        labels = ("判定", "区分", "根拠", "求められる文書", "透明性の義務", "次に行うこと", "出典")
        inconclusive_basis = (
            "提供された記述では Annex III のいずれかに該当するかを確認できませんでした。"
            "これは低リスクであるという判断ではありません。"
        )
        inconclusive_next = "より詳しいシステムの記述を用意し、分類を根拠にする前に法務確認を受けてください。"
    else:
        verdict = "High-risk under Annex III" if high else "Could not determine classification — legal review required"
        labels = (
            "Verdict",
            "Category",
            "Basis",
            "Documentation required",
            "Transparency obligations",
            "Next steps",
            "Sources",
        )
        inconclusive_basis = (
            "The supplied description does not establish a known Annex III pattern. "
            "This is not a low-risk determination."
        )
        inconclusive_next = (
            "Provide a fuller system description and obtain legal review before relying on any " "classification."
        )

    lines = [f"## {labels[0]} — {verdict}", ""]
    if report.get("risk_category"):
        lines += [f"**{labels[1]}** {report['risk_category']}", ""]
    if high:
        if report.get("rationale"):
            lines += [f"**{labels[2]}** {report['rationale']}", ""]
    else:
        # An unmatched description is reported as unresolved, never as a low-risk finding.
        lines += [f"**{labels[2]}** {inconclusive_basis}", ""]
        if report.get("rationale"):
            lines += [report["rationale"], ""]
    lines += _section(labels[3], report.get("documentation_requirements") or [])
    lines += _section(labels[4], report.get("transparency_obligations") or [])
    next_steps = list(report.get("action_plan") or [])
    if not high:
        next_steps = [inconclusive_next, *next_steps]
    lines += _section(labels[5], next_steps)
    citations = report.get("citations") or []
    if citations:
        lines += [f"**{labels[6]}** " + ", ".join(str(c) for c in citations), ""]
    lines.append(NOT_LEGAL_ADVICE_DISCLAIMER)
    return "\n".join(lines)


class AssessmentRenderNode(FunctionNode):
    """Outer post_process: assemble the final risk-classification + compliance
    assessment report (JSON-shaped) with the mandatory no-binding-legal-advice
    disclaimer.
    """

    required_trust_level: ClassVar[TrustLevel] = TrustLevel.VERIFIED_EXTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        # Progress (non-terminal) event for the caller. Outside the Marketplace runtime
        # this resolves to a no-op emitter, so it is safe on every entry path.
        emitter().emit_event(
            event_type=EventType.PROGRESS_UPDATE,
            message="Preparing the result...",
            metadata={"step": "post_process"},
        )
        # Nothing to assess is not a verdict: rendering "not high risk" would read as a
        # finding when nothing was examined.
        validation_error = state.get("validation_error")
        if validation_error:
            emit_trace_event("validation_reported", {"node": "AssessmentRenderNode"}, state)
            return {
                "formatted_output": _render_unassessable(validation_error, _is_japanese(state.get("user_input", ""))),
                "result": "COULD_NOT_ASSESS",
                "status": AgentStatus.SUCCESS.value,
            }

        report = {
            "classification_status": state.get("classification_status", "INCONCLUSIVE"),
            "high_risk": state.get("high_risk", False),
            "risk_category": state.get("risk_category", ""),
            "rationale": state.get("classification_rationale", ""),
            "documentation_requirements": state.get("documentation_requirements", []),
            "transparency_obligations": state.get("transparency_obligations", []),
            "action_plan": state.get("action_plan", []),
            "citations": state.get("citations", []),
            "disclaimer": NOT_LEGAL_ADVICE_DISCLAIMER,
        }

        emit_trace_event(
            "assessment_rendered",
            {"high_risk": report["high_risk"], "action_plan_steps": len(report["action_plan"])},
            state,
        )

        return {
            "assessment": report,
            "formatted_output": _render_report(report, _is_japanese(state.get("user_input", ""))),
            "result": "HIGH_RISK" if report.get("classification_status") == "HIGH_RISK" else "REQUIRES_LEGAL_REVIEW",
            "status": AgentStatus.SUCCESS.value,
        }
