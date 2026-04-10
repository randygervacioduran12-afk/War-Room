from fastapi import APIRouter, HTTPException

from f22_core_db import execute, fetch_one, j
from f25_core_types import TaskStatus

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/tasks/{task_id}/requeue")
async def requeue_task(task_id: str) -> dict:
    row = await fetch_one("SELECT * FROM tasks WHERE task_id = $1", task_id)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    await execute(
        """
        UPDATE tasks
        SET status = $2,
            lease_expires_at = NULL,
            error_payload = $3::jsonb,
            updated_at = now()
        WHERE task_id = $1
        """,
        task_id,
        TaskStatus.QUEUED.value,
        j({}),
    )
    return {"ok": True, "task_id": task_id, "status": TaskStatus.QUEUED.value}


@router.delete("/runs/{run_id}")
async def delete_run(run_id: str) -> dict:
    row = await fetch_one("SELECT run_id FROM runs WHERE run_id = $1", run_id)
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")

    await execute("DELETE FROM runs WHERE run_id = $1", run_id)
    return {"ok": True, "deleted_run_id": run_id}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str) -> dict:
    row = await fetch_one("SELECT task_id FROM tasks WHERE task_id = $1", task_id)
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    await execute("DELETE FROM tasks WHERE task_id = $1", task_id)
    return {"ok": True, "deleted_task_id": task_id}