"""Test setup. Everything runs on the mock models and a fictional corpus: no API keys, no cost.

Integration tests need a Postgres with pgvector. Point TEST_DATABASE_URL at one
(`docker compose up -d` gives you postgresql://postgres:postgres@localhost:5433/eka);
without it those tests are skipped.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

# Settings are read at import time by eka.api, so the environment is set here first.
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://unused:unused@localhost:1/unused"
)
os.environ.update(
    LLM_PROVIDER="mock", LLM_MODEL="mock", EMBED_PROVIDER="mock", EMBED_MODEL="mock",
    RERANK_PROVIDER="none", HANDBOOK_CONTENT_DIR=str(FIXTURES / "content"),
    DB_SCHEMA="eka_test", DEMO_API_TOKEN="", RATE_LIMIT_PER_MINUTE="3",
)


@pytest.fixture(scope="session")
def settings():
    from eka.settings import Settings

    return Settings(_env_file=None)  # type: ignore[call-arg]


@pytest.fixture(scope="session")
def policy():
    from eka.access import load_policy

    return load_policy(FIXTURES / "corpus.yaml")


@pytest.fixture(scope="session")
def db(settings):
    if "TEST_DATABASE_URL" not in os.environ:
        pytest.skip("TEST_DATABASE_URL not set")
    return settings
