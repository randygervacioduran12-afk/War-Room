from f22_core_db import fetch_all


async def build_failure_digest(run_id: str) -> dict:
    rows = await fetch_all(
        """
        SELECT task_id, title, assigned_agent, attempt_count, error_payload, updated_at
        FROM tasks
        WHERE run_id = $1 AND status = 'failed'
        ORDER BY updated_at DESC
        """,
        run_id,
    )

    return {
        "run_id": run_id,
        "failed_count": len(rows),
        "failures": [dict(row) for row in rows],
    }