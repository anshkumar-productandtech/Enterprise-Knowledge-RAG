# Backend image for a container host (Render, Fly.io, Railway, Cloud Run).
# Not built or run as part of this project's tests: build it once locally before deploying.
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

EXPOSE 8000
CMD ["sh", "-c", "uvicorn eka.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
