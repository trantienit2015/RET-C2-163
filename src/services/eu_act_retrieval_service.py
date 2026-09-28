"""Hybrid retrieval over the EU AI Act + METI AI事業者ガイドライン v1.2 KB."""

from __future__ import annotations

from typing import Any, Protocol

# Seed regulatory corpus (deterministic fallback when no retriever is injected).
# Sources: EU AI Act (Regulation (EU) 2024/1689), Annex III, Article 52 transparency
# obligations, and METI AI事業者ガイドライン v1.2 (March 2026).
_SEED_CORPUS: list[dict[str, Any]] = [
    {
        "rule_id": "EU AI Act Annex III(4)",
        "domain": "hiring",
        "text": "AI systems intended to be used for recruitment or selection of natural persons, "
        "in particular for placing targeted job advertisements, analysing and filtering job "
        "applications, and evaluating candidates, are classified as high-risk.",
    },
    {
        "rule_id": "EU AI Act Annex III(5)(b)",
        "domain": "credit_scoring",
        "text": "AI systems intended to be used to evaluate the creditworthiness of natural persons "
        "or establish their credit score are classified as high-risk, with certain exceptions for "
        "detecting financial fraud.",
    },
    {
        "rule_id": "EU AI Act Article 9",
        "domain": "risk_management",
        "text": "Providers of high-risk AI systems shall establish, implement, document and maintain "
        "a risk management system throughout the entire lifecycle of the high-risk AI system.",
    },
    {
        "rule_id": "EU AI Act Article 11",
        "domain": "technical_documentation",
        "text": "Providers of high-risk AI systems shall draw up technical documentation before the "
        "system is placed on the market, and keep it up to date.",
    },
    {
        "rule_id": "EU AI Act Article 52",
        "domain": "transparency",
        "text": "Providers shall ensure that AI systems intended to interact with natural persons are "
        "designed and developed so that the natural persons are informed that they are interacting "
        "with an AI system, unless this is obvious.",
    },
    {
        "rule_id": "METI AI事業者ガイドライン v1.2 第3章",
        "domain": "transparency",
        "text": "AI事業者は、AIシステムの利用者に対し、AIが利用されていることを分かりやすく開示し、判断根拠の説明可能性を確保する努力を行うことが求められる。",
    },
    {
        "rule_id": "METI AI事業者ガイドライン v1.2 第4章",
        "domain": "risk_management",
        "text": "AI事業者は、AIシステムのリスク評価を継続的に実施し、開発・提供・利用の各段階でリスク低減措置を講じるべきである。",
    },
]


class Retriever(Protocol):
    """Surface the injected object must expose."""

    def search(self, query: str, *, top_k: int, hybrid_search: bool) -> list[dict[str, Any]]: ...


def hybrid_retrieve(
    query: str, top_k: int = 8, hybrid_search: bool = True, retriever: "Retriever | None" = None
) -> list[dict[str, Any]]:
    """Retrieve matching EU AI Act / METI passages for the classified category.

    If ``retriever`` is injected it must expose ``search(query, top_k, hybrid_search)``.
    Otherwise a deterministic keyword overlap over the seed corpus is used.
    """
    if retriever is not None:
        return retriever.search(query, top_k=top_k, hybrid_search=hybrid_search)

    q = (query or "").lower()
    scored = []
    for rule in _SEED_CORPUS:
        overlap = sum(
            1
            for kw in (
                "hiring",
                "credit",
                "risk",
                "documentation",
                "transparency",
                "annex",
                "article",
                "採用",
                "リスク",
                "説明",
            )
            if kw in q or kw in rule["text"].lower()
        )
        scored.append((overlap, rule))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [dict(r, score=0.7) for _s, r in scored[:top_k]]
