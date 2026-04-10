import json
from typing import Any, Dict

from f24_db import execute


def _json_text(payload: Dict[str, Any]) -> str:
    return json.dumps(payload or {}, default=str)


async def mark_task_completed(task_id: str, output_payload: Dict[str, Any]) -> None:
    await execute(
        """
        UPDATE tasks
        SET
            status = 'completed',
            output_payload = $2::jsonb,
            error_payload = '{}'::jsonb,
            lease_expires_at = NULL,
            updated_at = NOW() AT TIME ZONE 'utc'
        WHERE task_id = $1
        """,
        task_id,
        _json_text(output_payload),
    )


async def mark_task_failed(task_id: str, error_payload: Dict[str, Any]) -> None:
    await execute(
        """
        UPDATE tasks
        SET
            status = 'failed',
            error_payload = $2::jsonb,
            lease_expires_at = NULL,
            updated_at = NOW() AT TIME ZONE 'utc'
        WHERE task_id = $1
        """,
        task_id,
        _json_text(error_payload),
    )


async def mark_task_retry(task_id: str, error_payload: Dict[str, Any]) -> None:
    await execute(
        """
        UPDATE tasks
        SET
            status = 'retry',
            error_payload = $2::jsonb,
            lease_expires_at = NULL,
            updated_at = NOW() AT TIME ZONE 'utc'
        WHERE task_id = $1
        """,
        task_id,
        _json_text(error_payload),
    )