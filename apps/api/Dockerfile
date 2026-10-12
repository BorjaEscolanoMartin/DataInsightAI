# uv is pinned by version and digest and only used to install dependencies from uv.lock.
FROM ghcr.io/astral-sh/uv:0.11.11@sha256:798712e57f879c5393777cbda2bb309b29fcdeb0532129d4b1c3125c5385975a AS uv

FROM python:3.12-slim AS base

WORKDIR /app

# The virtualenv lives outside /app so the dev bind mount does not hide it. The app is not
# installed as a package: PYTHONPATH lets uvicorn, Alembic and Celery import it from any cwd.
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy

# Unprivileged runtime user with its own writable HOME (libraries cache under ~/.cache).
# UID/GID 1000 match the usual host user, so files written to dev bind mounts stay theirs.
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd --gid "$APP_GID" app \
    && useradd --uid "$APP_UID" --gid app --create-home --shell /usr/sbin/nologin app

# ── Production dependencies (build stage only) ───────────────────────────────
FROM base AS builder
COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
# --locked fails the build when uv.lock does not match pyproject.toml.
RUN uv sync --locked --no-install-project --no-cache

# ── Development (dev extras; keeps uv to manage dependencies) ────────────────
FROM base AS dev
COPY --from=uv /uv /usr/local/bin/uv
# The dev venv belongs to app so dependencies can be managed from inside the container.
RUN mkdir /opt/venv && chown app:app /opt/venv
COPY pyproject.toml uv.lock ./
USER app
RUN uv sync --locked --no-install-project --no-cache --extra dev
COPY . .
CMD ["bash", "start.sh"]

# ── Production (no uv, no dev extras) ────────────────────────────────────────
FROM base AS prod
COPY --from=builder /opt/venv /opt/venv
COPY . .
# Code and venv stay root-owned: the process can read them but not modify them.
USER app
CMD ["bash", "start.sh"]
