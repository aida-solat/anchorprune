"""State retrieval route."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from anchorprune.api.dependencies import get_run_service
from anchorprune.api.schemas import StateResponse
from anchorprune.services import RunService

router = APIRouter(prefix="/runs", tags=["state"])


@router.get("/{run_id}/state", response_model=StateResponse)
def get_state(
    run_id: str,
    include_payload: bool = Query(True),
    service: RunService = Depends(get_run_service),
) -> StateResponse:
    state = service.get_state(run_id, include_payload=include_payload)
    return StateResponse(**state)
