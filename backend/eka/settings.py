"""Runtime configuration, read from environment variables or backend/.env.

API keys are SecretStr so they never show up in logs, reprs or error pages.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

LLMProvider = Literal["openai", "anthropic", "gemini", "mock"]
EmbedProvider = Literal["openai", "voyage", "gemini", "local", "mock"]
RerankProvider = Literal["cohere", "local", "none"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: SecretStr

    llm_provider: LLMProvider = "mock"
    llm_model: str = "mock"
    embed_provider: EmbedProvider = "mock"
    embed_model: str = "mock"
    rerank_provider: RerankProvider = "none"
    rerank_model: str | None = None
    judge_provider: LLMProvider | None = None
    judge_model: str | None = None

    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None
    voyage_api_key: SecretStr | None = None
    cohere_api_key: SecretStr | None = None

    handbook_content_dir: Path = Path("data/handbook/content")
    db_schema: str = "eka"

    # Serving defaults. Point these at the winning experiment.
    chunk_size: int = 256
    chunk_overlap: int = 32
    chunker: Literal["sentence", "markdown"] = "sentence"
    search_mode: Literal["vector", "hybrid"] = "hybrid"
    top_k: int = 5
    candidate_k: int = 20

    allowed_origins: str = "http://localhost:3000"
    rate_limit_per_minute: int = 20
    max_question_chars: int = 500
    demo_api_token: SecretStr | None = None
    log_questions: bool = False

    @field_validator("judge_provider", "judge_model", "rerank_model", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        return v or None

    @field_validator(
        "openai_api_key", "anthropic_api_key", "google_api_key", "voyage_api_key",
        "cohere_api_key", "demo_api_token", mode="before",
    )
    @classmethod
    def _blank_secret_to_none(cls, v):
        return v or None

    @property
    def content_dir(self) -> Path:
        p = self.handbook_content_dir
        return p if p.is_absolute() else BACKEND_DIR / p

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    def require_key(self, name: str) -> str:
        """Return an API key or fail with a message that names the variable, not the value."""
        secret: SecretStr | None = getattr(self, name)
        if secret is None:
            raise RuntimeError(f"{name.upper()} is not set. Add it to backend/.env.")
        return secret.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
