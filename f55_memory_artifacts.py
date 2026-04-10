from f22_core_db import execute, j
from f25_core_types import ArtifactKind
from f26_core_utils import new_id


async def create_artifact(
    *,
    run_id: str,
    project_key: str,
    artifact_kind: ArtifactKind,
    title: str,
    body: str,
    task_id: str | None = None,
    metadata: dict | None = None,
) -> str:
    artifact_id = new_id("art")
    await execute(
        """
        INSERT INTO artifacts (
            artifact_id, run_id, task_id, project_key, artifact_kind, title, body, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
        """,
        artifact_id,
        run_id,
        task_id,
        project_key,
        artifact_kind.value,
        title,
        body,
        j(metadata or {}),
    )
    return artifact_id