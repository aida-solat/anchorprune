"""Run lifecycle routes: create, list, get, delete.

Routes translate schemas <-> service calls. No governance logic here.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from anchorprune.api.dependencies import get_run_service
from anchorprune.api.schemas import (
    CreateRunRequest,
    CreateRunResponse,
    DeleteRunResponse,
    RunListResponse,
    RunResponse,
)
from anchorprune.services import RunService

router = APIRouter(prefix="/runs", tags=["runs"])


def _to_run_response(run) -> RunResponse:
    return RunResponse(
        run_id=run.id,
        goal=run.goal,
        domain=run.domain,
        status=run.status,
        config_name=run.config_name,
        metadata=run.metadata,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


@router.post("", response_model=CreateRunResponse, status_code=201)
def create_run(
    request: CreateRunRequest,
    service: RunService = Depends(get_run_service),
) -> CreateRunResponse:
    run = service.create_run(
        goal=request.goal,
        domain=request.domain,
        config_name=request.config_name,
        system_anchors=[a.model_dump() for a in request.system_anchors],
        metadata=request.metadata,
    )
    return CreateRunResponse(run_id=run.id, status=run.status, domain=run.domain)


@router.get("", response_model=RunListResponse)
def list_runs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    domain: Optional[str] = Query(None),
    service: RunService = Depends(get_run_service),
) -> RunListResponse:
    runs = service.list_runs(limit=limit, offset=offset, domain=domain)
    items = [_to_run_response(r) for r in runs]
    total = service.count_runs(domain=domain)
    return RunListResponse(
        runs=items, count=len(items), limit=limit, offset=offset, total=total
    )


@router.get("/{run_id}", response_model=RunResponse)
def get_run(
    run_id: str,
    service: RunService = Depends(get_run_service),
) -> RunResponse:
    return _to_run_response(service.get_run(run_id))


@router.delete("/{run_id}", response_model=DeleteRunResponse)
def delete_run(
    run_id: str,
    service: RunService = Depends(get_run_service),
) -> DeleteRunResponse:
    service.delete_run(run_id)
    return DeleteRunResponse(run_id=run_id)
