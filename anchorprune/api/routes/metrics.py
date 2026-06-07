"""Metrics route."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from anchorprune.api.dependencies import get_run_service
from anchorprune.api.schemas import MetricsResponse
from anchorprune.services import RunService

router = APIRouter(prefix="/runs", tags=["metrics"])


@router.get("/{run_id}/metrics", response_model=MetricsResponse)
def get_metrics(
    run_id: str,
    service: RunService = Depends(get_run_service),
) -> MetricsResponse:
    return MetricsResponse(**service.get_metrics(run_id))
