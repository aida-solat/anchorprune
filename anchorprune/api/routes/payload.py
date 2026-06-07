"""Payload ingestion route."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from anchorprune.api.dependencies import get_run_service
from anchorprune.api.schemas import AddPayloadRequest, AddPayloadResponse
from anchorprune.services import RunService

router = APIRouter(prefix="/runs", tags=["payload"])


@router.post("/{run_id}/payload", response_model=AddPayloadResponse)
def add_payload(
    run_id: str,
    request: AddPayloadRequest,
    service: RunService = Depends(get_run_service),
) -> AddPayloadResponse:
    block_id = service.add_payload(
        run_id,
        block_type=request.block_type,
        content=request.content,
        decision_impact=request.decision_impact,
        metadata=request.metadata,
    )
    return AddPayloadResponse(run_id=run_id, payload_block_id=block_id)
