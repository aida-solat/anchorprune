"""API error handling.

Maps service-layer exceptions to HTTP responses. Keeping this in one place means
routes never construct error responses by hand.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from anchorprune.services.run_service import RunNotFoundError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RunNotFoundError)
    async def _run_not_found(request: Request, exc: RunNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"error": "run_not_found", "run_id": str(exc)},
        )

    @app.exception_handler(ValueError)
    async def _value_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": "bad_request", "detail": str(exc)},
        )
