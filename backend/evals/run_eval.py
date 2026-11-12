"""Score one configuration against the golden set.

    python -m evals.run_eval --retrieval-only      # free apart from query embeddings: hit rate, MRR, latency
    python -m evals.run_eval                       # adds answers, refusals, cost and Ragas scores
    python -m evals.run_eval --no-judge --limit 10 # quick look at real answers

Quality is measured as the `admin` role so access rules do not hide the right
page. Access control is measured separately: every restricted question is
retried as `employee` and must come back without its source page.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from llama_index.core.schema import MetadataMode

from eka.access import get_policy
from eka.assistant import Assistant
from eka.corpus import normalise_url
from eka.index import IndexSpec, row_count
from eka.providers import build_judge_llm
from eka.retrieval import RetrievalConfig
from eka.settings import BACKEND_DIR, Settings, get_settings
from evals.metrics import retrieval_scores, summarise
from scripts.validate_golden_set import load_golden

RESULTS_DIR = BACKEND_DIR / "evals" / "results"
# EVAL_RPM=10 spaces answer-model calls six seconds apart, for keys with a low requests-per-minute limit.
PACE_SECONDS = 60 / float(os.environ["EVAL_RPM"]) if os.environ.get("EVAL_RPM") else 0.0
QUALITY_ROLE = "admin"
LEAST_PRIVILEGED_ROLE = "employee"


_RETRY_AFTER = re.compile(r"retry in ([0-9.]+)s", re.I)


def _answer_with_retry(assistant: Assistant, question: str, retrieved, log: Callable[[str], None], tries: int = 8):
    """Ride out rate limits (429) and overload (503). A free-tier key hits 429 within a minute."""
    for attempt in range(1, tries + 1):
        try:
            return assistant.answer(question, retrieved)
        except Exception as exc:  # provider SDKs raise their own types; match on the message
            msg = str(exc)
            if "PerDay" in msg or "per day" in msg.lower():
                raise  # a daily quota will not reset by waiting a minute
            transient = any(k in msg for k in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE"))
            if not transient or attempt == tries:
                raise
            m = _RETRY_AFTER.search(msg)
            wait = max(float(m.group(1)) + 2 if m else 0, 10 * attempt)
            log(f"    rate limited or overloaded; waiting {wait:.0f}s (attempt {attempt}/{tries})")
            time.sleep(min(wait, 120))
    raise RuntimeError("unreachable")


def evaluate(
    assistant: Assistant,
    items: list[dict],
    cfg: RetrievalConfig,
    *,
    generate: bool = True,
    judge: bool = True,
    pass_threshold: float = 0.6,
    log: Callable[[str], None] = print,
) -> dict:
    rows: list[dict] = []
    to_judge: list[tuple[int, dict]] = []

    for i, item in enumerate(items, start=1):
        retrieved = assistant.retrieve(item["question"], QUALITY_ROLE, cfg)
        urls = [normalise_url(n.node.metadata["url"]) for n in retrieved.nodes]
        expected = [normalise_url(u) for u in item["source_urls"]]
        row = {
            "id": item["id"],
            "type": item["type"],
            "access_group": item["access_group"],
            "question": item["question"],
            "retrieved_urls": urls,
            "retrieval_ms": round(sum(retrieved.timings_ms.values()), 1),
            **retrieval_scores(urls, expected),
        }

        if generate:
            if PACE_SECONDS:
                time.sleep(PACE_SECONDS)
            result = _answer_with_retry(assistant, item["question"], retrieved, log)
            row |= {
                "answer": result.answer.text,
                "refused": result.answer.refused,
                "uncited": result.answer.uncited,
                "cited": result.answer.cited,
                "total_ms": result.timings_ms["total"],
                "cost_usd": result.cost["total"],
                "prompt_tokens": result.usage.prompt_tokens,
                "completion_tokens": result.usage.completion_tokens,
                "token_source": result.usage.token_source,
            }
            if item["type"] != "unanswerable":
                if result.answer.refused:
                    if judge:  # a wrong refusal scores zero without spending a judge call
                        row |= {"faithfulness": None, "answer_correctness": 0.0}
                elif judge:
                    to_judge.append(
                        (
                            len(rows),
                            {
                                "question": item["question"],
                                "answer": result.answer.text,
                                "reference": item["reference_answer"],
                                "contexts": [
                                    n.node.get_content(metadata_mode=MetadataMode.NONE)
                                    for n in retrieved.nodes
                                ],
                            },
                        )
                    )
        rows.append(row)
        log(f"  [{i}/{len(items)}] {item['id']} hit={row['hit']}" + (f" refused={row['refused']}" if generate else ""))

    if to_judge:
        from evals.judges import judge_answers

        log(f"Judging {len(to_judge)} answers with Ragas...")
        scores = judge_answers(
            [s for _, s in to_judge], build_judge_llm(assistant.settings), assistant.embed_model
        )
        for (index, _), score in zip(to_judge, scores):
            rows[index] |= score

    summary = summarise(rows, pass_threshold=pass_threshold)
    summary["access_control"] = access_check(assistant, items, cfg)
    return {"summary": summary, "rows": rows}


def access_check(assistant: Assistant, items: list[dict], cfg: RetrievalConfig) -> dict:
    """Ask every restricted question as the least-privileged role. Anything other than 0 leaks is a bug."""
    allowed = set(assistant.policy.groups_for_role(LEAST_PRIVILEGED_ROLE))
    restricted = [i for i in items if i["type"] != "unanswerable" and i["access_group"] not in allowed]
    leaks: list[str] = []
    for item in restricted:
        try:
            retrieved = assistant.retrieve(item["question"], LEAST_PRIVILEGED_ROLE, cfg)
        except PermissionError:
            leaks.append(item["id"])
            continue
        urls = {normalise_url(n.node.metadata["url"]) for n in retrieved.nodes}
        groups = {n.node.metadata["access_group"] for n in retrieved.nodes}
        if urls & {normalise_url(u) for u in item["source_urls"]} or not groups <= allowed:
            leaks.append(item["id"])
    return {"role": LEAST_PRIVILEGED_ROLE, "restricted_questions": len(restricted), "leaks": leaks}


def run_meta(
    settings: Settings, spec: IndexSpec, cfg: RetrievalConfig, n: int, *, generate: bool = True, judge: bool = True
) -> dict:
    snapshot = settings.content_dir.parent / "SNAPSHOT.txt"
    used = {settings.embed_provider} | ({settings.llm_provider} if generate else set())
    mock = "mock" in used
    return {
        "label": "MOCK RUN - plumbing check only, not a result" if mock else "real run",
        "scope": "retrieval + answers" + (" + judge" if judge else "") if generate else "retrieval only",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "golden_questions": n,
        "index": spec.__dict__,
        "retrieval": cfg.__dict__,
        "llm": f"{settings.llm_provider}/{settings.llm_model}" if generate else "not used",
        "embedding": f"{settings.embed_provider}/{settings.embed_model}",
        "reranker": f"{settings.rerank_provider}/{settings.rerank_model}" if cfg.rerank else "none",
        "judge": (
            f"{settings.judge_provider or settings.llm_provider}/{settings.judge_model or settings.llm_model}"
            if generate and judge
            else "not used"
        ),
        "corpus_snapshot": snapshot.read_text(encoding="utf-8").strip() if snapshot.exists() else "unknown",
    }


def save(run: dict, name: str) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{name}.json"
    path.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> int:
    s = get_settings()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", default="serving-config", help="file name for the result")
    p.add_argument("--retrieval-only", action="store_true", help="skip answer generation and judging")
    p.add_argument("--no-judge", action="store_true", help="generate answers but skip Ragas scoring")
    p.add_argument("--limit", type=int, help="only the first N questions")
    p.add_argument("--pass-threshold", type=float, default=0.6)
    args = p.parse_args()

    spec, cfg = IndexSpec.from_settings(s), RetrievalConfig.from_settings(s)
    if not row_count(s, spec):
        print(f"No index for this config ({spec.table}). Run: python -m scripts.ingest")
        return 1

    items = load_golden()[: args.limit]
    assistant = Assistant(s, policy=get_policy(), spec=spec, config=cfg)
    run = evaluate(
        assistant, items, cfg,
        generate=not args.retrieval_only,
        judge=not (args.retrieval_only or args.no_judge),
        pass_threshold=args.pass_threshold,
    )
    run = {
        "meta": run_meta(
            s, spec, cfg, len(items),
            generate=not args.retrieval_only, judge=not (args.retrieval_only or args.no_judge),
        ),
        **run,
    }
    path = save(run, args.name)
    print(json.dumps({"meta": run["meta"], "summary": run["summary"]}, indent=2))
    print(f"\nSaved {path.relative_to(BACKEND_DIR)}")
    return 1 if run["summary"]["access_control"]["leaks"] else 0


if __name__ == "__main__":
    sys.exit(main())
