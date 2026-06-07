"""FastAPI application factory.

The service is a thin shell around the governed-state runtime. It wires a
SQLite-backed :class:`RunService` onto ``app.state`` and mounts the route
modules. No governance, pruning, or model logic lives in this layer.

FastAPI/uvicorn are optional dependencies (``pip install anchorprune[api]``).
Importing this module requires FastAPI, but importing the AnchorPrune core does
not.
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from anchorprune import __version__
from anchorprune.api.errors import register_error_handlers
from anchorprune.api.routes import (
    audit,
    health,
    metrics,
    payload,
    runs,
    state,
    steps,
)
from anchorprune.services import RunService
from anchorprune.storage import RunRepository, SQLiteRunRepository

DESCRIPTION = (
    "Local-first service layer around the AnchorPrune governed-state runtime. "
    "Persists runs, state snapshots, audit events, and metrics to SQLite. "
    "The service wraps the runtime; it does not redefine the method."
)


def create_app(
    *,
    database_path: str = ".anchorprune/anchorprune.db",
    repository: Optional[RunRepository] = None,
) -> FastAPI:
    app = FastAPI(
        title="AnchorPrune API",
        version=__version__,
        description=DESCRIPTION,
    )

    # Local-first CORS: the read-only dashboard runs on a different localhost
    # origin (e.g. :3000) than the API (:8000), so the browser needs permissive
    # CORS to read responses. This is transport configuration only — it changes
    # no governance, pruning, or model behavior. No credentials are used.
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    repo = repository or SQLiteRunRepository(database_path)
    app.state.repository = repo
    app.state.run_service = RunService(repo)

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(runs.router)
    app.include_router(payload.router)
    app.include_router(steps.router)
    app.include_router(state.router)
    app.include_router(audit.router)
    app.include_router(metrics.router)

    return app
