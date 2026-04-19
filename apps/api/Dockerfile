FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

# ── Development (includes dev extras for hot-reload) ────────────────────────
FROM base AS dev
RUN pip install --no-cache-dir -e ".[dev]"
COPY . .
RUN chmod +x start.sh
CMD ["bash", "start.sh"]

# ── Production (no dev extras) ───────────────────────────────────────────────
FROM base AS prod
RUN pip install --no-cache-dir -e .
COPY . .
RUN chmod +x start.sh
CMD ["bash", "start.sh"]
