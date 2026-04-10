import logging
import os
from typing import Optional


def setup_logging(level: Optional[str] = None) -> None:
    log_level = (level or os.getenv("LOG_LEVEL") or "INFO").upper()

    root = logging.getLogger()
    if root.handlers:
        root.setLevel(log_level)
        return

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)