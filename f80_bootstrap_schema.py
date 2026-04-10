import asyncio

from f21_core_logging import get_logger, setup_logging
from f22_core_db import execute, init_db

logger = get_logger("bootstrap")


DDL = [
    """
    CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        project_key TEXT NOT NULL,
        adapter_key TEXT NOT NULL,
        goal TEXT NOT NULL,
        status TEXT NOT NULL,
        input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        output_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        task_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
        parent_task_id TEXT NULL REFERENCES tasks(task_id) ON DELETE SET NULL,
        task_type TEXT NOT NULL,
        assigned_agent TEXT NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL,
        priority INT NOT NULL DEFAULT 100,
        attempt_count INT NOT NULL DEFAULT 0,
        input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        output_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        error_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        lease_expires_at TIMESTAMPTZ NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS task_events (
        event_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
        run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
        event_type TEXT NOT NULL,
        payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS memory_entries (
        memory_id TEXT PRIMARY KEY,
        run_id TEXT NULL,
        project_key TEXT NOT NULL,
        scope TEXT NOT NULL,
        kind TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS artifacts (
        artifact_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE CASCADE,
        task_id TEXT NULL REFERENCES tasks(task_id) ON DELETE SET NULL,
        project_key TEXT NOT NULL,
        artifact_kind TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_runs_project_created
    ON runs(project_key, created_at DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tasks_run_status_priority
    ON tasks(run_id, status, priority, created_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tasks_status_lease
    ON tasks(status, lease_expires_at, priority, created_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_memory_project_scope_kind_created
    ON memory_entries(project_key, scope, kind, created_at DESC)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_artifacts_run_created
    ON artifacts(run_id, created_at DESC)
    """,
]


async def bootstrap() -> None:
    setup_logging()
    await init_db()

    for stmt in DDL:
        await execute(stmt)

    logger.info("bootstrap_complete", statements=len(DDL))


if __name__ == "__main__":
    asyncio.run(bootstrap())