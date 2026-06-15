"""Metrics route."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from anchorprune.api.dependencies import get_run_service
from anchorprune.api.schemas import MetricsResponse
from anchorprune.services import RunService

router = APIRouter(prefix="/runs", tags=["metrics"])


@router.get("/{run_id}/metrics", response_model=MetricsResponse)
def get_metrics(
    run_id: str,
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: RunService = Depends(get_run_service),
) -> MetricsResponse:
    return MetricsResponse(**service.get_metrics(run_id, limit=limit, offset=offset))
