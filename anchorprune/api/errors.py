"""API error handling.

Maps the AnchorPrune error taxonomy (:mod:`anchorprune.errors`) to a single,
stable HTTP response shape:

    {"error": {"code": "RUN_NOT_FOUND", "message": "...", "details": {...}}}

Keeping this in one place means routes never construct error responses by hand.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from anchorprune.errors import AnchorPruneError, error_payload


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AnchorPruneError)
    async def _anchorprune_error(
        request: Request, exc: AnchorPruneError
    ) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    @app.exception_handler(ValueError)
    async def _value_error(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=error_payload("BAD_REQUEST", str(exc)),
        )
