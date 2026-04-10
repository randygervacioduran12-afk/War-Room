import asyncio

from f21_core_logging import get_logger, setup_logging

logger = get_logger("seed")


async def seed() -> None:
    setup_logging()
    logger.info("seed_complete", message="No default seed data required yet.")


if __name__ == "__main__":
    asyncio.run(seed())