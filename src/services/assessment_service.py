"""Compliance assessment: documentation/transparency requirements + action plan.

Assembly is deterministic; the mandatory no-binding-legal-advice disclaimer and
citation trail are always produced (S-3 discipline) — never silently suppressed.
"""

from __future__ import annotations

from typing import Any

NOT_LEGAL_ADVICE_DISCLAIMER = (
    "This assessment is generated for self-evaluation support and does not constitute "
    "binding legal advice, a conformity certification, or an official regulatory decision. "
    "Verify against the cited EU AI Act / METI v1.2 sources and consult qualified legal "
    "counsel before acting, especially for ambiguous or borderline classifications."
)


def assemble_assessment(high_risk: bool, risk_category: str, requirements: list[dict[str, Any]]) -> dict[str, Any]:
    """Return {"documentation_requirements", "transparency_obligations", "action_plan", "citations"}."""
    if not high_risk:
        return {
            "documentation_requirements": [],
            "transparency_obligations": [
                "General AI-interaction disclosure recommended even for non-high-risk systems "
                "(METI v1.2 transparency guidance)."
            ],
            "action_plan": [
                {
                    "step": "Legal review",
                    "guidance": "System not categorically Annex III high-risk on the information "
                    "provided — flag for legal review before finalizing the classification.",
                }
            ],
            "citations": sorted({r["rule_id"] for r in requirements if r.get("rule_id")}),
        }

    doc_reqs = [r["text"] for r in requirements if r.get("domain") == "technical_documentation"]
    if not doc_reqs:
        doc_reqs = ["Technical documentation per EU AI Act Article 11 (lifecycle-maintained)."]

    transparency = [r["text"] for r in requirements if r.get("domain") == "transparency"]
    if not transparency:
        transparency = ["AI-interaction disclosure per EU AI Act Article 52 + METI v1.2."]

    action_plan = [
        {
            "step": "Risk management system",
            "guidance": f"Establish an EU AI Act Article 9 risk management system for the {risk_category} use case.",
        },
        {
            "step": "Technical documentation",
            "guidance": "Draw up and maintain technical documentation per Article 11.",
        },
        {
            "step": "Transparency disclosure",
            "guidance": "Implement AI-interaction disclosure per Article 52 + METI v1.2 §3.",
        },
    ]

    citations = sorted({r["rule_id"] for r in requirements if r.get("rule_id")})

    return {
        "documentation_requirements": doc_reqs,
        "transparency_obligations": transparency,
        "action_plan": action_plan,
        "citations": citations,
    }
