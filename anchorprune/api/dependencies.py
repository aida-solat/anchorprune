"""Dependency injection.

The :class:`RunService` is stored on ``app.state`` by :func:`create_app`, so
tests can spin up an app against a temporary SQLite database (or override the
dependency) without globals.
"""

from __future__ import annotations

from fastapi import Request

from anchorprune.services import RunService


def get_run_service(request: Request) -> RunService:
    return request.app.state.run_service
