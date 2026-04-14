from datetime import datetime, timezone

from f22_core_db import execute, fetch_all, fetch_one, init_db

init_db()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_tasks(run_id: str | None = None, project_key: str | None = None, status: str | None = None):
    if project_key:
        sql = """
            SELECT
                t.task_id,
                t.run_id,
                t.task_type,
                t.assigned_agent,
                t.title,
                t.status,
                t.priority,
                t.attempt_count,
                t.input_payload,
                t.output_payload,
                t.error_payload,
                t.lease_expires_at,
                t.created_at,
                t.updated_at
            FROM tasks t
            JOIN runs r ON r.run_id = t.run_id
            WHERE r.project_key = ?
        """
        params: list[object] = [project_key]

        if run_id:
            sql += " AND t.run_id = ?"
            params.append(run_id)

        if status:
            sql += " AND t.status = ?"
            params.append(status)

        sql += " ORDER BY t.created_at DESC"
        return fetch_all(sql, params)

    sql = """
        SELECT
            task_id,
            run_id,
            task_type,
            assigned_agent,
            title,
            status,
            priority,
            attempt_count,
            input_payload,
            output_payload,
            error_payload,
            lease_expires_at,
            created_at,
            updated_at
        FROM tasks
        WHERE 1=1
    """
    params: list[object] = []

    if run_id:
        sql += " AND run_id = ?"
        params.append(run_id)

    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += " ORDER BY created_at DESC"
    return fetch_all(sql, params)


def get_task(task_id: str):
    return fetch_one(
        """
        SELECT
            task_id,
            run_id,
            task_type,
            assigned_agent,
            title,
            status,
            priority,
            attempt_count,
            input_payload,
            output_payload,
            error_payload,
            lease_expires_at,
            created_at,
            updated_at
        FROM tasks
        WHERE task_id = ?
        """,
        [task_id],
    )


def delete_task(task_id: str) -> int:
    return execute("DELETE FROM tasks WHERE task_id = ?", [task_id])


def requeue_task(task_id: str) -> int:
    return execute(
        """
        UPDATE tasks
        SET
            status = 'queued',
            lease_expires_at = NULL,
            error_payload = '{}',
            updated_at = ?
        WHERE task_id = ?
        """,
        [utc_now_iso(), task_id],
    )


# alias helpers for old code
fetch_task = get_task
fetch_task_by_id = get_task
list_tasks_for_run = list_tasks
delete_task_by_id = delete_task
requeue_task_by_id = requeue_task