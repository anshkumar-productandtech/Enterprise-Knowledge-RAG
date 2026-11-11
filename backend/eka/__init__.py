"""Enterprise Knowledge Assistant: RAG over a company handbook with citations and access control."""

from __future__ import annotations

import os
from importlib.util import find_spec
from pathlib import Path


def _use_private_nltk_dir() -> None:
    """LlamaIndex's sentence splitter needs NLTK data, which it ships inside site-packages.

    Recent NLTK refuses to load data from a directory other accounts can write
    to (common on CI runners and shared images). In that case point NLTK at a
    private per-user directory; LlamaIndex downloads what it needs there once.
    """
    if os.environ.get("NLTK_DATA"):
        return
    try:
        spec = find_spec("llama_index.core")
        bundled = Path(spec.origin).parent / "_static" / "nltk_cache"  # type: ignore[union-attr,arg-type]
        if bundled.is_dir() and not bundled.stat().st_mode & 0o022:
            return
    except Exception:
        pass
    private = Path.home() / ".cache" / "eka" / "nltk_data"
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.environ["NLTK_DATA"] = str(private)


_use_private_nltk_dir()
