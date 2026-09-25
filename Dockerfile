FROM python:3.12-slim

# uv binary, pinned via the official image
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv

# Azure Container Apps will happily run it as anything
RUN useradd --create-home --uid 1000 app
WORKDIR /app

# uv settings for containers:
# - copy mode: files are copied, not linked (venv mount-safe)
# - bytecode precompiled: faster container startup
# - PYTHON_DOWNLOADS=never: use the base image's interpreter only
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

# persistent cache for uv downloads
COPY --chown=app:app pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-group pipeline \
    && chown -R app:app /app/.venv

# App code + baked data
COPY --chown=app:app api/ ./api/
COPY --chown=app:app data/bronze/ ./data/bronze/

# Add the data/bronze guard. Checks that the Bronze pipeline actually ran, which COPY alone doesn't verify.
RUN test -d data/bronze/policy/_delta_log \
    || (echo "data/bronze/policy/_delta_log missing — Bronze not built" && exit 1)

USER app

EXPOSE 8080




# Run inside the uv-managed venv
# api.main:app, module api/main.py, attribute app
# api: package (a folder with __init__.py)
# main: module lives inside api/main.py
# attribute: app lives inside api/main.py where app = FastAPI()
# --host 0.0.0.0 binds to all interfaces inside the container so the port is reachable from outside
CMD ["uv", "run", "--no-sync", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]