# Backend image for a container host (Render, Fly.io, Railway, Cloud Run).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY eka ./eka
COPY config ./config

# Run as an unprivileged user. Secrets come from the host's environment settings, never from the image.
RUN useradd --create-home app
USER app

# Sentence-splitting data, fetched at build time into a directory the app user owns.
ENV NLTK_DATA=/home/app/nltk_data
RUN python -m nltk.downloader -d "$NLTK_DATA" punkt_tab stopwords

# Open-source embedding model (and reranker, if the serving config uses one), baked into the image.
ENV FASTEMBED_CACHE_PATH=/home/app/.cache/fastembed
ARG EMBED_MODEL=BAAI/bge-small-en-v1.5
ARG RERANK_MODEL=
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('${EMBED_MODEL}')" \
 && if [ -n "${RERANK_MODEL}" ]; then python -c "from fastembed.rerank.cross_encoder import TextCrossEncoder; TextCrossEncoder('${RERANK_MODEL}')"; fi

EXPOSE 8000
CMD ["sh", "-c", "uvicorn eka.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
