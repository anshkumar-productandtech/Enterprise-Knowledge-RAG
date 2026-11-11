"""HTTP API for the chat UI.

    uvicorn eka.api:app --port 8000

Hardening that matters for a public demo paid for from a personal API key:
  - a shared bearer token, so only the Next.js server can call this API
  - a per-client rate limit and a question length cap
  - CORS restricted to the configured origins
  - question text is not logged unless LOG_QUESTIONS=true
"""

from __future__ import annotations

import hmac
import json
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Iterator

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .access import get_policy
from .assistant import Assistant, Result
from .settings import Settings, get_settings

log = logging.getLogger("eka.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


class ChatRequest(BaseModel):
    question: str = Field(min_length=3)
    # Demo only: lets a visitor switch persona. A real deployment derives the
    # role from the authenticated session and ignores anything the client sends.
    role: str = "employee"


class RateLimiter:
    """Sliding one-minute window per client. In-memory: fine for one instance."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, client: str) -> None:
        now = time.monotonic()
        window = self.hits[client]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.per_minute:
            raise HTTPException(429, "Too many questions. Wait a minute and try again.")
        window.append(now)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.limiter = RateLimiter(settings.rate_limit_per_minute)
    app.state.assistant = Assistant(settings)
    if settings.demo_api_token is None:
        log.warning("DEMO_API_TOKEN is not set: the API accepts unauthenticated calls. Local use only.")
    yield


app = FastAPI(title="Enterprise Knowledge Assistant", lifespan=lifespan, docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().origins,
    allow_methods=["GET", "POST"],
    allow_headers=["authorization", "content-type"],
)


def require_token(request: Request) -> None:
    settings: Settings = request.app.state.settings
    if settings.demo_api_token is None:
        return
    supplied = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
    expected = settings.demo_api_token.get_secret_value()
    if not hmac.compare_digest(supplied.encode(), expected.encode()):
        raise HTTPException(401, "Unauthorized")


def client_id(request: Request) -> str:
    # Behind the Next.js proxy the visitor's address arrives in x-forwarded-for.
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/roles", dependencies=[Depends(require_token)])
def roles() -> list[dict]:
    return [
        {"name": r.name, "label": r.label, "description": r.description}
        for r in get_policy().roles.values()
    ]


@app.post("/chat", dependencies=[Depends(require_token)])
def chat(body: ChatRequest, request: Request) -> StreamingResponse:
    settings: Settings = request.app.state.settings
    assistant: Assistant = request.app.state.assistant

    question = " ".join(body.question.split())
    if len(question) > settings.max_question_chars:
        raise HTTPException(413, f"Keep questions under {settings.max_question_chars} characters.")
    if body.role not in assistant.policy.roles:
        raise HTTPException(400, "Unknown role")
    request.app.state.limiter.check(client_id(request))

    def events() -> Iterator[str]:
        try:
            for kind, payload in assistant.stream(question, body.role):
                if kind == "done":
                    result: Result = payload  # type: ignore[assignment]
                    summary = result.summary()
                    log.info(
                        "chat role=%s refused=%s cited=%d total_ms=%s%s",
                        body.role, summary["refused"], len(summary["cited"]),
                        summary["timings_ms"].get("total"),
                        f" q={question!r}" if settings.log_questions else "",
                    )
                    yield sse("done", summary)
                else:
                    yield sse(kind, payload)
        except Exception:
            # Full detail goes to the server log; the browser gets a generic message
            # so provider errors (which can echo request details) never reach users.
            log.exception("chat failed")
            yield sse("error", {"message": "Something went wrong answering that. Please try again."})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"cache-control": "no-cache", "x-accel-buffering": "no"},
    )
