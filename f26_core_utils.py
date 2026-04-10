import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import orjson


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def safe_json_dumps(value: Any) -> str:
    return orjson.dumps(value).decode("utf-8")


def safe_json_loads(value: str | bytes | None, default: Any = None) -> Any:
    if value in (None, "", b""):
        return default
    try:
        return orjson.loads(value)
    except Exception:
        return default


def ensure_dict(value: Any, default: dict | None = None) -> dict:
    fallback = default or {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        loaded = safe_json_loads(value, fallback)
        return loaded if isinstance(loaded, dict) else fallback
    if isinstance(value, bytes):
        loaded = safe_json_loads(value, fallback)
        return loaded if isinstance(loaded, dict) else fallback
    return fallback


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)
