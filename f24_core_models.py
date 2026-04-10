from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from f25_core_types import (
    AgentName,
    ArtifactKind,
    MemoryKind,
    MemoryScope,
    RunStatus,
    TaskStatus,
    TaskType,
)


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True, use_enum_values=False)


class RunCreate(APIModel):
    project_key: str = "default-project"
    adapter_key: str = "research_project"
    goal: str
    input_payload: dict[str, Any] = Field(default_factory=dict)


class RunView(APIModel):
    run_id: str
    project_key: str
    adapter_key: str
    goal: str
    status: RunStatus
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TaskCreate(APIModel):
    run_id: str
    task_type: TaskType
    assigned_agent: AgentName
    title: str
    input_payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = 100
    parent_task_id: str | None = None


class TaskView(APIModel):
    task_id: str
    run_id: str
    task_type: TaskType
    assigned_agent: AgentName
    title: str
    status: TaskStatus
    priority: int
    attempt_count: int
    input_payload: dict[str, Any]
    output_payload: dict[str, Any]
    error_payload: dict[str, Any]
    lease_expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MemoryCreate(APIModel):
    run_id: str | None = None
    project_key: str
    scope: MemoryScope
    kind: MemoryKind
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryView(APIModel):
    memory_id: str
    run_id: str | None
    project_key: str
    scope: MemoryScope
    kind: MemoryKind
    title: str
    content: str
    metadata: dict[str, Any]
    created_at: datetime


class ArtifactCreate(APIModel):
    run_id: str
    task_id: str | None = None
    project_key: str
    artifact_kind: ArtifactKind
    title: str
    body: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArtifactView(APIModel):
    artifact_id: str
    run_id: str
    task_id: str | None
    project_key: str
    artifact_kind: ArtifactKind
    title: str
    body: str
    metadata: dict[str, Any]
    created_at: datetime


class HealthView(APIModel):
    ok: bool
    app_env: str
    db_ok: bool
    llm_ok: bool
    timestamp: str