"""Check the golden set against the corpus you actually cloned.

The handbook changes every day, and the golden set was written from the live
site on one particular day. Before trusting any score, run:

    python -m scripts.validate_golden_set

For every answerable question it checks that
  1. each source URL exists in the cloned corpus,
  2. the key facts (`must_include`) still appear on those pages,
  3. the page's access group matches the one recorded in the golden set.

Fix or replace any question that fails. A stale reference answer makes the
assistant look wrong when it is right.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from eka.access import get_policy
from eka.corpus import load_documents, normalise_url
from eka.settings import BACKEND_DIR, get_settings

GOLDEN = BACKEND_DIR / "evals" / "golden_set.jsonl"


def load_golden(path: Path | None = None) -> list[dict]:
    path = path or Path(os.environ.get("EKA_GOLDEN_SET", GOLDEN))
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _plain(text: str) -> str:
    """Lowercase, with markdown links reduced to their text and emphasis marks removed."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    return re.sub(r"[\s*_`]+", " ", text.lower())


def _candidates(content_dir: Path, url: str, limit: int = 4) -> list[str]:
    """Files anywhere in the clone whose path ends like the missing URL: the page may have moved."""
    slug = normalise_url(url).rsplit("/", 1)[-1]
    hits = [
        p.relative_to(content_dir).as_posix()
        for p in content_dir.rglob("*.md")
        if p.stem == slug or (p.stem in {"_index", "index"} and p.parent.name == slug)
    ]
    return sorted(hits)[:limit]


def _closest_line(fact: str, text: str) -> str:
    """The line on the page sharing the most words with the missing fact, to show what changed."""
    words = set(re.findall(r"[a-z0-9$%]+", fact.lower()))
    best, score = "", 0
    for line in text.splitlines():
        overlap = len(words & set(re.findall(r"[a-z0-9$%]+", line.lower())))
        if overlap > score:
            best, score = line.strip(), overlap
    return best[:220]


def main() -> int:
    settings, policy = get_settings(), get_policy()
    all_docs = load_documents(settings.content_dir, policy)
    docs = {normalise_url(d.metadata["url"]): d for d in all_docs}
    items = load_golden()
    problems: list[str] = []

    print("Pages per configured section:")
    for inc in policy.include:
        n = sum(1 for d in all_docs if d.metadata["path"].startswith(inc))
        print(f"  {n:5d}  {inc}" + ("   <-- nothing found, check the path" if n == 0 else ""))
        if n == 0:
            problems.append(f"corpus.yaml: no pages under {inc}")
    print()

    for item in items:
        if item["type"] == "unanswerable":
            continue
        found = [docs.get(normalise_url(u)) for u in item["source_urls"]]
        for url, doc in zip(item["source_urls"], found):
            if doc is None:
                moved = _candidates(settings.content_dir, url)
                hint = f" (similar files: {', '.join(moved)})" if moved else ""
                problems.append(f"{item['id']}: source not in corpus: {url}{hint}")
        pages = [d for d in found if d is not None]
        if not pages:
            continue
        text = _plain(" ".join(d.text for d in pages))
        for fact in item.get("must_include", []):
            if _plain(fact) not in text:
                closest = _closest_line(fact, "\n".join(d.text for d in pages))
                problems.append(f"{item['id']}: fact no longer on the page: {fact!r}\n      closest line: {closest}")
        groups = {d.metadata["access_group"] for d in pages}
        if item["access_group"] not in groups:
            problems.append(
                f"{item['id']}: golden set says group {item['access_group']!r}, corpus says {sorted(groups)}"
            )

    answerable = sum(1 for i in items if i["type"] != "unanswerable")
    print(f"{len(items)} questions ({answerable} answerable), {len(docs)} pages in corpus")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        return 1
    print("Golden set matches the corpus.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
