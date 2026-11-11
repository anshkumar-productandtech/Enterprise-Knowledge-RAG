"""Retrieval: access filter -> vector and/or keyword search -> fusion -> optional rerank.

The access filter is part of both SQL queries. Nothing a role cannot read is
ever fetched, so nothing downstream (reranker, prompt, logs) can leak it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from llama_index.core import QueryBundle, VectorStoreIndex
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores.types import (
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
    VectorStoreQueryMode,
)

from .access import AccessPolicy
from .index import IndexSpec, open_store
from .providers import embedding_dim
from .settings import Settings
from .usage import count_tokens

RRF_K = 60  # standard constant for reciprocal rank fusion


@dataclass(frozen=True)
class RetrievalConfig:
    search_mode: str = "hybrid"  # "vector" | "hybrid"
    rerank: bool = False
    top_k: int = 5  # chunks handed to the model
    candidate_k: int = 20  # chunks fetched per search before fusion/rerank

    @classmethod
    def from_settings(cls, s: Settings) -> "RetrievalConfig":
        return cls(s.search_mode, s.rerank_provider != "none", s.top_k, s.candidate_k)


@dataclass
class Retrieved:
    nodes: list[NodeWithScore]
    timings_ms: dict[str, float] = field(default_factory=dict)
    embed_tokens: int = 0
    rerank_searches: int = 0


def reciprocal_rank_fusion(result_lists: list[list[NodeWithScore]]) -> list[NodeWithScore]:
    """Merge ranked lists by rank, not score, so cosine and ts_rank never need a common scale."""
    scores: dict[str, float] = {}
    by_id: dict[str, NodeWithScore] = {}
    for results in result_lists:
        for rank, item in enumerate(results):
            nid = item.node.node_id
            scores[nid] = scores.get(nid, 0.0) + 1.0 / (RRF_K + rank + 1)
            by_id.setdefault(nid, item)
    ranked = sorted(scores, key=scores.__getitem__, reverse=True)
    return [NodeWithScore(node=by_id[nid].node, score=scores[nid]) for nid in ranked]


class Retriever:
    def __init__(
        self,
        settings: Settings,
        policy: AccessPolicy,
        spec: IndexSpec,
        embed_model: BaseEmbedding,
        reranker: BaseNodePostprocessor | None = None,
    ) -> None:
        self.policy = policy
        self.embed_model = embed_model
        self.reranker = reranker
        store = open_store(settings, spec, embedding_dim(embed_model), create=False)
        self.index = VectorStoreIndex.from_vector_store(store, embed_model=embed_model)

    def retrieve(self, question: str, role: str, cfg: RetrievalConfig) -> Retrieved:
        # Raises UnknownRole for anything not in corpus.yaml. Group names come
        # from that file only, never from the request.
        groups = self.policy.groups_for_role(role)
        filters = MetadataFilters(
            filters=[MetadataFilter(key="access_group", operator=FilterOperator.IN, value=groups)]
        )
        out = Retrieved(nodes=[], embed_tokens=count_tokens(question))

        t0 = time.perf_counter()
        bundle = QueryBundle(
            query_str=question, embedding=self.embed_model.get_query_embedding(question)
        )
        out.timings_ms["embed"] = _ms(t0)

        t0 = time.perf_counter()
        vector_hits = self.index.as_retriever(
            similarity_top_k=cfg.candidate_k, filters=filters
        ).retrieve(bundle)
        if cfg.search_mode == "hybrid":
            keyword_hits = self.index.as_retriever(
                vector_store_query_mode=VectorStoreQueryMode.SPARSE,
                similarity_top_k=cfg.candidate_k,
                sparse_top_k=cfg.candidate_k,
                filters=filters,
            ).retrieve(bundle)
            candidates = reciprocal_rank_fusion([vector_hits, keyword_hits])
        else:
            candidates = vector_hits
        out.timings_ms["search"] = _ms(t0)

        if cfg.rerank and self.reranker is not None and candidates:
            t0 = time.perf_counter()
            self.reranker.top_n = cfg.top_k  # type: ignore[attr-defined]
            out.nodes = self.reranker.postprocess_nodes(candidates[: cfg.candidate_k], bundle)
            out.timings_ms["rerank"] = _ms(t0)
            out.rerank_searches = 1
        else:
            out.nodes = candidates[: cfg.top_k]

        # Defence in depth: the SQL filter should make this impossible.
        allowed = set(groups)
        leaked = [n for n in out.nodes if n.node.metadata.get("access_group") not in allowed]
        if leaked:
            raise PermissionError("Access filter returned a chunk outside the caller's groups.")
        return out


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 1)
