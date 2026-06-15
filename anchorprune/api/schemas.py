"""Request/response schemas for the AnchorPrune API.

These are the HTTP contract only. They never contain governance, pruning, or
model logic — routes translate between these schemas and the service layer.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ---- health ---------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


# ---- runs -----------------------------------------------------------------


class SystemAnchorSpec(BaseModel):
    content: str
    anchor_type: str = "policy"
    priority: str = "critical"


class CreateRunRequest(BaseModel):
    goal: str
    domain: str = "default"
    config_name: str = "mock"
    system_anchors: List[SystemAnchorSpec] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreateRunResponse(BaseModel):
    run_id: str
    status: str
    domain: str


class RunResponse(BaseModel):
    run_id: str
    goal: str
    domain: str
    status: str
    config_name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class RunListResponse(BaseModel):
    runs: List[RunResponse]
    count: int
    # Pagination metadata (v0.9). Added without removing existing fields, so the
    # dashboard and earlier clients that read ``runs``/``count`` are unaffected.
    limit: int = 50
    offset: int = 0
    total: int = 0


class DeleteRunResponse(BaseModel):
    run_id: str
    status: str = "deleted"


# ---- payload --------------------------------------------------------------


class AddPayloadRequest(BaseModel):
    block_type: str = "tool_output"
    content: str
    decision_impact: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AddPayloadResponse(BaseModel):
    run_id: str
    payload_block_id: str
    status: str = "added"


# ---- steps ----------------------------------------------------------------


class RunStepRequest(BaseModel):
    instruction: str


class StepMetrics(BaseModel):
    input_tokens: int
    output_tokens: int


class RunStepResponse(BaseModel):
    run_id: str
    step_id: str
    step_index: int
    model_output: str
    state_summary: Dict[str, int]
    pruning_summary: Dict[str, int]
    metrics: StepMetrics


# ---- state / audit / metrics ---------------------------------------------


class StateResponse(BaseModel):
    run_id: str
    goal: str
    domain: str
    step_index: int
    anchors: List[Dict[str, Any]]
    payload_blocks: List[Dict[str, Any]]
    milestones: List[Dict[str, Any]]
    conflict_edges: List[Dict[str, Any]]
    payload_block_count: int


class AuditEvent(BaseModel):
    event_type: str
    step_index: int
    payload: Dict[str, Any]
    created_at: str


class AuditResponse(BaseModel):
    run_id: str
    events: List[AuditEvent]
    # Pagination metadata (v0.9); existing ``events`` field is preserved.
    limit: Optional[int] = None
    offset: int = 0
    total: int = 0


class MetricsResponse(BaseModel):
    run_id: str
    steps: List[Dict[str, Any]]
    summary: Dict[str, Any]
    # Pagination metadata (v0.9); ``steps``/``summary`` are preserved.
    limit: Optional[int] = None
    offset: int = 0
    total: int = 0
