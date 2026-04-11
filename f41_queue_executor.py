import asyncio
import json
import os
import re
import socket
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from f22_core_db import execute, fetch_one, init_db, update_fields
from f35_general_router import run_general_task

try:
    from f21_core_logging import get_logger, setup_logging
except Exception:
    import logging

    def setup_logging() -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )

    def get_logger(name: str):
        return logging.getLogger(name)


POLL_SECONDS = int(os.getenv("EXECUTOR_POLL_SECONDS", "2"))
LEASE_SECONDS = int(os.getenv("EXECUTOR_LEASE_SECONDS", "180"))
EXECUTOR_OWNER = os.getenv(
    "EXECUTOR_OWNER",
    f"{socket.gethostname()}:{os.getpid()}",
)

ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "artifacts")).resolve()

logger = get_logger("queue.executor")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def lease_until() -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=LEASE_SECONDS)).isoformat()


def _safe_json_loads(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return value


def _json_text(value: Any, fallback: Any = None) -> str:
    if value is None:
        value = fallback if fallback is not None else {}
    if isinstance(value, str):
        text = value.strip()
        if text:
            return text
        return json.dumps(fallback if fallback is not None else {}, ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False)


def _slug(value: str, fallback: str = "artifact") -> str:
    text = (value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or fallback


def _claim_next_task() -> dict[str, Any] | None:
    init_db()
    now = utc_now()

    row = fetch_one(
        """
        SELECT *
        FROM tasks
        WHERE
            status = 'queued'
            OR (status = 'claimed' AND lease_expires_at IS NOT NULL AND lease_expires_at < ?)
        ORDER BY created_at ASC
        LIMIT 1
        """,
        [now],
    )

    if not row:
        return None

    updated = execute(
        """
        UPDATE tasks
        SET
            status = 'claimed',
            lease_owner = ?,
            lease_expires_at = ?,
            updated_at = ?,
            attempt_count = COALESCE(attempt_count, 0) + 1
        WHERE task_id = ?
          AND (
            status = 'queued'
            OR (status = 'claimed' AND lease_expires_at IS NOT NULL AND lease_expires_at < ?)
          )
        """,
        [
            EXECUTOR_OWNER,
            lease_until(),
            now,
            row["task_id"],
            now,
        ],
    )

    if not updated:
        return None

    return fetch_one("SELECT * FROM tasks WHERE task_id = ?", [row["task_id"]])


def _normalize_task(task: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(task)

    for key in (
        "payload_json",
        "result_json",
        "artifact_json",
        "input_payload",
        "output_payload",
        "error_payload",
    ):
        normalized[key] = _safe_json_loads(normalized.get(key))

    if not normalized.get("operator_message"):
        payload = normalized.get("payload_json")
        if isinstance(payload, dict):
            normalized["operator_message"] = payload.get("operator_message", "")

    return normalized


def _artifact_extension(kind: str) -> str:
    lowered = (kind or "").lower()
    if lowered in {"json", "json_blob"}:
        return ".json"
    if lowered in {"code", "code_patch", "patch"}:
        return ".md"
    return ".md"


def _artifact_body_and_kind(task: dict[str, Any], result: dict[str, Any]) -> tuple[str, str, str]:
    raw_artifact = result.get("artifact")
    title = (
        (raw_artifact.get("title") if isinstance(raw_artifact, dict) else None)
        or task.get("title")
        or f"{task.get('general_key') or 'agent'} output"
    )
    kind = (
        (raw_artifact.get("type") if isinstance(raw_artifact, dict) else None)
        or "markdown"
    )

    if isinstance(raw_artifact, dict):
        body = raw_artifact.get("content") or raw_artifact.get("body")
        if body is None:
            body = json.dumps(raw_artifact, ensure_ascii=False, indent=2)
    elif isinstance(raw_artifact, str):
        body = raw_artifact
    else:
        body = result.get("raw_text") or result.get("summary")
        if not body:
            body = json.dumps(result, ensure_ascii=False, indent=2)

    return str(title), str(kind), str(body)


def _write_artifact_file(task: dict[str, Any], title: str, kind: str, body: str) -> tuple[str, str]:
    project_key = task.get("project_key") or "default-project"
    run_id = task.get("run_id") or "no-run"
    task_id = task.get("task_id") or f"task_{uuid4().hex[:8]}"

    folder = ARTIFACTS_DIR / _slug(project_key, "project") / _slug(run_id, "run")
    folder.mkdir(parents=True, exist_ok=True)

    ext = _artifact_extension(kind)
    filename = f"{task_id}-{_slug(title)}{ext}"
    file_path = folder / filename

    file_path.write_text(body, encoding="utf-8")

    relative_path = str(file_path.relative_to(Path.cwd())).replace("\\", "/")
    href = f"/assets/{relative_path}"
    return relative_path, href


def _build_artifact_payload(task: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    title, kind, body = _artifact_body_and_kind(task, result)
    relative_path, href = _write_artifact_file(task, title, kind, body)

    return {
        "type": kind,
        "title": title,
        "body": body,
        "path": relative_path,
        "href": href,
        "task_id": task.get("task_id"),
        "run_id": task.get("run_id"),
        "project_key": task.get("project_key"),
        "general_key": task.get("general_key"),
        "created_at": utc_now(),
    }


def _persist_memory(
    *,
    task: dict[str, Any],
    memory_type: str,
    title: str,
    body: str,
    source_task_id: str | None = None,
) -> None:
    project_key = task.get("project_key") or "demo-project"
    run_id = task.get("run_id")
    memory_id = f"mem_{uuid4().hex[:16]}"

    execute(
        """
        INSERT INTO memory_items (
            memory_id,
            project_key,
            run_id,
            memory_type,
            title,
            body,
            source_task_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            memory_id,
            project_key,
            run_id,
            memory_type,
            title,
            body,
            source_task_id,
            utc_now(),
        ],
    )


def _mark_completed(task: dict[str, Any], result: dict[str, Any]) -> None:
    artifact_payload = _build_artifact_payload(task, result)

    result_json = _json_text(result, {})
    artifact_json = _json_text(artifact_payload, {})
    output_payload = _json_text(result, {})
    error_payload = "{}"

    update_fields(
        "tasks",
        {
            "status": "completed",
            "result_json": result_json,
            "artifact_json": artifact_json,
            "artifact_path": artifact_payload.get("path"),
            "error_text": None,
            "updated_at": utc_now(),
            "lease_owner": None,
            "lease_expires_at": None,
            "assigned_agent": task.get("general_key"),
            "output_payload": output_payload,
            "error_payload": error_payload,
        },
        "task_id = ?",
        [task["task_id"]],
    )

    _persist_memory(
        task=task,
        memory_type="summary",
        title=artifact_payload.get("title") or task.get("title") or "Completed task",
        body=artifact_payload.get("body") or result.get("summary") or "Task completed.",
        source_task_id=task.get("task_id"),
    )


def _mark_failed(task: dict[str, Any], exc: Exception) -> None:
    payload = {"error": str(exc)}

    update_fields(
        "tasks",
        {
            "status": "failed",
            "result_json": "{}",
            "artifact_json": "{}",
            "artifact_path": None,
            "error_text": str(exc),
            "updated_at": utc_now(),
            "lease_owner": None,
            "lease_expires_at": None,
            "output_payload": "{}",
            "error_payload": _json_text(payload, {"error": "unknown"}),
        },
        "task_id = ?",
        [task["task_id"]],
    )

    _persist_memory(
        task=task,
        memory_type="failure",
        title=f"Failure: {task.get('title') or task.get('task_id') or 'task'}",
        body=str(exc),
        source_task_id=task.get("task_id"),
    )


async def _run_task(task: dict[str, Any]) -> dict[str, Any]:
    return await asyncio.to_thread(run_general_task, task)


async def run_executor_loop() -> None:
    setup_logging()
    init_db()
    logger.info("executor loop started owner=%s", EXECUTOR_OWNER)

    while True:
        task = _claim_next_task()

        if not task:
            await asyncio.sleep(POLL_SECONDS)
            continue

        task = _normalize_task(task)
        logger.info(
            "claimed task task_id=%s general=%s type=%s title=%s",
            task.get("task_id"),
            task.get("general_key"),
            task.get("task_type"),
            task.get("title"),
        )

        try:
            result = await _run_task(task)
            _mark_completed(task, result)
            logger.info("completed task task_id=%s", task.get("task_id"))
        except Exception as exc:
            _mark_failed(task, exc)
            logger.exception("failed task task_id=%s", task.get("task_id"))

        await asyncio.sleep(0.1)