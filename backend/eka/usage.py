"""Token counts and cost per query.

Prices live in config/pricing.yaml because they change and because a cost
metric is only as honest as the price behind it. A model with no price
configured yields cost = None, never 0.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from llama_index.core.utils import get_tokenizer

from .settings import BACKEND_DIR

PRICING_FILE = BACKEND_DIR / "config" / "pricing.yaml"


@dataclass(frozen=True)
class Pricing:
    llm: dict[str, dict[str, float | None]]
    embedding: dict[str, dict[str, float | None]]
    rerank: dict[str, dict[str, float | None]]

    def llm_price(self, model: str) -> tuple[float, float] | None:
        p = self.llm.get(model) or {}
        i, o = p.get("input_per_mtok"), p.get("output_per_mtok")
        return None if i is None or o is None else (float(i), float(o))

    def embedding_price(self, model: str) -> float | None:
        v = (self.embedding.get(model) or {}).get("per_mtok")
        return None if v is None else float(v)

    def rerank_price(self, model: str) -> float | None:
        v = (self.rerank.get(model) or {}).get("per_search")
        return None if v is None else float(v)


@lru_cache
def load_pricing(path: Path = PRICING_FILE) -> Pricing:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return Pricing(raw.get("llm") or {}, raw.get("embedding") or {}, raw.get("rerank") or {})


def count_tokens(text: str) -> int:
    """Tokenizer estimate (tiktoken). Expect roughly +/-15% for non-OpenAI models."""
    try:
        return len(get_tokenizer()(text))
    except Exception:
        return max(1, len(text) // 4)


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    embed_tokens: int = 0
    rerank_searches: int = 0
    token_source: str = "estimated"  # "provider" when the API reported real counts

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def provider_token_counts(response: Any) -> tuple[int, int] | None:
    """Pull real token counts out of a LlamaIndex response if the provider sent them."""
    candidates: list[Any] = [getattr(response, "additional_kwargs", None)]
    raw = getattr(response, "raw", None)
    usage = raw.get("usage") if isinstance(raw, dict) else getattr(raw, "usage", None)
    candidates.append(usage)
    candidates.append(getattr(raw, "usage_metadata", None))

    for c in candidates:
        if c is None:
            continue
        get = c.get if isinstance(c, dict) else lambda k, _c=c: getattr(_c, k, None)
        prompt = get("prompt_tokens") or get("input_tokens") or get("prompt_token_count")
        completion = (
            get("completion_tokens") or get("output_tokens") or get("candidates_token_count")
        )
        if isinstance(prompt, int) and isinstance(completion, int):
            return prompt, completion
    return None


def cost_usd(
    usage: Usage, *, llm_model: str, embed_model: str, rerank_model: str | None
) -> dict[str, float | None]:
    """Cost breakdown for one query. Any component without a configured price is None."""
    pricing = load_pricing()

    llm_p = pricing.llm_price(llm_model)
    llm = (
        None
        if llm_p is None
        else usage.prompt_tokens / 1e6 * llm_p[0] + usage.completion_tokens / 1e6 * llm_p[1]
    )

    emb_p = pricing.embedding_price(embed_model)
    emb = None if emb_p is None else usage.embed_tokens / 1e6 * emb_p

    if not usage.rerank_searches:
        rr: float | None = 0.0
    else:
        rr_p = pricing.rerank_price(rerank_model or "")
        rr = None if rr_p is None else usage.rerank_searches * rr_p

    parts = {"llm": llm, "embedding": emb, "rerank": rr}
    total = None if any(v is None for v in parts.values()) else sum(parts.values())  # type: ignore[arg-type]
    return {**parts, "total": total}
