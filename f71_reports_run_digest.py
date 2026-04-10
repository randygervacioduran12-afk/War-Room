from f22_core_db import fetch_all


async def build_run_digest(run_id: str) -> dict:
    rows = await fetch_all(
        """
        SELECT task_id, title, status, assigned_agent, updated_at
        FROM tasks
        WHERE run_id = $1
        ORDER BY updated_at DESC
        """,
        run_id,
    )
    return {"run_id": run_id, "tasks": [dict(r) for r in rows]}