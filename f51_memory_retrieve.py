from f22_core_db import fetch_all
from f26_core_utils import ensure_dict
from f54_memory_scope import build_memory_scope_list


async def get_relevant_memory(project_key: str, run_id: str | None = None, limit: int = 20) -> list[dict]:
    scopes = build_memory_scope_list(run_id, project_key)

    items: list[dict] = []

    for scope, scoped_run_id in scopes:
        rows = await fetch_all(
            """
            SELECT * FROM memory_entries
            WHERE project_key = $1
              AND scope = $2
              AND ($3::text IS NULL OR run_id = $3)
            ORDER BY created_at DESC
            LIMIT $4
            """,
            project_key,
            scope,
            scoped_run_id,
            limit,
        )

        for row in rows:
            item = dict(row)
            item["metadata"] = ensure_dict(item.get("metadata"), {})
            items.append(item)

    return items[:limit]