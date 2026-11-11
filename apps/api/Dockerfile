# syntax=docker/dockerfile:1.7
# Build context: repository root (uv workspace). `docker compose build api`
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

WORKDIR /app

# 1) third-party dependencies only (cached layer)
COPY pyproject.toml uv.lock .python-version ./
COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY packages/economics/pyproject.toml packages/economics/pyproject.toml
COPY packages/ml/pyproject.toml packages/ml/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --all-packages --no-install-workspace

# 2) workspace sources
COPY apps/api apps/api
COPY packages/economics packages/economics
COPY packages/ml packages/ml
# Genuine demo snapshot (108 KB) for `macropulse demo-load` without network or keys.
COPY data/demo data/demo
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --all-packages

RUN useradd --create-home --uid 10001 app \
    && mkdir -p /app/data /app/models/artifacts \
    && chown -R app /app/data /app/models
USER app
# Trained artifacts live on a volume (compose: `models`); train with `docker compose exec api macropulse train`.
ENV PATH="/app/.venv/bin:${PATH}" \
    MODELS_DIR=/app/models/artifacts

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2).status == 200 else 1)"

# Migrations + registry sync are idempotent, so running them on start is safe.
CMD ["sh", "-c", "macropulse db upgrade && macropulse serve --host 0.0.0.0 --port 8000"]
