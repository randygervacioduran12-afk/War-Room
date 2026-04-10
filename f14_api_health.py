import os
from datetime import datetime, timezone

from fastapi import APIRouter

from f22_core_db import fetch_one, init_db

router = APIRouter(tags=["health"])


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/health")
def health() -> dict:
    db_ok = False
    db_error = None

    try:
        init_db()
        row = fetch_one("SELECT 1 AS ok")
        db_ok = bool(row and row.get("ok") == 1)
    except Exception as exc:
        db_ok = False
        db_error = str(exc)

    anthropic_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    gemini_key = bool(os.getenv("GEMINI_API_KEY"))
    llm_ok = anthropic_key or gemini_key

    provider = None
    if anthropic_key:
        provider = "anthropic"
    elif gemini_key:
        provider = "gemini"

    return {
        "ok": db_ok and llm_ok,
        "app_env": os.getenv("APP_ENV", "dev"),
        "db_ok": db_ok,
        "llm_ok": llm_ok,
        "provider": provider,
        "timestamp": _utc_now(),
        "db_error": db_error,
    }