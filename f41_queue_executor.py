import asyncio
import json
import os
import socket
from datetime import datetime, timedelta, timezone
from typing import Any

from f22_core_db import fetch_one, execute, init_db, update_fields
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


def _mark_completed(task: dict[str, Any], result: dict[str, Any]) -> None:
    artifact = result.get("artifact") or {}

    result_json = _json_text(result, {})
    artifact_json = _json_text(artifact, {})
    output_payload = _json_text(result, {})
    error_payload = "{}"

    update_fields(
        "tasks",
        {
            "status": "completed",
            "result_json": result_json,
            "artifact_json": artifact_json,
            "artifact_path": artifact.get("path") if isinstance(artifact, dict) else None,
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