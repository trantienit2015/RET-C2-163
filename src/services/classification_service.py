"""High-risk classification under EU AI Act Annex III (deterministic baseline).

Classification is LLM-driven when a client is injected; otherwise a deterministic
keyword-based heuristic maps retail AI use cases to Annex III high-risk categories.
Ambiguous systems are flagged for legal review rather than defaulted to low-risk.
"""

from __future__ import annotations

from typing import Any, Protocol

# Annex III high-risk categories relevant to retail AI use cases.
_HIGH_RISK_USE_CASES = {
    "hiring": "Annex III(4) — employment, workers management and access to self-employment",
    "recruitment": "Annex III(4) — employment, workers management and access to self-employment",
    "credit_scoring": "Annex III(5)(b) — creditworthiness evaluation",
    "pricing": None,  # dynamic pricing is NOT categorically Annex III — requires review
}


class Classifier(Protocol):
    """Surface the injected object must expose."""

    def classify(self, description: str) -> dict[str, Any]: ...


def classify_system(description: str, llm: "Classifier | None" = None) -> dict[str, Any]:
    """Return {"high_risk": bool, "risk_category": str, "rationale": str}."""
    if llm is not None and hasattr(llm, "classify"):
        return llm.classify(description)

    text = (description or "").lower()

    if any(k in text for k in ("hiring", "recruitment", "採用", "人事")):
        return {
            "classification_status": "HIGH_RISK",
            "high_risk": True,
            "risk_category": _HIGH_RISK_USE_CASES["hiring"],
            "rationale": "System performs hiring/HR-related decisions — Annex III(4) employment category.",
        }
    if any(k in text for k in ("credit", "loan", "与信", "融資")):
        return {
            "classification_status": "HIGH_RISK",
            "high_risk": True,
            "risk_category": _HIGH_RISK_USE_CASES["credit_scoring"],
            "rationale": "System evaluates creditworthiness — Annex III(5)(b) category.",
        }
    if any(k in text for k in ("recommend", "推薦", "レコメンド")):
        return {
            "classification_status": "INCONCLUSIVE",
            "high_risk": False,
            "risk_category": "",
            "rationale": (
                "Recommendation engine described without a hiring/credit/biometric signal — "
                "not categorically Annex III high-risk on the information available. "
                "Flag for legal review if the recommendation influences access to essential services."
            ),
        }
    if any(k in text for k in ("pricing", "価格", "値付け")):
        return {
            "classification_status": "INCONCLUSIVE",
            "high_risk": False,
            "risk_category": "",
            "rationale": (
                "Dynamic pricing is not a categorical Annex III high-risk use case. "
                "Requires legal review if pricing affects access to essential services or is discriminatory."
            ),
        }

    return {
        "classification_status": "INCONCLUSIVE",
        "high_risk": False,
        "risk_category": "",
        "rationale": "System description does not match a known Annex III high-risk pattern — requires legal review.",
    }
