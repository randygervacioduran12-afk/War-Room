import asyncio
from typing import Optional

from f21_core_logging import get_logger, setup_logging
from f22_core_db import init_db

logger = get_logger(__name__)
POLL_SECONDS = 5


async def run_scheduler_loop() -> None:
    setup_logging()
    init_db()

    logger.info("scheduler loop started")

    while True:
        try:
            # Scheduler placeholder.
            # Add queue creation / orchestration logic here later.
            await asyncio.sleep(POLL_SECONDS)
        except Exception as exc:
            logger.exception("scheduler loop error: %s", exc)
            await asyncio.sleep(POLL_SECONDS)