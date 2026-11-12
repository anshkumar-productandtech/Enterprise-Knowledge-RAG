"""Tests that need no database."""

from __future__ import annotations

import pytest
from llama_index.core.schema import NodeWithScore, TextNode

from eka.access import UnknownRole, load_policy
from eka.corpus import clean_markdown, load_documents, normalise_url, path_to_url
from eka.generation import NOT_FOUND, REFUSAL_MESSAGE, answer_once, stream_answer
from eka.providers import ExtractiveMockLLM
from eka.retrieval import reciprocal_rank_fusion
from eka.usage import Usage, cost_usd


# ---------------------------------------------------------------- access policy

def test_longest_prefix_wins(policy):
    assert policy.group_for_path("handbook/finance/expenses/_index.md") == "general"
    assert policy.group_for_path("handbook/finance/procurement.md") == "finance"


def test_prefix_does_not_match_sibling_directory(policy):
    # "handbook/finance" must not swallow "handbook/finance-archive"
    assert policy.group_for_path("handbook/finance-archive/x.md") == "restricted"


def test_unmapped_path_is_denied_by_default(policy):
    assert policy.group_for_path("handbook/misc/unmapped.md") == "restricted"
    assert "restricted" not in policy.groups_for_role("employee")


def test_unknown_role_is_rejected(policy):
    with pytest.raises(UnknownRole):
        policy.groups_for_role("ceo'; drop table users;--")


def test_unsafe_group_names_are_rejected(tmp_path):
    bad = tmp_path / "corpus.yaml"
    bad.write_text(
        "site_url: https://x.test\ninclude: [a]\n"
        "access_rules: [{prefix: a, group: \"x') or true --\"}]\n"
        "default_group: restricted\nroles: {r: {label: R, groups: [restricted]}}\n"
    )
    with pytest.raises(ValueError, match="Unsafe"):
        load_policy(bad)


def test_shipped_corpus_config_loads():
    policy = load_policy()
    assert policy.group_for_path("handbook/finance/expenses/_index.md") == "general"
    assert policy.group_for_path("handbook/finance/procurement/_index.md") == "finance"
    assert set(policy.groups_for_role("admin")) == policy.all_groups


# ----------------------------------------------------------------------- corpus

def test_url_mapping():
    site = "https://handbook.example.test"
    assert path_to_url("handbook/finance/expenses/_index.md", site) == f"{site}/handbook/finance/expenses/"
    assert path_to_url("handbook/finance/procurement.md", site) == f"{site}/handbook/finance/procurement/"
    assert normalise_url(f"{site}/Handbook/Finance/#top") == f"{site}/handbook/finance"


def test_cleaning_strips_shortcodes_and_comments():
    cleaned = clean_markdown("A {{< alert >}}B{{< /alert >}} <!-- hidden --> C")
    assert "alert" not in cleaned and "hidden" not in cleaned and "B" in cleaned


def test_documents_carry_access_metadata(settings, policy):
    docs = {d.metadata["path"]: d for d in load_documents(settings.content_dir, policy)}
    assert len(docs) == 5
    page = docs["handbook/people/time-off/_index.md"]
    assert page.metadata["title"] == "Time Off"
    assert page.metadata["access_group"] == "general"
    assert "internal note" not in page.text
    assert docs["handbook/misc/unmapped.md"].metadata["access_group"] == "restricted"


# ----------------------------------------------------------------------- fusion

def _hit(node_id: str, score: float = 0.0) -> NodeWithScore:
    return NodeWithScore(node=TextNode(id_=node_id, text=node_id), score=score)


def test_rrf_rewards_agreement_between_lists():
    fused = reciprocal_rank_fusion([[_hit("a"), _hit("b"), _hit("c")], [_hit("b"), _hit("d")]])
    assert [n.node.node_id for n in fused][0] == "b"
    assert {n.node.node_id for n in fused} == {"a", "b", "c", "d"}


# ------------------------------------------------------------------- generation

def _source(text: str) -> NodeWithScore:
    return NodeWithScore(node=TextNode(text=text, metadata={"title": "T", "url": "u"}), score=1.0)


class _FixedLLM(ExtractiveMockLLM):
    reply: str = ""

    def _answer(self, prompt: str) -> str:
        return self.reply


def test_no_sources_means_refusal_without_calling_the_model():
    answer = answer_once(_FixedLLM(reply="should not be used"), "q?", [])
    assert answer.refused and answer.text == REFUSAL_MESSAGE and answer.prompt_tokens == 0


