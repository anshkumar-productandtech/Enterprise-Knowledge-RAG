"""One place that knows about vendors.

Everything else in the codebase asks for "an LLM", "an embedding model" or
"a reranker" and gets a LlamaIndex object back, so switching provider is an
.env change, not a code change.

The `mock` providers need no API key and no network. They exist so the whole
pipeline (ingest -> retrieve -> answer -> eval) can be smoke-tested for free.
Never report mock numbers as results.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import (
    CompletionResponse,
    CompletionResponseGen,
    CustomLLM,
    LLMMetadata,
)
from llama_index.core.llms.callbacks import llm_completion_callback
from llama_index.core.llms.llm import LLM
from llama_index.core.bridge.pydantic import PrivateAttr
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import MetadataMode, NodeWithScore, QueryBundle

from .settings import Settings

# ---------------------------------------------------------------- mock models

_WORD = re.compile(r"[a-z0-9]+")


class HashEmbedding(BaseEmbedding):
    """Deterministic bag-of-words embedding. Good enough to test plumbing, nothing more."""

    dim: int = 256

    @classmethod
    def class_name(cls) -> str:
        return "HashEmbedding"

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for word in _WORD.findall(text.lower()):
            h = int.from_bytes(hashlib.md5(word.encode()).digest()[:4], "little")
            vec[h % self.dim] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._embed(query)

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._embed(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._embed(text)


class ExtractiveMockLLM(CustomLLM):
    """Answers with the first sentence of source [1]. Stands in for a real model in tests."""

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(model_name="mock", context_window=32_000, num_output=256)

    def _answer(self, prompt: str) -> str:
        sources = prompt.split("Sources:", 1)[-1]  # skip the "[1]" mentioned in the system prompt
        m = re.search(r"\[1\][^\n]*\n(.+?)(?:\n\[2\]|\nQuestion:|\Z)", sources, flags=re.S)
        if not m:
            return "NOT_FOUND"
        body = " ".join(
            line for line in m.group(1).splitlines() if line.strip() and not line.startswith("#")
        )
        first = re.split(r"(?<=[.!?])\s", body.strip(), maxsplit=1)[0]
        return f"{first[:300]} [1]"

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        return CompletionResponse(text=self._answer(prompt))

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        text, acc = self._answer(prompt), ""
        for word in re.findall(r"\S+\s*", text):
            acc += word
            yield CompletionResponse(text=acc, delta=word)


# ---------------------------------------------- open-source models, run locally
#
# fastembed runs small ONNX models on CPU: no API key, no per-token cost, and
# light enough for a small container. The model files download from Hugging
# Face on first use.


class FastEmbedEmbedding(BaseEmbedding):
    """Open-source embedding model (default BAAI/bge-small-en-v1.5, 384 dimensions, 512-token limit)."""

    _encoder: Any = PrivateAttr(default=None)

    @classmethod
    def class_name(cls) -> str:
        return "FastEmbedEmbedding"

    def _enc(self) -> Any:
        if self._encoder is None:
            from fastembed import TextEmbedding

            self._encoder = TextEmbedding(self.model_name)
        return self._encoder

    def _get_query_embedding(self, query: str) -> list[float]:
        return [float(x) for x in next(iter(self._enc().query_embed(query)))]

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        return self._get_text_embeddings([text])[0]

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[float(x) for x in vec] for vec in self._enc().embed(texts, batch_size=32)]


class FastEmbedRerank(BaseNodePostprocessor):
    """Open-source cross-encoder reranker: scores each (question, passage) pair together."""

    model: str
    top_n: int = 5
    _encoder: Any = PrivateAttr(default=None)

    @classmethod
    def class_name(cls) -> str:
        return "FastEmbedRerank"

    def _enc(self) -> Any:
        if self._encoder is None:
            from fastembed.rerank.cross_encoder import TextCrossEncoder

            self._encoder = TextCrossEncoder(self.model)
        return self._encoder

    def _postprocess_nodes(
        self, nodes: list[NodeWithScore], query_bundle: QueryBundle | None = None
    ) -> list[NodeWithScore]:
        if not nodes or query_bundle is None:
            return nodes[: self.top_n]
        texts = [n.node.get_content(metadata_mode=MetadataMode.EMBED) for n in nodes]
        scores = list(self._enc().rerank(query_bundle.query_str, texts))
        ranked = sorted(zip(nodes, scores), key=lambda pair: pair[1], reverse=True)[: self.top_n]
        return [NodeWithScore(node=n.node, score=float(score)) for n, score in ranked]


# ------------------------------------------------------------------ factories


def build_llm(
    settings: Settings, *, provider: str | None = None, model: str | None = None, max_tokens: int = 700
) -> LLM:
    provider = provider or settings.llm_provider
    model = model or settings.llm_model
    common = {"temperature": 0.0, "max_tokens": max_tokens}

    if provider == "mock":
        return ExtractiveMockLLM()
    if provider == "openai":
        from llama_index.llms.openai import OpenAI

        return OpenAI(model=model, api_key=settings.require_key("openai_api_key"), **common)
    if provider == "anthropic":
        from llama_index.llms.anthropic import Anthropic

        return Anthropic(model=model, api_key=settings.require_key("anthropic_api_key"), **common)
    if provider == "gemini":
        from llama_index.llms.google_genai import GoogleGenAI

        return GoogleGenAI(model=model, api_key=settings.require_key("google_api_key"), **common)
    raise ValueError(f"Unknown LLM provider: {provider}")


def build_judge_llm(settings: Settings) -> LLM:
    """Model that grades answers. Falls back to the answer model when not set."""
    return build_llm(
        settings,
        provider=settings.judge_provider or settings.llm_provider,
        model=settings.judge_model or settings.llm_model,
        # The judge lists every statement in an answer; 700 tokens cut some lists off mid-way.
        max_tokens=4096,
    )


def build_embed_model(settings: Settings) -> BaseEmbedding:
    provider, model = settings.embed_provider, settings.embed_model

    if provider == "mock":
        return HashEmbedding()
    if provider == "local":
        return FastEmbedEmbedding(model_name=model, embed_batch_size=32)
    if provider == "openai":
        from llama_index.embeddings.openai import OpenAIEmbedding

        return OpenAIEmbedding(model=model, api_key=settings.require_key("openai_api_key"))
    if provider == "voyage":
        from llama_index.embeddings.voyageai import VoyageEmbedding

        return VoyageEmbedding(
            model_name=model, voyage_api_key=settings.require_key("voyage_api_key")
        )
    if provider == "gemini":
        from llama_index.embeddings.google_genai import GoogleGenAIEmbedding

        return GoogleGenAIEmbedding(
            model_name=model, api_key=settings.require_key("google_api_key")
        )
    raise ValueError(f"Unknown embedding provider: {provider}")


def build_reranker(settings: Settings, top_n: int) -> BaseNodePostprocessor | None:
    provider, model = settings.rerank_provider, settings.rerank_model

    if provider == "none":
        return None
    if not model:
        raise RuntimeError("RERANK_MODEL is not set but RERANK_PROVIDER is.")
    if provider == "cohere":
        from llama_index.postprocessor.cohere_rerank import CohereRerank

        return CohereRerank(
            model=model, top_n=top_n, api_key=settings.require_key("cohere_api_key")
        )
    if provider == "local":
        return FastEmbedRerank(model=model, top_n=top_n)
    raise ValueError(f"Unknown rerank provider: {provider}")


def embedding_dim(embed_model: BaseEmbedding) -> int:
    """Ask the model rather than hardcode a table of dimensions that goes stale."""
    return len(embed_model.get_text_embedding("dimension probe"))
