"""Load handbook markdown into LlamaIndex Documents with the metadata retrieval needs."""

from __future__ import annotations

import re
from pathlib import Path

import frontmatter
from llama_index.core import Document

from .access import AccessPolicy

MIN_CHARS = 200  # skip stubs and redirect pages

_SHORTCODE = re.compile(r"\{\{[<%].*?[%>]\}\}", flags=re.S)
_HTML_COMMENT = re.compile(r"<!--.*?-->", flags=re.S)
_HTML_TAG = re.compile(r"</?(?:div|span|br|details|summary|figure|iframe|script|style)[^>]*>", re.I)
_BLANK_RUNS = re.compile(r"\n{3,}")
_FIRST_H1 = re.compile(r"^#\s+(.+)$", flags=re.M)

# Kept out of the embedded text and out of the prompt: they are for filtering
# and citations, and would only add noise to similarity search.
_HIDDEN_KEYS = ["path", "url", "access_group", "section"]


def clean_markdown(text: str) -> str:
    text = _HTML_COMMENT.sub("", text)
    text = _SHORTCODE.sub("", text)
    text = _HTML_TAG.sub("", text)
    return _BLANK_RUNS.sub("\n\n", text).strip()


def path_to_url(rel_path: str, site_url: str) -> str:
    """handbook/finance/expenses/_index.md -> https://site/handbook/finance/expenses/"""
    p = rel_path.replace("\\", "/")
    p = re.sub(r"(^|/)_?index\.md$", "", p)
    p = re.sub(r"\.md$", "", p)
    return f"{site_url}/{p.strip('/')}/".lower()


def normalise_url(url: str) -> str:
    """Compare URLs without caring about case, trailing slash or anchors."""
    return url.split("#")[0].split("?")[0].rstrip("/").lower()


def load_documents(content_dir: Path, policy: AccessPolicy) -> list[Document]:
    if not content_dir.is_dir():
        raise FileNotFoundError(
            f"{content_dir} not found. Run scripts/fetch_handbook.sh or set HANDBOOK_CONTENT_DIR."
        )

    files: set[Path] = set()
    for inc in policy.include:
        base = content_dir / inc
        if base.is_dir():
            files.update(base.rglob("*.md"))
        elif base.with_suffix(".md").is_file():
            files.add(base.with_suffix(".md"))

    docs: list[Document] = []
    for file in sorted(files):
        rel = file.relative_to(content_dir).as_posix()
        try:
            post = frontmatter.loads(file.read_text(encoding="utf-8", errors="replace"))
        except Exception:  # malformed front matter: index the raw text instead of dropping the page
            post = frontmatter.Post(file.read_text(encoding="utf-8", errors="replace"))

        body = clean_markdown(post.content)
        if len(body) < MIN_CHARS:
            continue

        h1 = _FIRST_H1.search(body)
        title = str(post.get("title") or (h1.group(1) if h1 else file.stem)).strip()
        parts = rel.split("/")

        docs.append(
            Document(
                text=body,
                doc_id=rel,
                metadata={
                    "title": title,
                    "path": rel,
                    "url": path_to_url(rel, policy.site_url),
                    "section": parts[1] if len(parts) > 1 else parts[0],
                    "access_group": policy.group_for_path(rel),
                },
                excluded_embed_metadata_keys=_HIDDEN_KEYS,
                excluded_llm_metadata_keys=_HIDDEN_KEYS,
            )
        )
    return docs
