FROM python:3.12-slim

# uv binary, pinned via the official image
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv

WORKDIR /app

# uv settings for containers:
# - copy mode: files are copied, not linked (venv mount-safe)
# - no cache: don't leave build cache in the image
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

# persistent cache for uv downloads
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# App code + baked data
COPY api/ ./api/
COPY data/bronze/ ./data/bronze/

EXPOSE 8080

# Run inside the uv-managed venv
CMD ["uv", "run", "--no-sync", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]