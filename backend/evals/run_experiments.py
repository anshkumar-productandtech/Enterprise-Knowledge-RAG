"""Run the experiments in config/experiments.yaml and write the comparison table.

    python -m evals.run_experiments --retrieval-only --ingest-missing
    python -m evals.run_experiments --only 0-baseline 3-hybrid-rerank

Each experiment saves evals/results/<name>.json. The table (experiments.md and
experiments.csv) is rebuilt from every saved result, so a cheap retrieval-only
pass and a later paid pass on a few rows add up to one table.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys

import yaml

from eka.access import get_policy
from eka.assistant import Assistant
from eka.index import IndexSpec, ingest, row_count
from eka.providers import build_embed_model
from eka.retrieval import RetrievalConfig
from eka.settings import BACKEND_DIR, get_settings
from evals.run_eval import RESULTS_DIR, evaluate, run_meta, save
from scripts.validate_golden_set import load_golden

CONFIG = BACKEND_DIR / "config" / "experiments.yaml"

COLUMNS = [
    ("experiment", "Experiment"), ("chunk", "Chunk"), ("search", "Search"), ("rerank", "Rerank"),
    ("hit_rate", "Hit@5"), ("mrr", "MRR"), ("faithfulness", "Faithful"),
    ("answer_correctness", "Correct"), ("pass_rate", "Pass rate"),
    ("refusal_accuracy", "Refusal acc"), ("retrieval_ms_p95", "Retrieval p95 ms"),
    ("total_ms_p95", "Answer p95 ms"), ("cost_per_query_usd", "$/query"), ("leaks", "ACL leaks"),
]
PERCENT = {"hit_rate", "faithfulness", "answer_correctness", "pass_rate", "refusal_accuracy"}


def fmt(key: str, value) -> str:
    if value is None:
        return "n/a"
    if key == "cost_per_query_usd":
        return f"{value:.5f}"
    if key in PERCENT:
        return f"{value:.0%}"
    if key == "mrr":
        return f"{value:.3f}"
    if key.endswith("_p95"):
        return f"{value:.0f}"
    return str(value)


def load_result(name: str) -> dict | None:
    path = RESULTS_DIR / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def best_chunk(plan: dict) -> dict | None:
    """Chunk size with the best hit rate (then MRR) among the sweep rows, once all of them have results."""
    runs = [load_result(name) for name in plan.get("chunk_sweep", [])]
    if not runs or any(r is None or "MOCK" in r["meta"]["label"] for r in runs):
        return None
    best = max(runs, key=lambda r: (r["summary"]["hit_rate"] or 0, r["summary"]["mrr"] or 0))
    index = best["meta"]["index"]
    return {"chunk_size": index["chunk_size"], "chunk_overlap": index["chunk_overlap"]}


def table_row(name: str, run: dict) -> dict:
    meta, summary = run["meta"], run["summary"]
    return {
        "experiment": name,
        "chunk": f"{meta['index']['chunk_size']} {meta['index']['chunker']}",
        "search": meta["retrieval"]["search_mode"],
        "rerank": "yes" if meta["retrieval"]["rerank"] else "no",
        **{k: summary.get(k) for k, _ in COLUMNS if k in summary},
        "leaks": len(summary["access_control"]["leaks"]),
    }


def write_table(plan: dict) -> list[str]:
    """Rebuild the table from every saved result that belongs to the plan."""
    runs = [(e["name"], load_result(e["name"])) for e in plan["experiments"]]
    runs = [(n, r) for n, r in runs if r is not None]
    if not runs:
        return []
    rows = [table_row(n, r) for n, r in runs]
    metas = [r["meta"] for _, r in runs]

    with (RESULTS_DIR / "experiments.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[k for k, _ in COLUMNS], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    def uniq(key: str) -> str:
        return ", ".join(sorted({m[key] for m in metas} - {"not used", "none"})) or "none"

    label = "MOCK RUN - plumbing check only, not a result" if any("MOCK" in m["label"] for m in metas) else "real run"
    chosen = best_chunk(plan)
    lines = [
        f"<!-- {label} | last updated {max(m['timestamp'] for m in metas)} -->",
        "| " + " | ".join(h for _, h in COLUMNS) + " |",
        "| " + " | ".join("---" for _ in COLUMNS) + " |",
        *["| " + " | ".join(fmt(k, row.get(k)) for k, _ in COLUMNS) + " |" for row in rows],
        "",
        f"Measured on {metas[0]['golden_questions']} golden questions; {plan['defaults']['top_k']} chunks go to the model. "
        f"Embeddings: {uniq('embedding')}. Reranker: {uniq('reranker')}. "
        f"Answer model: {uniq('llm')}. Judge: {uniq('judge')}. "
        "Rows showing n/a for answer metrics were run retrieval-only.",
        "",
        f"Corpus: {metas[-1]['corpus_snapshot'].replace(chr(10), ', ')}.",
    ]
    if chosen:
        lines += ["", f"Chunk size carried into the later rows: {chosen['chunk_size']} tokens (best hit rate in the chunk sweep)."]
    (RESULTS_DIR / "experiments.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return lines


def main() -> int:
    s = get_settings()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--retrieval-only", action="store_true")
    p.add_argument("--no-judge", action="store_true")
    p.add_argument("--ingest-missing", action="store_true", help="build missing index tables")
    p.add_argument("--only", nargs="*", help="experiment names to run")
    p.add_argument("--limit", type=int)
    p.add_argument("--pass-threshold", type=float, default=0.6)
    args = p.parse_args()

    plan = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    policy, items = get_policy(), load_golden()[: args.limit]
    sweep = set(plan.get("chunk_sweep", []))
    generate = not args.retrieval_only
    judge = not (args.retrieval_only or args.no_judge)
    ran = 0
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for exp in plan["experiments"]:
        name = exp["name"]
        if args.only and name not in args.only:
            continue
        overrides = {k: v for k, v in exp.items() if k not in {"name", "note"}}
        inherited = {} if name in sweep else (best_chunk(plan) or {})
        c = plan["defaults"] | inherited | overrides
        spec = IndexSpec(c["chunk_size"], c["chunk_overlap"], c["chunker"], s.embed_model)
        cfg = RetrievalConfig(c["search_mode"], c["rerank"], c["top_k"], c["candidate_k"])
        print(f"\n== {name}: {exp.get('note', '')}", flush=True)

        if cfg.rerank and s.rerank_provider == "none":
            print("   skipped: set RERANK_PROVIDER and RERANK_MODEL to run this one")
            continue
        if not row_count(s, spec):
            if not args.ingest_missing:
                print(
                    f"   skipped: no index. Run: python -m scripts.ingest --chunk-size {spec.chunk_size} "
                    f"--chunk-overlap {spec.chunk_overlap} --chunker {spec.chunker}   (or pass --ingest-missing)"
                )
                continue
            print("   building index...", flush=True)
            stats = ingest(s, policy, spec, build_embed_model(s), log=lambda m: None)
            print(f"   indexed {stats['chunks']} chunks from {stats['pages']} pages", flush=True)

        assistant = Assistant(s, policy=policy, spec=spec, config=cfg)
        run = evaluate(assistant, items, cfg, generate=generate, judge=judge, pass_threshold=args.pass_threshold)
        meta = run_meta(s, spec, cfg, len(items), generate=generate, judge=judge)
        # A --limit run is a spot check: keep it apart so it never replaces a full result in the table.
        save({"meta": meta, **run}, f"{name}--first{args.limit}" if args.limit else name)
        ran += 1
        print(f"   {json.dumps({k: v for k, v in run['summary'].items() if k != 'access_control'})}", flush=True)

    lines = write_table(plan)
    if not lines:
        print("\nNothing ran and no saved results.")
        return 1
    print("\n" + "\n".join(lines))
    return 0 if ran else 1


if __name__ == "__main__":
    sys.exit(main())
