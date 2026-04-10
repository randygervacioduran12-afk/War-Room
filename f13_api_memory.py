from fastapi import APIRouter, HTTPException, Query

from f22_core_db import execute, fetch_all, fetch_one

router = APIRouter()


@router.get("/memory")
def list_memory(project_key: str = Query(...)):
    rows = fetch_all(
        """
        SELECT *
        FROM memory
        WHERE project_key = ?
        ORDER BY rowid DESC
        """,
        [project_key],
    )
    return {"items": rows}


@router.get("/memory/{memory_id}")
def get_memory(memory_id: str):
    row = fetch_one(
        """
        SELECT *
        FROM memory
        WHERE memory_id = ?
        """,
        [memory_id],
    )
    if not row:
        raise HTTPException(status_code=404, detail="Memory not found")
    return row


@router.delete("/admin/memory/{memory_id}")
def delete_memory(memory_id: str):
    row = fetch_one(
        """
        SELECT memory_id
        FROM memory
        WHERE memory_id = ?
        """,
        [memory_id],
    )
    if not row:
        raise HTTPException(status_code=404, detail="Memory not found")

    execute(
        """
        DELETE FROM memory
        WHERE memory_id = ?
        """,
        [memory_id],
    )
    return {"ok": True, "deleted": memory_id}