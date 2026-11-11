"""Chunking, embedding and the pgvector store.

Each (chunk size, overlap, chunker, embedding model) combination gets its own
table, so experiments can be compared side by side without re-ingesting, and the
serving config just points at the winning table.

Tables live in a dedicated Postgres schema (`eka`), not `public`. On Supabase,
`public` is exposed through the auto-generated REST API; `eka` is not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.node_parser import MarkdownNodeParser, SentenceSplitter
from llama_index.core.schema import BaseNode, MetadataMode
from llama_index.core.utils import get_tokenizer
from llama_index.vector_stores.postgres import PGVectorStore
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine, make_url

from .access import AccessPolicy
from .corpus import load_documents
from .providers import embedding_dim
from .settings import Settings
from .usage import load_pricing

HNSW_MAX_DIM = 2000  # pgvector's limit for HNSW on `vector`; `halfvec` goes to 4000


@dataclass(frozen=True)
class IndexSpec:
    chunk_size: int
    chunk_overlap: int
    chunker: str  # "sentence" | "markdown"
    embed_model: str

    @classmethod
    def from_settings(cls, s: Settings) -> "IndexSpec":
        return cls(s.chunk_size, s.chunk_overlap, s.chunker, s.embed_model)

    @property
    def table(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "", self.embed_model.lower())[-22:]
        return f"c{self.chunk_size}o{self.chunk_overlap}_{self.chunker[:2]}_{slug}"

    @property
    def physical_table(self) -> str:
        return f"data_{self.table}"  # PGVectorStore adds the prefix


def _urls(settings: Settings) -> tuple[URL, URL]:
    base = make_url(settings.database_url.get_secret_value().replace("postgres://", "postgresql://", 1))
    return base.set(drivername="postgresql+psycopg2"), base.set(drivername="postgresql+asyncpg")


def _store_urls(settings: Settings) -> tuple[str, str]:
    """Connection strings for the vector store.

    The store keeps them as plain strings, and str(URL) replaces the password
    with "***", so they are rendered explicitly. Never log these.
    """
    sync_url, async_url = _urls(settings)
    return sync_url.render_as_string(hide_password=False), async_url.render_as_string(hide_password=False)


def admin_engine(settings: Settings) -> Engine:
    return create_engine(_urls(settings)[0], pool_pre_ping=True)


def row_count(settings: Settings, spec: IndexSpec) -> int | None:
    """Number of chunks in the table, or None if the table does not exist."""
    engine = admin_engine(settings)
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("select to_regclass(:name)"),
                {"name": f"{settings.db_schema}.{spec.physical_table}"},
            ).scalar()
            if exists is None:
                return None
            return conn.execute(
                text(f'select count(*) from "{settings.db_schema}"."{spec.physical_table}"')
            ).scalar_one()
    finally:
        engine.dispose()


def open_store(settings: Settings, spec: IndexSpec, dim: int, *, create: bool) -> PGVectorStore:
    sync_url, async_url = _store_urls(settings)
    halfvec = dim > HNSW_MAX_DIM
    return PGVectorStore(
        connection_string=sync_url,
        async_connection_string=async_url,
        table_name=spec.table,
        schema_name=settings.db_schema,
        embed_dim=dim,
        hybrid_search=True,  # adds a tsvector column + GIN index for keyword search
        text_search_config="english",
        use_jsonb=True,
        use_halfvec=halfvec,
        hnsw_kwargs={
            "hnsw_m": 16,
            "hnsw_ef_construction": 64,
            "hnsw_ef_search": 60,
            "hnsw_dist_method": "halfvec_cosine_ops" if halfvec else "vector_cosine_ops",
        },
        perform_setup=create,  # no DDL on the serving path
        initialization_fail_on_error=create,
    )


def build_nodes(settings: Settings, policy: AccessPolicy, spec: IndexSpec) -> list[BaseNode]:
    docs = load_documents(settings.content_dir, policy)
    splitter = SentenceSplitter(chunk_size=spec.chunk_size, chunk_overlap=spec.chunk_overlap)
    if spec.chunker == "markdown":
        # Split on headings first so a chunk never straddles two sections, and
        # carry the heading path into the embedded text.
        sections = MarkdownNodeParser().get_nodes_from_documents(docs)
        return splitter(sections)
    return splitter.get_nodes_from_documents(docs)


def ingest(
    settings: Settings,
    policy: AccessPolicy,
    spec: IndexSpec,
    embed_model: BaseEmbedding,
    *,
    recreate: bool = False,
    dry_run: bool = False,
    batch_size: int = 64,
    log: Callable[[str], None] = print,
) -> dict:
    nodes = build_nodes(settings, policy, spec)
    texts = [n.get_content(metadata_mode=MetadataMode.EMBED) for n in nodes]
    tokenizer = get_tokenizer()
    tokens = sum(len(tokenizer(t)) for t in texts)
    price = load_pricing().embedding_price(settings.embed_model)
    stats = {
        "table": f"{settings.db_schema}.{spec.physical_table}",
        "pages": len({n.metadata["path"] for n in nodes}),
        "chunks": len(nodes),
        "embed_tokens_est": tokens,
        "embed_cost_usd_est": None if price is None else round(tokens / 1e6 * price, 4),
        "groups": _count_by(nodes, "access_group"),
    }
    if settings.embed_provider == "local" and dry_run:
        stats["chunks_over_model_limit_pct"] = _over_limit_pct(settings.embed_model, texts)
    if dry_run:
        return stats | {"status": "dry_run"}

    existing = row_count(settings, spec)
    if existing and not recreate:
        log(f"{stats['table']} already has {existing} chunks. Use --recreate to rebuild it.")
        return stats | {"status": "exists", "chunks": existing}

    store = open_store(settings, spec, embedding_dim(embed_model), create=True)
    if existing:
        store.clear()

    for start in range(0, len(nodes), batch_size):
        batch = nodes[start : start + batch_size]
        vectors = embed_model.get_text_embedding_batch(texts[start : start + batch_size])
        for node, vec in zip(batch, vectors):
            node.embedding = vec
        store.add(batch)
        log(f"  embedded {min(start + batch_size, len(nodes))}/{len(nodes)} chunks")
    return stats | {"status": "ingested"}


def _over_limit_pct(model: str, texts: list[str], limit: int = 512) -> float | None:
    """Share of chunks longer than the embedding model can read (the excess is silently cut off)."""
    try:
        from tokenizers import Tokenizer

        tok = Tokenizer.from_pretrained(model)
        tok.no_truncation()
        over = sum(1 for enc in tok.encode_batch(texts) if len(enc.ids) > limit)
        return round(100 * over / max(1, len(texts)), 2)
    except Exception:
        return None


def _count_by(nodes: list[BaseNode], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for n in nodes:
        out[n.metadata.get(key, "?")] = out.get(n.metadata.get(key, "?"), 0) + 1
    return dict(sorted(out.items()))
