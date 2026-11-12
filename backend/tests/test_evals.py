"""The eval harness is code too: these tests pin down what each metric means."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from evals.metrics import percentile, retrieval_scores, summarise

FIXTURES = Path(__file__).parent / "fixtures"


def test_retrieval_scores():
    got = ["u/a", "u/b", "u/c"]
    assert retrieval_scores(got, ["u/b"]) == {"hit": True, "all_sources": True, "reciprocal_rank": 0.5}
    assert retrieval_scores(got, ["u/b", "u/z"])["all_sources"] is False
    assert retrieval_scores(got, ["u/z"]) == {"hit": False, "all_sources": False, "reciprocal_rank": 0.0}


def test_percentile_is_nearest_rank():
    assert percentile([10, 20, 30, 40], 50) == 20
    assert percentile([10, 20, 30, 40], 95) == 40
    assert percentile([], 50) is None


def _row(type_, hit, refused=None, correctness=None, cost=0.001):
    row = {"type": type_, "hit": hit, "all_sources": hit, "reciprocal_rank": float(hit), "retrieval_ms": 10.0}
    if refused is not None:
        row |= {"refused": refused, "uncited": False, "total_ms": 100.0, "cost_usd": cost,
                "answer_correctness": correctness, "faithfulness": 1.0 if correctness else None}
    return row


def test_summary_retrieval_only_has_no_answer_metrics():
    s = summarise([_row("factual", True), _row("factual", False), _row("unanswerable", False)], pass_threshold=0.6)
    assert s["hit_rate"] == 0.5 and "pass_rate" not in s and "refusal_accuracy" not in s


def test_pass_rate_counts_correct_answers_and_correct_refusals():
    rows = [
        _row("factual", True, refused=False, correctness=0.9),   # pass
        _row("factual", True, refused=False, correctness=0.3),   # answered wrongly
        _row("factual", False, refused=True, correctness=0.0),   # refused something answerable
        _row("unanswerable", False, refused=True),               # pass
        _row("unanswerable", False, refused=False),              # made something up
    ]
    s = summarise(rows, pass_threshold=0.6)
    assert s["pass_rate"] == 0.4
    assert s["refusal_accuracy"] == 0.5
    assert s["false_refusal_rate"] == pytest.approx(1 / 3, abs=1e-3)


def test_cost_is_not_averaged_when_any_price_is_missing():
    rows = [_row("factual", True, False, 0.9), _row("factual", True, False, 0.9, cost=None)]
    assert summarise(rows, pass_threshold=0.6)["cost_per_query_usd"] is None


def test_shipped_golden_set_is_well_formed():
    from scripts.validate_golden_set import GOLDEN
    from eka.access import load_policy

    items = [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]
    policy = load_policy()
    assert len(items) == 50 and len({i["id"] for i in items}) == 50
    for item in items:
        assert item["type"] in {"factual", "multi_source", "unanswerable"}
        assert item["access_group"] in policy.all_groups
        if item["type"] == "unanswerable":
            assert not item["source_urls"] and not item["reference_answer"]
            continue
        assert item["reference_answer"] and item["must_include"]
        for url in item["source_urls"]:
            assert url.startswith(policy.site_url + "/handbook/") and url.endswith("/")
            # the access group recorded in the golden set must match what the policy assigns
            rel = url.removeprefix(policy.site_url + "/") + "_index.md"
            assert policy.group_for_path(rel) == item["access_group"], item["id"]


def test_evaluate_end_to_end_on_fixture_corpus(db, policy):
    from eka.assistant import Assistant
    from eka.index import IndexSpec, ingest
    from eka.providers import build_embed_model
    from eka.retrieval import RetrievalConfig
    from evals.run_eval import evaluate

    spec = IndexSpec(128, 16, "sentence", "mock")
    ingest(db, policy, spec, build_embed_model(db), recreate=True, log=lambda _: None)
    cfg = RetrievalConfig("hybrid", False, 3, 10)
    assistant = Assistant(db, policy=policy, spec=spec, config=cfg)
    items = [json.loads(line) for line in (FIXTURES / "golden_set.jsonl").read_text().splitlines()]

    run = evaluate(assistant, items, cfg, generate=True, judge=False, log=lambda _: None)
    summary = run["summary"]
    assert summary["hit_rate"] == 1.0
    # t03, t04 and t05 are outside the employee role: none of their pages may come back
    assert summary["access_control"] == {"role": "employee", "restricted_questions": 3, "leaks": []}
    assert all("answer" in row for row in run["rows"])


def test_later_experiments_inherit_the_best_chunk_size(tmp_path, monkeypatch):
    from evals import run_experiments as rx

    monkeypatch.setattr(rx, "RESULTS_DIR", tmp_path)
    plan = {"chunk_sweep": ["a", "b", "c"]}

    def result(size, hit, mrr, label="real run"):
        return {"meta": {"label": label, "index": {"chunk_size": size, "chunk_overlap": size // 8}},
                "summary": {"hit_rate": hit, "mrr": mrr}}

    (tmp_path / "a.json").write_text(json.dumps(result(256, 0.8, 0.6)))
    (tmp_path / "b.json").write_text(json.dumps(result(128, 0.8, 0.7)))
    assert rx.best_chunk(plan) is None  # sweep incomplete: do not guess

    (tmp_path / "c.json").write_text(json.dumps(result(384, 0.7, 0.9)))
    assert rx.best_chunk(plan) == {"chunk_size": 128, "chunk_overlap": 16}  # tie on hit rate, MRR decides

    (tmp_path / "c.json").write_text(json.dumps(result(384, 0.9, 0.9, label="MOCK RUN")))
    assert rx.best_chunk(plan) is None  # mock numbers never drive a decision


def test_fact_matching_sees_through_markdown_links_and_emphasis():
    from scripts.validate_golden_set import _plain

    page = "You may not use Paid [Caregiver Sick Time](/handbook/time-off/#caregiver), unless **approved**."
    assert _plain("Paid Caregiver Sick Time") in _plain(page)
    assert _plain("unless approved") in _plain(page)


def test_answer_retry_waits_out_rate_limits_and_gives_up_on_daily_quota(monkeypatch):
    from evals import run_eval

    sleeps = []
    monkeypatch.setattr(run_eval.time, "sleep", sleeps.append)

    class Flaky:
        calls = 0

        def answer(self, question, retrieved):
            self.calls += 1
            if self.calls < 3:
                raise RuntimeError("429 RESOURCE_EXHAUSTED ... Please retry in 11.6s.")
            return "ok"

    flaky = Flaky()
    assert run_eval._answer_with_retry(flaky, "q", None, log=lambda _: None) == "ok"
    assert flaky.calls == 3 and sleeps == [13.6, 20]

    class Daily:
        def answer(self, question, retrieved):
            raise RuntimeError("429 RESOURCE_EXHAUSTED quota metric GenerateRequestsPerDayPerProjectPerModel")

    with pytest.raises(RuntimeError, match="PerDay"):
        run_eval._answer_with_retry(Daily(), "q", None, log=lambda _: None)
