from f22_core_db import fetch_all, fetch_one


async def build_morning_brief(run_id: str) -> dict:
    run_row = await fetch_one("SELECT * FROM runs WHERE run_id = $1", run_id)
    task_rows = await fetch_all(
        """
        SELECT task_id, title, assigned_agent, status, output_payload, error_payload
        FROM tasks
        WHERE run_id = $1
        ORDER BY priority ASC, created_at ASC
        """,
        run_id,
    )
    artifact_rows = await fetch_all(
        """
        SELECT artifact_id, artifact_kind, title, created_at
        FROM artifacts
        WHERE run_id = $1
        ORDER BY created_at DESC
        """,
        run_id,
    )

    completed = [dict(r) for r in task_rows if r["status"] == "completed"]
    failed = [dict(r) for r in task_rows if r["status"] == "failed"]

    return {
        "run": dict(run_row) if run_row else None,
        "summary": {
            "task_count": len(task_rows),
            "completed_count": len(completed),
            "failed_count": len(failed),
            "artifact_count": len(artifact_rows),
        },
        "completed_tasks": completed,
        "failed_tasks": failed,
        "artifacts": [dict(r) for r in artifact_rows],
    }