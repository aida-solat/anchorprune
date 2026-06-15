"""RunService — orchestration of the governed runtime over persistent storage.

This is the seam between HTTP and the runtime. Routes call these methods and do
nothing else; all persistence and runtime wiring lives here. Crucially, this
service contains **no** governance, pruning, or model logic — it delegates every
such decision to :class:`AnchorPruneRuntime`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from anchorprune.blocks.models import PayloadBlockType
from anchorprune.core.runtime import AnchorPruneRuntime, StepResult
from anchorprune.errors import NotFoundError
from anchorprune.services.runtime_service import RuntimeService
from anchorprune.storage.base import RunRepository
from anchorprune.storage.models import (
    AuditEventRecord,
    RunRecord,
    StateSnapshotRecord,
    StepMetricsRecord,
    new_id,
    now_iso,
)
from anchorprune.storage.serialization import serialize_runtime


class RunNotFoundError(NotFoundError):
    """Raised when a run id does not exist in storage."""

    code = "RUN_NOT_FOUND"

    def __init__(self, run_id: str) -> None:
        super().__init__(
            f"Run '{run_id}' was not found.", details={"run_id": run_id}
        )
        self.run_id = run_id


class RunService:
    def __init__(
        self,
        repository: RunRepository,
        runtime_service: Optional[RuntimeService] = None,
    ) -> None:
        self.repo = repository
        self.runtimes = runtime_service or RuntimeService()

    # ---- lifecycle --------------------------------------------------------

    def create_run(
        self,
        *,
        goal: str,
        domain: str = "default",
        config_name: str = "mock",
        system_anchors: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RunRecord:
        runtime = self.runtimes.build_new(domain=domain, config_name=config_name)
        runtime.create_run(goal=goal, system_anchors=system_anchors or [])

        run = RunRecord(
            id=runtime.graph.run_id,
            goal=goal,
            domain=runtime.domain_profile.name,
            status="created",
            config_name=config_name,
            metadata=metadata or {},
        )
        self.repo.create_run(run)
        self._persist_runtime(runtime, status=None)
        return run

    def get_run(self, run_id: str) -> RunRecord:
        run = self.repo.get_run(run_id)
        if run is None:
            raise RunNotFoundError(run_id)
        return run

    def list_runs(
        self, *, limit: int = 50, offset: int = 0, domain: Optional[str] = None
    ) -> List[RunRecord]:
        return self.repo.list_runs(limit=limit, offset=offset, domain=domain)

    def count_runs(self, *, domain: Optional[str] = None) -> int:
        return self.repo.count_runs(domain=domain)

    def delete_run(self, run_id: str) -> None:
        if not self.repo.delete_run(run_id):
            raise RunNotFoundError(run_id)

    # ---- payload & steps --------------------------------------------------

    def add_payload(
        self,
        run_id: str,
        *,
        block_type: str,
        content: str,
        decision_impact: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        runtime = self._load_runtime(run_id)
        block = runtime.add_payload(
            content,
            PayloadBlockType(block_type),
            decision_impact=decision_impact,
            metadata=metadata,
        )
        self._persist_runtime(runtime, status="active")
        return block.id

    def run_step(self, run_id: str, *, instruction: str) -> Dict[str, Any]:
        runtime = self._load_runtime(run_id)
        result: StepResult = runtime.run_step(instruction)
        self._persist_runtime(runtime, status="active")
        self._persist_step_metrics(run_id, result)
        step_number = result.step_index + 1
        return {
            "run_id": run_id,
            "step_id": f"step_{step_number:03d}",
            "step_index": result.step_index,
            "model_output": result.model_output,
            "state_summary": result.state_summary,
            "pruning_summary": result.pruning_summary,
            "metrics": {
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
            },
        }

    # ---- read models ------------------------------------------------------

    def get_state(self, run_id: str, *, include_payload: bool = True) -> Dict[str, Any]:
        snapshot = self._require_snapshot(run_id)
        graph = snapshot.state["graph"]
        anchors = list(graph.get("anchors", {}).values())
        payload_blocks = list(graph.get("payload_blocks", {}).values())
        milestones = list(graph.get("milestones", {}).values())
        state = {
            "run_id": run_id,
            "goal": graph.get("goal", ""),
            "domain": graph.get("domain", "default"),
            "step_index": graph.get("step_index", 0),
            "anchors": anchors,
            "milestones": milestones,
            "conflict_edges": graph.get("conflict_edges", []),
            "payload_blocks": payload_blocks if include_payload else [],
            "payload_block_count": len(payload_blocks),
        }
        return state

    def get_audit(
        self, run_id: str, *, limit: Optional[int] = None, offset: int = 0
    ) -> Dict[str, Any]:
        self.get_run(run_id)  # 404 if missing
        events = self.repo.list_audit_events(run_id, limit=limit, offset=offset)
        total = self.repo.count_audit_events(run_id)
        items = [
            {
                "event_type": e.event_type,
                "step_index": e.step_index,
                "payload": e.payload,
                "created_at": e.created_at,
            }
            for e in events
        ]
        return {
            "run_id": run_id,
            "events": items,
            "limit": limit,
            "offset": offset,
            "total": total,
        }

    def get_metrics(
        self, run_id: str, *, limit: Optional[int] = None, offset: int = 0
    ) -> Dict[str, Any]:
        self.get_run(run_id)  # 404 if missing
        # Summary is computed over ALL steps so it is stable regardless of paging.
        all_steps = [r.metrics for r in self.repo.list_step_metrics(run_id)]
        total = len(all_steps)
        total_in = sum(int(s.get("input_tokens", 0)) for s in all_steps)
        total_out = sum(int(s.get("output_tokens", 0)) for s in all_steps)
        max_context = max(
            (int(s.get("input_tokens", 0)) for s in all_steps), default=0
        )
        paged = self.repo.list_step_metrics(run_id, limit=limit, offset=offset)
        return {
            "run_id": run_id,
            "steps": [r.metrics for r in paged],
            "summary": {
                "total_steps": total,
                "total_input_tokens": total_in,
                "total_output_tokens": total_out,
                "max_context_size": max_context,
            },
            "limit": limit,
            "offset": offset,
            "total": total,
        }

    # ---- internals --------------------------------------------------------

    def _load_runtime(self, run_id: str) -> AnchorPruneRuntime:
        run = self.get_run(run_id)
        snapshot = self._require_snapshot(run_id)
        return self.runtimes.rehydrate(
            domain=run.domain,
            config_name=run.config_name,
            snapshot_state=snapshot.state,
        )

    def _require_snapshot(self, run_id: str) -> StateSnapshotRecord:
        self.get_run(run_id)  # 404 if missing
        snapshot = self.repo.latest_snapshot(run_id)
        if snapshot is None:
            raise RunNotFoundError(run_id)
        return snapshot

    def _persist_runtime(
        self, runtime: AnchorPruneRuntime, *, status: Optional[str]
    ) -> None:
        run_id = runtime.graph.run_id
        self.repo.add_snapshot(
            StateSnapshotRecord(
                id=new_id("snap"),
                run_id=run_id,
                step_index=runtime.graph.step_index,
                state=serialize_runtime(runtime),
            )
        )
        self.repo.add_audit_events(self._audit_records(run_id, runtime))
        run = self.repo.get_run(run_id)
        if run is not None:
            run.updated_at = now_iso()
            if status is not None:
                run.status = status
            self.repo.update_run(run)

    def _persist_step_metrics(self, run_id: str, result: StepResult) -> None:
        summary = result.state_summary
        self.repo.add_step_metrics(
            StepMetricsRecord(
                id=new_id("metric"),
                run_id=run_id,
                step_index=result.step_index,
                metrics={
                    "step": result.step_index + 1,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "anchors": summary.get("anchors", 0),
                    "payload_blocks": summary.get("payload_blocks", 0),
                    "quarantined": summary.get("quarantined_blocks", 0),
                },
            )
        )

    @staticmethod
    def _audit_records(
        run_id: str, runtime: AnchorPruneRuntime
    ) -> List[AuditEventRecord]:
        records: List[AuditEventRecord] = []
        for event in runtime.audit.events:
            records.append(
                AuditEventRecord(
                    id=event.id,
                    run_id=run_id,
                    event_type=event.event_type.value,
                    step_index=event.step_index,
                    payload=event.detail,
                    created_at=event.timestamp.isoformat(),
                )
            )
        return records
