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


class TaskCreate(BaseModel):
    run_id: Optional[str] = None
    project_key: str = "demo-project"
    general_key: str = "general_of_the_army"
    task_type: str = "manual"
    title: str = "Manual mission dispatch"
    operator_message: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


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
            title,
            operator_message,
            payload_json,
            status,
            result_json,
            error_text,
            artifact_path,
            artifact_json,
            created_at,
            updated_at,
            lease_owner,
            lease_expires_at
        FROM tasks
    """

    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)

    sql += " ORDER BY created_at DESC"

    rows = fetch_all(sql, params)

    for row in rows:
        for key in ("payload_json", "result_json", "artifact_json"):
            if row.get(key):
                try:
                    row[key] = json.loads(row[key])
                except Exception:
                    pass

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
            title,
            operator_message,
            payload_json,
            status,
            result_json,
            error_text,
            artifact_path,
            artifact_json,
            created_at,
            updated_at,
            lease_owner,
            lease_expires_at
        FROM tasks
        WHERE task_id = ?
        """,
        [task_id],
    )

    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    for key in ("payload_json", "result_json", "artifact_json"):
        if row.get(key):
            try:
                row[key] = json.loads(row[key])
            except Exception:
                pass

    return row


@router.post("/tasks")
def create_task(body: TaskCreate):
    ensure_tasks_ready()

    task_id = f"task_{uuid.uuid4().hex[:16]}"
    now = utc_now()

    payload = {
        "operator_message": body.operator_message,
        **(body.payload or {}),
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            task_id,
            body.run_id,
            body.project_key,
            body.general_key,
            body.task_type,
            body.title,
            body.operator_message,
            json.dumps(payload),
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
    return {"ok": True, "task": row}


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
            updated_at = ?,
            lease_owner = NULL,
            lease_expires_at = NULL
        WHERE task_id = ?
        """,
        ["queued", utc_now(), task_id],
    )

    row = fetch_one("SELECT * FROM tasks WHERE task_id = ?", [task_id])
    return {"ok": True, "task": row}


@router.delete("/admin/tasks/{task_id}")
def delete_task(task_id: str):
    ensure_tasks_ready()

    existing = fetch_one("SELECT task_id FROM tasks WHERE task_id = ?", [task_id])
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    execute("DELETE FROM tasks WHERE task_id = ?", [task_id])
    return {"ok": True, "deleted": task_id}