def test_not_found_sentinel_never_reaches_the_user():
    events = list(stream_answer(_FixedLLM(reply=f"{NOT_FOUND} nothing here"), "q?", [_source("x")]))
    shown = "".join(p for k, p in events if k == "delta")
    final = events[-1][1]
    assert NOT_FOUND not in shown and shown == REFUSAL_MESSAGE
    assert final.refused and final.cited == []


def test_streamed_text_matches_final_answer_and_citations_are_validated():
    llm = _FixedLLM(reply="Vacation is 22 days [1]. Something else [7].")
    events = list(stream_answer(llm, "q?", [_source("Vacation is 22 days.")]))
    shown = "".join(p for k, p in events if k == "delta")
    final = events[-1][1]
    assert shown.strip() == final.text
    assert final.cited == [1]  # [7] points at a source that does not exist
    assert not final.refused and not final.uncited


def test_answer_without_citation_is_flagged():
    answer = answer_once(_FixedLLM(reply="Vacation is 22 days."), "q?", [_source("x")])
    assert answer.uncited and not answer.refused


def test_short_answer_is_still_streamed():
    events = list(stream_answer(_FixedLLM(reply="Yes [1]"), "q?", [_source("x")]))
    assert "".join(p for k, p in events if k == "delta").strip() == "Yes [1]"


# ------------------------------------------------------------------------- cost

def test_cost_is_none_when_a_price_is_missing():
    usage = Usage(prompt_tokens=1000, completion_tokens=100, embed_tokens=10)
    cost = cost_usd(usage, llm_model="no-such-model", embed_model="mock", rerank_model=None)
    assert cost["llm"] is None and cost["total"] is None


def test_cost_adds_up_for_priced_models():
    usage = Usage(prompt_tokens=1_000_000, completion_tokens=1_000_000, embed_tokens=0)
    cost = cost_usd(usage, llm_model="mock", embed_model="mock", rerank_model=None)
    assert cost["total"] == 0


# ------------------------------------------------------- local open-source models

class _FakeEncoder:
    """Stands in for the fastembed models so these tests need no download."""

    def embed(self, texts, batch_size=32):
        return [[float(len(t)), 1.0] for t in texts]

    def query_embed(self, query):
        return iter([[float(len(query)), 2.0]])

    def rerank(self, query, documents):
        return [float(doc.count("vacation")) for doc in documents]


def test_local_embedding_wrapper_returns_plain_floats():
    from eka.providers import FastEmbedEmbedding

    model = FastEmbedEmbedding(model_name="fake")
    model._encoder = _FakeEncoder()
    assert model.get_text_embedding_batch(["ab", "abcd"]) == [[2.0, 1.0], [4.0, 1.0]]
    assert model.get_query_embedding("abc") == [3.0, 2.0]


def test_local_reranker_reorders_and_truncates():
    from llama_index.core import QueryBundle

    from eka.providers import FastEmbedRerank

    reranker = FastEmbedRerank(model="fake", top_n=2)
    reranker._encoder = _FakeEncoder()
    nodes = [_source("expenses"), _source("vacation vacation"), _source("vacation"), _source("incidents")]
    out = reranker.postprocess_nodes(nodes, QueryBundle("vacation days"))
    assert [n.node.get_content() for n in out] == ["vacation vacation", "vacation"]
    assert out[0].score == 2.0


# ------------------------------------------------------------------------ index

def test_vector_store_urls_keep_the_password(monkeypatch):
    """str(sqlalchemy URL) masks the password as ***; the store must get the real one."""
    from eka.index import _store_urls
    from eka.settings import Settings

    monkeypatch.setenv("DATABASE_URL", "postgres://user:s3cret@db.example.test:5432/app")
    sync_url, async_url = _store_urls(Settings(_env_file=None))
    assert sync_url == "postgresql+psycopg2://user:s3cret@db.example.test:5432/app"
    assert async_url == "postgresql+asyncpg://user:s3cret@db.example.test:5432/app"


def test_grouped_citations_count_as_citations():
    answer = answer_once(_FixedLLM(reply="Give 6 days of notice [1, 2, 3]. Also [2,4]."), "q?",
                         [_source("a"), _source("b"), _source("c")])
    assert answer.cited == [1, 2, 3] and not answer.uncited  # 4 is out of range and dropped
