# AnchorPrune API image (v0.9) — local-first FastAPI service.
#
# Local-first: this image is intended for local / trusted-network use. Do NOT
# expose the service directly to the public internet (no auth in v0.9). See
# docs/security.md.
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install only what the package needs to build + run the API extra.
COPY pyproject.toml README.md ./
COPY anchorprune ./anchorprune
COPY examples ./examples

RUN pip install ".[api]"

# Run as a non-root user; persist the SQLite DB under /data.
RUN useradd --create-home --uid 10001 anchorprune \
    && mkdir -p /data \
    && chown -R anchorprune:anchorprune /data
USER anchorprune

VOLUME ["/data"]
EXPOSE 8000

CMD ["anchorprune", "serve", "--host", "0.0.0.0", "--port", "8000", \
     "--db", "/data/anchorprune.db", "--log-format", "json"]
