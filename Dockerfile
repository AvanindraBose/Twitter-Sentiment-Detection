FROM python:3.11-slim AS builder


ENV UV_LINK_MODE=copy \
    NLTK_DATA=/usr/local/share/nltk_data

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY ./scripts/ scripts/
RUN mkdir -p "$NLTK_DATA" \
    && uv run python scripts/setup_nltk.py

FROM python:3.11-slim AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    NLTK_DATA=/usr/local/share/nltk_data \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv ./.venv
COPY --from=builder /usr/local/share/nltk_data /usr/local/share/nltk_data
COPY ./backend/ backend/
COPY ./src/logger_class.py src/logger_class.py

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
