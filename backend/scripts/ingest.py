"""Chunk, embed and store the corpus.

    python -m scripts.ingest --dry-run          # count chunks and estimate cost, send nothing
    python -m scripts.ingest                    # build the table for the serving config in .env
    python -m scripts.ingest --chunk-size 256   # build a table for an experiment
"""

from __future__ import annotations

import argparse
import json
import sys

from eka.access import get_policy
from eka.index import IndexSpec, ingest
from eka.providers import build_embed_model
from eka.settings import get_settings


def main() -> int:
    s = get_settings()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--chunk-size", type=int, default=s.chunk_size)
    p.add_argument("--chunk-overlap", type=int, default=s.chunk_overlap)
    p.add_argument("--chunker", choices=["sentence", "markdown"], default=s.chunker)
    p.add_argument("--recreate", action="store_true", help="rebuild the table if it exists")
    p.add_argument("--dry-run", action="store_true", help="estimate only, no API or DB writes")
    p.add_argument("--yes", action="store_true", help="skip the cost confirmation")
    args = p.parse_args()

    policy = get_policy()
    spec = IndexSpec(args.chunk_size, args.chunk_overlap, args.chunker, s.embed_model)
    embed_model = build_embed_model(s)

    plan = ingest(s, policy, spec, embed_model, dry_run=True)
    print(json.dumps(plan, indent=2))
    if args.dry_run:
        return 0

    if s.embed_provider != "mock" and not args.yes:
        cost = plan["embed_cost_usd_est"]
        shown = "unknown (no price in config/pricing.yaml)" if cost is None else f"about ${cost}"
        reply = input(f"Embed {plan['chunks']} chunks with {s.embed_model}? Estimated cost: {shown}. [y/N] ")
        if reply.strip().lower() != "y":
            print("Cancelled.")
            return 1

    result = ingest(s, policy, spec, embed_model, recreate=args.recreate)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
