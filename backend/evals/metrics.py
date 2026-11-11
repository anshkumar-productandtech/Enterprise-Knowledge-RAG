"""Metric definitions. Kept free of I/O so each one can be unit-tested and explained in one line.

hit@k        share of answerable questions where at least one expected page is in the top k chunks
all-sources  same, but every expected page must be present (matters for multi-source questions)
MRR          mean of 1/rank of the first expected page (0 when missing): rewards putting it first
refusal acc  share of unanswerable questions the assistant declined to answer
false refuse share of answerable questions it wrongly declined
pass rate    share of ALL questions handled correctly: unanswerable -> refused,
             answerable -> answered with judge correctness >= threshold
"""

from __future__ import annotations

import math
from statistics import mean
from typing import Iterable, Sequence


def retrieval_scores(retrieved_urls: Sequence[str], expected_urls: Iterable[str]) -> dict:
    expected = set(expected_urls)
    ranks = [i for i, url in enumerate(retrieved_urls, start=1) if url in expected]
    return {
        "hit": bool(ranks),
        "all_sources": expected <= set(retrieved_urls),
        "reciprocal_rank": 1.0 / ranks[0] if ranks else 0.0,
    }


def percentile(values: Sequence[float], p: float) -> float | None:
    """Nearest-rank percentile. p in [0, 100]."""
    if not values:
        return None
    ordered = sorted(values)
    k = max(1, math.ceil(p / 100 * len(ordered)))
    return ordered[k - 1]


def _mean(values: Iterable[float | None]) -> float | None:
    vals = [v for v in values if v is not None]
    return round(mean(vals), 4) if vals else None


def summarise(rows: list[dict], *, pass_threshold: float) -> dict:
    answerable = [r for r in rows if r["type"] != "unanswerable"]
    unanswerable = [r for r in rows if r["type"] == "unanswerable"]
    generated = [r for r in rows if "refused" in r]
    judged = [r for r in answerable if r.get("answer_correctness") is not None]

    summary: dict = {
        "questions": len(rows),
        "answerable": len(answerable),
        "hit_rate": _mean(float(r["hit"]) for r in answerable),
        "all_sources_rate": _mean(float(r["all_sources"]) for r in answerable),
        "mrr": _mean(r["reciprocal_rank"] for r in answerable),
        "retrieval_ms_p50": percentile([r["retrieval_ms"] for r in rows], 50),
        "retrieval_ms_p95": percentile([r["retrieval_ms"] for r in rows], 95),
    }
    if not generated:
        return summary

    summary |= {
        "refusal_accuracy": _mean(float(r["refused"]) for r in unanswerable if "refused" in r),
        "false_refusal_rate": _mean(float(r["refused"]) for r in answerable if "refused" in r),
        "uncited_rate": _mean(float(r["uncited"]) for r in answerable if "refused" in r),
        "total_ms_p50": percentile([r["total_ms"] for r in generated], 50),
        "total_ms_p95": percentile([r["total_ms"] for r in generated], 95),
        "cost_per_query_usd": _mean(r["cost_usd"] for r in generated)
        if all(r["cost_usd"] is not None for r in generated)
        else None,
        "faithfulness": _mean(r.get("faithfulness") for r in answerable),
        "answer_correctness": _mean(r.get("answer_correctness") for r in answerable),
    }
    if judged and len(judged) == len(answerable):
        passed = sum(1 for r in unanswerable if r.get("refused")) + sum(
            1 for r in answerable if not r["refused"] and r["answer_correctness"] >= pass_threshold
        )
        summary["pass_rate"] = round(passed / len(rows), 4)
        summary["pass_threshold"] = pass_threshold
    return summary
