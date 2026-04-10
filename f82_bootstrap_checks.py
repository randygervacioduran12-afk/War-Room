import asyncio
import os

from f21_core_logging import get_logger, setup_logging
from f22_core_db import fetch_all, fetch_one, init_db

logger = get_logger("bootstrap_checks")

EXPECTED_TABLES = {
    "runs",
    "tasks",
    "task_events",
    "memory_entries",
    "artifacts",
}


async def run_checks() -> None:
    setup_logging()
    await init_db()

    row = await fetch_one("SELECT 1 AS ok")
    if not row or row["ok"] != 1:
        raise RuntimeError("Database ping failed")

    tables = await fetch_all(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """
    )
    found = {r["table_name"] for r in tables}
    missing = EXPECTED_TABLES - found
    if missing:
        raise RuntimeError(f"Missing tables: {sorted(missing)}")

    logger.info(
        "checks_complete",
        has_database_url=bool(os.getenv("DATABASE_URL")),
        has_anthropic_api_key=bool(os.getenv("ANTHROPIC_API_KEY")),
        tables=sorted(found),
    )


if __name__ == "__main__":
    asyncio.run(run_checks())