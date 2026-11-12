"""The assistant as one object: retrieve, answer, account for time and money.

Both the API and the eval harness go through this class, so what gets measured
is what gets served.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterator

from llama_index.core.schema import NodeWithScore

from .access import AccessPolicy, get_policy
from .generation import Answer, Source, answer_once, stream_answer, to_sources
from .index import IndexSpec
from .providers import build_embed_model, build_llm, build_reranker
from .retrieval import Retrieved, RetrievalConfig, Retriever
from .settings import Settings
from .usage import Usage, cost_usd


@dataclass
class Result:
    answer: Answer
    sources: list[Source]
    nodes: list[NodeWithScore]
    usage: Usage
    cost: dict[str, float | None]
    timings_ms: dict[str, float]

    def summary(self) -> dict:
        """What the UI footer and the logs get. No question text, no source text."""
        return {
            "refused": self.answer.refused,
            "uncited": self.answer.uncited,
            "cited": self.answer.cited,
            "usage": self.usage.to_dict(),
            "cost_usd": self.cost,
            "timings_ms": self.timings_ms,
        }


class Assistant:
    def __init__(
        self,
        settings: Settings,
        *,
        policy: AccessPolicy | None = None,
        spec: IndexSpec | None = None,
        config: RetrievalConfig | None = None,
    ) -> None:
        self.settings = settings
        self.policy = policy or get_policy()
        self.spec = spec or IndexSpec.from_settings(settings)
        self.config = config or RetrievalConfig.from_settings(settings)
        self.llm = build_llm(settings)
        self.embed_model = build_embed_model(settings)
        self.reranker = build_reranker(settings, top_n=self.config.top_k)
        self.retriever = Retriever(settings, self.policy, self.spec, self.embed_model, self.reranker)

    def retrieve(self, question: str, role: str, config: RetrievalConfig | None = None) -> Retrieved:
        return self.retriever.retrieve(question, role, config or self.config)

    def _result(self, retrieved: Retrieved, answer: Answer) -> Result:
        usage = Usage(
            prompt_tokens=answer.prompt_tokens,
            completion_tokens=answer.completion_tokens,
            embed_tokens=retrieved.embed_tokens,
            rerank_searches=retrieved.rerank_searches,
            token_source=answer.token_source,
        )
        timings = {**retrieved.timings_ms, **answer.timings_ms}
        timings["total"] = round(
            sum(v for k, v in timings.items() if k in {"embed", "search", "rerank", "generate"}), 1
        )
        cost = cost_usd(
            usage,
            llm_model=self.settings.llm_model,
            embed_model=self.settings.embed_model,
            rerank_model=self.settings.rerank_model,
        )
        return Result(answer, to_sources(retrieved.nodes), retrieved.nodes, usage, cost, timings)

    def answer(self, question: str, retrieved: Retrieved) -> Result:
        """Answer from chunks that were already retrieved (the eval harness reuses them)."""
        return self._result(retrieved, answer_once(self.llm, question, retrieved.nodes))

    def ask(self, question: str, role: str, config: RetrievalConfig | None = None) -> Result:
        return self.answer(question, self.retrieve(question, role, config))

    def stream(self, question: str, role: str, *, tries: int = 3) -> Iterator[tuple[str, object]]:
        """Yield ("sources", [...]), then ("delta", str)..., then ("done", Result).

        A temporary model error (overload, rate limit) before the first word is
        retried, so the reader never sees it. Once text has been shown, an error
        is passed on rather than restarting the answer mid-sentence.
        """
        retrieved = self.retrieve(question, role)
        yield "sources", [s.to_dict() for s in to_sources(retrieved.nodes)]
        for attempt in range(1, tries + 1):
            started = False
            try:
                for kind, payload in stream_answer(self.llm, question, retrieved.nodes):
                    if kind == "delta":
                        started = True
                        yield "delta", payload
                    else:
                        yield "done", self._result(retrieved, payload)  # type: ignore[arg-type]
                return
            except Exception as exc:
                if started or attempt == tries or not is_transient(exc):
                    raise
                time.sleep(2 * attempt)


def is_transient(exc: Exception) -> bool:
    msg = str(exc)
    return any(k in msg for k in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "overloaded"))
