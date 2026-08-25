"""Secret-free administrator collector status response contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class CollectorQueueStatus(BaseModel):
    queue_name: str
    broker_available: bool
    worker_available: bool
    worker_count: int


class CollectorScheduleStatus(BaseModel):
    enabled: bool
    source_id: str
    requested_count: int
    complete_snapshot: bool
    cron_hour: int
    cron_minute: int
    timezone: str


class CollectorRunSummary(BaseModel):
    run_id: UUID
    status: str
    trigger_type: str
    started_at: datetime
    finished_at: datetime | None
    is_stale: bool
    requested_count: int
    inserted_count: int
    updated_count: int
    failed_count: int
    error_type: str | None


class AdminCollectorStatus(BaseModel):
    source_id: str
    display_name: str
    source_type: Literal["api", "file", "web"]
    manual_run_enabled: bool
    runtime_status: Literal[
        "ready",
        "configuration_required",
        "unavailable",
        "unknown",
    ]
    worker_registered: bool | None
    credential_status: Literal[
        "configured",
        "missing",
        "not_required",
        "unknown",
    ]
    public_policy_count: int
    active_run: CollectorRunSummary | None
    last_run: CollectorRunSummary | None


class AdminCollectorStatusResponse(BaseModel):
    generated_at: datetime
    queue: CollectorQueueStatus
    schedule: CollectorScheduleStatus
    collectors: list[AdminCollectorStatus]

