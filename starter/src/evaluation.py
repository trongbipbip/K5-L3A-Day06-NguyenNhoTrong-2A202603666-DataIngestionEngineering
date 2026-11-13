"""Automatic retrieval evaluation and trace summarization."""
import re
from typing import Any


def _normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().casefold()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def evaluate_query(
    question: dict[str, Any],
    hits: list[dict[str, Any]],
) -> dict[str, Any]:
    """Mark retrieval hits using the documented gold source/page/evidence."""
    gold_sources = set(str(value) for value in _as_list(question.get("gold_source_id")))
    gold_pages = set(int(value) for value in _as_list(question.get("gold_page")))
    evidence_quotes = [
        _normalized(value)
        for value in (
            _as_list(question.get("evidence_quote"))
            + _as_list(question.get("evidence_quotes"))
        )
        if value
    ]

    annotated_hits: list[dict[str, Any]] = []
    matching_ranks: list[int] = []

    for rank, hit in enumerate(hits, start=1):
        source_match = (
            str(hit.get("document_id")) in gold_sources
            or str(hit.get("source")) in gold_sources
        )
        page_match = int(hit.get("page")) in gold_pages
        hit_text = _normalized(hit.get("text", ""))
        evidence_match = any(quote in hit_text for quote in evidence_quotes)
        is_hit = source_match and page_match and evidence_match

        annotated = dict(hit)
        annotated["rank"] = rank
        annotated["source_match"] = source_match
        annotated["page_match"] = page_match
        annotated["evidence_match"] = evidence_match
        annotated["is_gold_hit"] = is_hit
        annotated_hits.append(annotated)

        if is_hit:
            matching_ranks.append(rank)

    return {
        "question_id": question["id"],
        "split": question["split"],
        "question": question["question"],
        "gold_source_id": question.get("gold_source_id"),
        "gold_page": question.get("gold_page"),
        "evidence_quote": question.get("evidence_quote"),
        "hit_at_1": bool(matching_ranks and matching_ranks[0] == 1),
        "evidence_hit_at_3": bool(matching_ranks),
        "matching_ranks": matching_ranks,
        "hits": annotated_hits,
    }


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by strategy and split."""
    summary: dict[str, Any] = {}

    for trace in traces:
        strategy = trace["strategy"]
        split = trace["split"]
        bucket = summary.setdefault(strategy, {}).setdefault(
            split,
            {"total": 0, "hit_at_1": 0, "evidence_hit_at_3": 0},
        )
        bucket["total"] += 1
        bucket["hit_at_1"] += int(trace["hit_at_1"])
        bucket["evidence_hit_at_3"] += int(trace["evidence_hit_at_3"])

    for strategy_data in summary.values():
        for bucket in strategy_data.values():
            total = bucket["total"]
            bucket["hit_at_1_rate"] = (
                round(bucket["hit_at_1"] / total, 4) if total else 0.0
            )
            bucket["evidence_hit_at_3_rate"] = (
                round(bucket["evidence_hit_at_3"] / total, 4)
                if total
                else 0.0
            )

    return summary
