from f22_core_db import execute, j
from f26_core_utils import new_id


async def record_task_event(task_id: str, run_id: str, event_type: str, payload: dict) -> None:
    await execute(
        """
        INSERT INTO task_events (event_id, task_id, run_id, event_type, payload)
        VALUES ($1, $2, $3, $4, $5::jsonb)
        """,
        new_id("evt"),
        task_id,
        run_id,
        event_type,
        j(payload),
    )