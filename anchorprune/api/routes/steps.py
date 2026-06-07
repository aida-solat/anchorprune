"""Step execution route."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from anchorprune.api.dependencies import get_run_service
from anchorprune.api.schemas import RunStepRequest, RunStepResponse, StepMetrics
from anchorprune.services import RunService

router = APIRouter(prefix="/runs", tags=["steps"])


@router.post("/{run_id}/steps", response_model=RunStepResponse)
def run_step(
    run_id: str,
    request: RunStepRequest,
    service: RunService = Depends(get_run_service),
) -> RunStepResponse:
    result = service.run_step(run_id, instruction=request.instruction)
    return RunStepResponse(
        run_id=result["run_id"],
        step_id=result["step_id"],
        step_index=result["step_index"],
        model_output=result["model_output"],
        state_summary=result["state_summary"],
        pruning_summary=result["pruning_summary"],
        metrics=StepMetrics(**result["metrics"]),
    )
