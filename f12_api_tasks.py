import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from f22_core_db import execute, fetch_all, fetch_one, init_db

router = APIRouter()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_tasks_ready() -> None:
    init_db()


def _safe_parse_json(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return value


def _serialize(value: Any, fallback: Any) -> str:
    if value is None:
        value = fallback
    if isinstance(value, str):
        stripped = value.strip()
        if stripped:
            return stripped
        return json.dumps(fallback, ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False)


class TaskCreate(BaseModel):
    run_id: Optional[str] = None
    project_key: str = "demo-project"
    general_key: str = "general_of_the_army"
    task_type: str = "manual"
    title: str = "Manual mission dispatch"
    operator_message: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    payload_json: dict[str, Any] | None = None
    input_payload: dict[str, Any] | None = None


def _normalize_task_row(row: dict[str, Any]) -> dict[str, Any]:
    for key in (
        "payload_json",
        "result_json",
        "artifact_json",
        "input_payload",
        "output_payload",
        "error_payload",
    ):
        row[key] = _safe_parse_json(row.get(key))
    return row


@router.get("/tasks")
def list_tasks(
    run_id: Optional[str] = Query(default=None),
    project_key: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
):
    ensure_tasks_ready()

    where_parts: list[str] = []
    params: list[Any] = []

    if run_id:
        where_parts.append("run_id = ?")
        params.append(run_id)

    if project_key:
        where_parts.append("project_key = ?")
        params.append(project_key)

    if status:
        where_parts.append("status = ?")
        params.append(status)

    sql = """
        SELECT
            task_id,
            run_id,
            project_key,
            general_key,
            task_type,
            assigned_agent,
            title,
            operator_message,
            payload_json,
            input_payload,
            output_payload,
            error_payload,
            status,
            result_json,
            error_text,
            artifact_path,
            artifact_json,
            created_at,
            updated_at,
            lease_owner,
            lease_expires_at,
            attempt_count,
            priority
        FROM tasks
    """

    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)

    sql += " ORDER BY created_at DESC"

    rows = [_normalize_task_row(row) for row in fetch_all(sql, params)]
    return {"items": rows}


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    ensure_tasks_ready()

    row = fetch_one(
        """
        SELECT
            task_id,
            run_id,
            project_key,
            general_key,
            task_type,
            assigned_agent,
            title,
            operator_message,
            payload_json,
            input_payload,
            output_payload,
            error_payload,
            status,
            result_json,
            error_text,
            artifact_path,
            artifact_json,
            created_at,
            updated_at,
            lease_owner,
            lease_expires_at,
            attempt_count,
            priority
        FROM tasks
        WHERE task_id = ?
        """,
        [task_id],
    )

    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    return _normalize_task_row(row)


@router.post("/tasks")
def create_task(body: TaskCreate):
    ensure_tasks_ready()

    if not body.run_id:
        raise HTTPException(status_code=400, detail="run_id is required")

    task_id = f"task_{uuid.uuid4().hex[:16]}"
    now = utc_now()

    merged_payload = {
        **(body.payload_json or {}),
        **(body.payload or {}),
    }

    if body.operator_message and "operator_message" not in merged_payload:
        merged_payload["operator_message"] = body.operator_message

    input_payload = {
        **(body.input_payload or {}),
        "project_key": body.project_key,
    }

    execute(
        """
        INSERT INTO tasks (
            task_id,
            run_id,
            project_key,
            general_key,
            task_type,
            title,
            operator_message,
            payload_json,
            input_payload,
            output_payload,
            error_payload,
            status,
            result_json,
            error_text,
            artifact_path,
            artifact_json,
            created_at,
            updated_at,
            lease_owner,
            lease_expires_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            task_id,
            body.run_id,
            body.project_key,
            body.general_key,
            body.task_type,
            body.title,
            body.operator_message,
            _serialize(merged_payload, {}),
            _serialize(input_payload, {}),
            "{}",
            "{}",
            "queued",
            None,
            None,
            None,
            None,
            now,
            now,
            None,
            None,
        ],
    )

    row = fetch_one("SELECT * FROM tasks WHERE task_id = ?", [task_id])
    return {"ok": True, "task": _normalize_task_row(row)}


@router.post("/admin/tasks")
def create_task_admin(body: TaskCreate):
    return create_task(body)


@router.post("/admin/tasks/{task_id}/requeue")
def requeue_task(task_id: str):
    ensure_tasks_ready()

    existing = fetch_one("SELECT task_id FROM tasks WHERE task_id = ?", [task_id])
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    execute(
        """
        UPDATE tasks
        SET
            status = ?,
            error_text = NULL,
            result_json = NULL,
            artifact_path = NULL,
            artifact_json = NULL,
            output_payload = '{}',
            error_payload = '{}',
            updated_at = ?,
            lease_owner = NULL,
            lease_expires_at = NULL
        WHERE task_id = ?
        """,
        ["queued", utc_now(), task_id],
    )

    row = fetch_one("SELECT * FROM tasks WHERE task_id = ?", [task_id])
    return {"ok": True, "task": _normalize_task_row(row)}


@router.delete("/admin/tasks/{task_id}")
def delete_task(task_id: str):
    ensure_tasks_ready()

    existing = fetch_one("SELECT task_id FROM tasks WHERE task_id = ?", [task_id])
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    execute("DELETE FROM tasks WHERE task_id = ?", [task_id])
    return {"ok": True, "deleted": task_id}