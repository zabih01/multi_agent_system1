from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentMessage(BaseModel):
    sender: str
    recipient: str | None = None
    content: str
    task_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskSpec(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    agent_name: str
    dependencies: list[str] = Field(default_factory=list)
    priority: int = Field(default=5, ge=1, le=10)
    timeout_seconds: float = Field(default=30.0, gt=0)
    max_retries: int = Field(default=2, ge=0, le=8)
    input_data: dict[str, Any] = Field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=utcnow)


class TaskResult(BaseModel):
    task_id: str
    agent_name: str
    status: TaskStatus
    output: Any = None
    error: str | None = None
    attempts: int = 1
    started_at: datetime | None = None
    finished_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewFeedback(BaseModel):
    approved: bool
    score: float = Field(ge=0, le=1)
    findings: list[str] = Field(default_factory=list)
    requested_changes: list[str] = Field(default_factory=list)


class WorkflowReport(BaseModel):
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    objective: str
    status: str
    results: list[TaskResult]
    summary: str
    started_at: datetime
    finished_at: datetime = Field(default_factory=utcnow)
