"""Storage record dataclasses.

Plain, framework-free records that the repository reads and writes. These are
deliberately decoupled from both the API schemas and the runtime models so the
storage layer has no governance or HTTP concerns.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class RunRecord:
    id: str
    goal: str
    domain: str
    status: str
    config_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)


@dataclass
class StateSnapshotRecord:
    id: str
    run_id: str
    step_index: int
    state: Dict[str, Any]
    created_at: str = field(default_factory=now_iso)


@dataclass
class AuditEventRecord:
    id: str
    run_id: str
    event_type: str
    step_index: int
    payload: Dict[str, Any]
    created_at: str = field(default_factory=now_iso)


@dataclass
class StepMetricsRecord:
    id: str
    run_id: str
    step_index: int
    metrics: Dict[str, Any]
    created_at: str = field(default_factory=now_iso)
