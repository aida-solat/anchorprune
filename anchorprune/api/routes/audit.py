"""Audit trail route."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from anchorprune.api.dependencies import get_run_service
from anchorprune.api.schemas import AuditEvent, AuditResponse
from anchorprune.services import RunService

router = APIRouter(prefix="/runs", tags=["audit"])


@router.get("/{run_id}/audit", response_model=AuditResponse)
def get_audit(
    run_id: str,
    service: RunService = Depends(get_run_service),
) -> AuditResponse:
    events = service.get_audit(run_id)
    return AuditResponse(
        run_id=run_id,
        events=[AuditEvent(**e) for e in events],
    )
