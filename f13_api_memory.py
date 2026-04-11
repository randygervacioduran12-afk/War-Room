from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from f22_core_db import execute, fetch_all, fetch_one, init_db

router = APIRouter()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_memory_ready() -> None:
    init_db()


class MemoryCreateRequest(BaseModel):
    project_key: str
    title: str
    body: str
    run_id: str | None = None
    memory_type: str = "note"
    source_task_id: str | None = None


@router.get("/memory")
def list_memory(project_key: str = Query(...)):
    ensure_memory_ready()

    rows = fetch_all(
        """
        SELECT
            memory_id,
            project_key,
            run_id,
            memory_type,
            title,
            body,
            source_task_id,
            created_at
        FROM memory_items
        WHERE project_key = ?
        ORDER BY created_at DESC
        """,
        [project_key],
    )
    return {"items": rows}


@router.get("/memory/{memory_id}")
def get_memory(memory_id: str):
    ensure_memory_ready()

    row = fetch_one(
        """
        SELECT
            memory_id,
            project_key,
            run_id,
            memory_type,
            title,
            body,
            source_task_id,
            created_at
        FROM memory_items
        WHERE memory_id = ?
        """,
        [memory_id],
    )
    if not row:
        raise HTTPException(status_code=404, detail="Memory not found")
    return row


@router.post("/memory")
def create_memory(payload: MemoryCreateRequest):
    ensure_memory_ready()

    memory_id = f"mem_{uuid4().hex[:16]}"
    created_at = utc_now()

    execute(
        """
        INSERT INTO memory_items (
            memory_id,
            project_key,
            run_id,
            memory_type,
            title,
            body,
            source_task_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            memory_id,
            payload.project_key,
            payload.run_id,
            payload.memory_type,
            payload.title,
            payload.body,
            payload.source_task_id,
            created_at,
        ],
    )

    row = fetch_one(
        """
        SELECT
            memory_id,
            project_key,
            run_id,
            memory_type,
            title,
            body,
            source_task_id,
            created_at
        FROM memory_items
        WHERE memory_id = ?
        """,
        [memory_id],
    )
    return {"ok": True, "item": row}


@router.delete("/admin/memory/{memory_id}")
def delete_memory(memory_id: str):
    ensure_memory_ready()

    row = fetch_one(
        """
        SELECT memory_id
        FROM memory_items
        WHERE memory_id = ?
        """,
        [memory_id],
    )
    if not row:
        raise HTTPException(status_code=404, detail="Memory not found")

    execute(
        """
        DELETE FROM memory_items
        WHERE memory_id = ?
        """,
        [memory_id],
    )
    return {"ok": True, "deleted": memory_id}