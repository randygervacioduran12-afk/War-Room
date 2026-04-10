from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from f22_core_db import execute, fetch_all, fetch_one
from f21_core_logging import get_logger

router = APIRouter()
logger = get_logger("api.runs")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CreateRunRequest(BaseModel):
    project_key: str
    adapter_key: str
    goal: str


@router.get("/runs")
def list_runs(project_key: str | None = None):
    if project_key:
        rows = fetch_all(
            """
            SELECT run_id, project_key, adapter_key, goal, status,
                   input_payload, output_payload, created_at, updated_at
            FROM runs
            WHERE project_key = ?
            ORDER BY created_at DESC
            """,
            [project_key],
        )
    else:
        rows = fetch_all(
            """
            SELECT run_id, project_key, adapter_key, goal, status,
                   input_payload, output_payload, created_at, updated_at
            FROM runs
            ORDER BY created_at DESC
            """
        )

    return {"runs": rows}


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    row = fetch_one(
        """
        SELECT run_id, project_key, adapter_key, goal, status,
               input_payload, output_payload, created_at, updated_at
        FROM runs
        WHERE run_id = ?
        """,
        [run_id],
    )
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    return row


@router.post("/runs")
def create_run(payload: CreateRunRequest):
    run_id = f"run_{uuid4().hex[:16]}"
    now = utc_now_iso()

    execute(
        """
        INSERT INTO runs (
            run_id,
            project_key,
            adapter_key,
            goal,
            status,
            input_payload,
            output_payload,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            run_id,
            payload.project_key,
            payload.adapter_key,
            payload.goal,
            "created",
            "{}",
            "{}",
            now,
            now,
        ],
    )

    logger.info("created run %s", run_id)

    return {
        "run_id": run_id,
        "project_key": payload.project_key,
        "adapter_key": payload.adapter_key,
        "goal": payload.goal,
        "status": "created",
        "input_payload": {},
        "output_payload": {},
        "created_at": now,
        "updated_at": now,
    }