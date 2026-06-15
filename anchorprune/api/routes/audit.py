"""Audit trail route."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from anchorprune.api.dependencies import get_run_service
from anchorprune.api.schemas import AuditEvent, AuditResponse
from anchorprune.services import RunService

router = APIRouter(prefix="/runs", tags=["audit"])


@router.get("/{run_id}/audit", response_model=AuditResponse)
def get_audit(
    run_id: str,
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: RunService = Depends(get_run_service),
) -> AuditResponse:
    result = service.get_audit(run_id, limit=limit, offset=offset)
    return AuditResponse(
        run_id=run_id,
        events=[AuditEvent(**e) for e in result["events"]],
        limit=result["limit"],
        offset=result["offset"],
        total=result["total"],
    )
