import os
import json
from typing import Any, Dict, List, Optional

import asyncpg


_pool: Optional[asyncpg.Pool] = None


def _normalize_arg(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    return value


async def _get_pool() -> asyncpg.Pool:
    global _pool

    if _pool is not None:
        return _pool

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("Missing DATABASE_URL")

    _pool = await asyncpg.create_pool(
        dsn=database_url,
        min_size=1,
        max_size=5,
    )
    return _pool


async def fetch_one(query: str, *args: Any) -> Optional[Dict[str, Any]]:
    pool = await _get_pool()
    safe_args = tuple(_normalize_arg(arg) for arg in args)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *safe_args)
        if row is None:
            return None
        return dict(row)


async def fetch_all(query: str, *args: Any) -> List[Dict[str, Any]]:
    pool = await _get_pool()
    safe_args = tuple(_normalize_arg(arg) for arg in args)

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *safe_args)
        return [dict(row) for row in rows]


async def execute(query: str, *args: Any) -> str:
    pool = await _get_pool()
    safe_args = tuple(_normalize_arg(arg) for arg in args)

    async with pool.acquire() as conn:
        return await conn.execute(query, *safe_args)