"""End-to-end tests against a real Postgres + pgvector, with mock models."""

from __future__ import annotations

import json

import pytest

from eka.assistant import Assistant
from eka.index import IndexSpec, ingest, row_count
from eka.providers import build_embed_model
from eka.retrieval import RetrievalConfig

SPEC = IndexSpec(chunk_size=128, chunk_overlap=16, chunker="markdown", embed_model="mock")


@pytest.fixture(scope="module")
def assistant(db, policy):
    stats = ingest(db, policy, SPEC, build_embed_model(db), recreate=True, log=lambda _: None)
    assert stats["status"] == "ingested" and stats["chunks"] == row_count(db, SPEC)
    return Assistant(db, policy=policy, spec=SPEC, config=RetrievalConfig("hybrid", False, 3, 10))


def _groups(retrieved) -> set[str]:
    return {n.node.metadata["access_group"] for n in retrieved.nodes}


def test_ingest_is_idempotent(db, policy, assistant):
    again = ingest(db, policy, SPEC, build_embed_model(db), log=lambda _: None)
    assert again["status"] == "exists"


@pytest.mark.parametrize("mode", ["vector", "hybrid"])
def test_relevant_page_is_retrieved(assistant, mode):
    cfg = RetrievalConfig(mode, False, 3, 10)
    hits = assistant.retrieve("How many days of paid vacation do employees get?", "employee", cfg)
    assert hits.nodes and hits.nodes[0].node.metadata["title"] == "Time Off"


def test_keyword_search_finds_exact_terms(assistant):
    hits = assistant.retrieve("Ledgerly", "employee", RetrievalConfig("hybrid", False, 3, 10))
    assert any("Ledgerly" in n.node.get_content() for n in hits.nodes)


@pytest.mark.parametrize("mode", ["vector", "hybrid"])
def test_employee_never_sees_restricted_groups(assistant, mode):
    cfg = RetrievalConfig(mode, False, 10, 20)
    for question in [
        "What is the negotiated day rate with the logistics supplier?",
        "What is the secret launch codename?",
        "How fast must the on-call engineer acknowledge a severity one page?",
    ]:
        hits = assistant.retrieve(question, "employee", cfg)
        assert _groups(hits) <= {"general"}, question
        text = " ".join(n.node.get_content() for n in hits.nodes)
        assert "1375" not in text and "Bluefinch" not in text


def test_roles_unlock_their_own_groups_only(assistant):
    cfg = RetrievalConfig("hybrid", False, 10, 20)
    q = "What is the negotiated day rate with the logistics supplier?"
    assert "finance" in _groups(assistant.retrieve(q, "finance_analyst", cfg))
    assert "finance" not in _groups(assistant.retrieve(q, "engineer", cfg))
    assert "restricted" in _groups(assistant.retrieve("secret launch codename", "admin", cfg))


def test_ask_returns_cited_answer_with_usage(assistant):
    result = assistant.ask("How many paid sick days do employees get per year?", "employee")
    assert not result.answer.refused and result.answer.cited == [1]
    assert result.sources[0].url.startswith("https://handbook.example.test/handbook/")
    assert result.usage.prompt_tokens > 0 and result.cost["total"] == 0
    assert {"embed", "search", "generate", "total"} <= set(result.timings_ms)


def test_api_stream_and_limits(db, policy, assistant, monkeypatch):
    from fastapi.testclient import TestClient

    from eka import api

    monkeypatch.setattr(api, "Assistant", lambda settings: assistant)
    with TestClient(api.app) as client:
        assert client.get("/health").json() == {"ok": True}
        assert client.post("/chat", json={"question": "hello there", "role": "root"}).status_code == 400
        assert client.post("/chat", json={"question": "x" * 600, "role": "employee"}).status_code == 413

        body = client.post(
            "/chat", json={"question": "How many vacation days do I get?", "role": "employee"}
        ).text
        events = [line.split(": ", 1)[1] for line in body.splitlines() if line.startswith("event: ")]
        assert events[0] == "sources" and events[-1] == "done" and "delta" in events
        done = json.loads(body.strip().splitlines()[-1].removeprefix("data: "))
        assert done["refused"] is False and "question" not in json.dumps(done)

        # RATE_LIMIT_PER_MINUTE=3 in conftest: one call used above, two left.
        codes = [
            client.post("/chat", json={"question": "vacation days?", "role": "employee"}).status_code
            for _ in range(3)
        ]
        assert codes == [200, 200, 429]
