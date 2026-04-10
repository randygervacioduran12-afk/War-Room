from typing import Dict, Optional

from f24_db import execute, fetch_one


LEASE_MINUTES = 15


async def claim_next_task() -> Optional[Dict]:
    row = await fetch_one(
        """
        UPDATE tasks
        SET
            status = 'claimed',
            attempt_count = COALESCE(attempt_count, 0) + 1,
            lease_expires_at = (NOW() AT TIME ZONE 'utc') + INTERVAL '15 minutes',
            updated_at = NOW() AT TIME ZONE 'utc'
        WHERE task_id = (
            SELECT task_id
            FROM tasks
            WHERE status IN ('queued', 'retry')
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING
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
        """
    )
    return dict(row) if row else None


async def expire_stale_claimed_tasks() -> None:
    await execute(
        """
        UPDATE tasks
        SET
            status = 'retry',
            lease_expires_at = NULL,
            updated_at = NOW() AT TIME ZONE 'utc'
        WHERE status = 'claimed'
          AND lease_expires_at IS NOT NULL
          AND lease_expires_at < (NOW() AT TIME ZONE 'utc')
        """
    )