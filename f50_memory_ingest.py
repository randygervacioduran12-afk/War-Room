from f22_core_db import execute, j
from f25_core_types import MemoryKind, MemoryScope
from f26_core_utils import new_id


async def write_memory(
    *,
    project_key: str,
    title: str,
    content: str,
    kind: MemoryKind = MemoryKind.NOTE,
    scope: MemoryScope = MemoryScope.PROJECT,
    run_id: str | None = None,
    metadata: dict | None = None,
) -> str:
    memory_id = new_id("mem")
    await execute(
        """
        INSERT INTO memory_entries (
            memory_id, run_id, project_key, scope, kind, title, content, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
        """,
        memory_id,
        run_id,
        project_key,
        scope.value,
        kind.value,
        title,
        content,
        j(metadata or {}),
    )
    return memory_id