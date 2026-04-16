import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional

DB_PATH = os.getenv("APP_DB_PATH", "war_room.db")


def j(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _db_file() -> Path:
    path = Path(DB_PATH)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_file()), check_same_thread=False)
    conn.row_factory = sqlite3.Row

    # Better behavior for API + worker sharing the same SQLite file.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _params(params: Optional[Iterable[Any]]) -> tuple[Any, ...]:
    if params is None:
        return ()
    return tuple(params)


def execute(query: str, params: Optional[Iterable[Any]] = None) -> int:
    conn = _connect()
    try:
        cur = conn.execute(query, _params(params))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def fetch_one(query: str, params: Optional[Iterable[Any]] = None) -> Optional[dict]:
    conn = _connect()
    try:
        cur = conn.execute(query, _params(params))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def fetch_all(query: str, params: Optional[Iterable[Any]] = None) -> list[dict]:
    conn = _connect()
    try:
        cur = conn.execute(query, _params(params))
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def scalar(query: str, params: Optional[Iterable[Any]] = None) -> Any:
    row = fetch_one(query, params)
    if not row:
        return None
    return next(iter(row.values()))


def table_columns(table_name: str) -> set[str]:
    rows = fetch_all(f"PRAGMA table_info({table_name})")
    return {row["name"] for row in rows}


def _ensure_column(table_name: str, column_name: str, column_type: str) -> None:
    cols = table_columns(table_name)
    if column_name not in cols:
        execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def update_fields(
    table_name: str,
    values: dict[str, Any],
    where_sql: str,
    where_params: Optional[Iterable[Any]] = None,
) -> int:
    if not values:
        return 0
    cols = table_columns(table_name)
    filtered = {k: v for k, v in values.items() if k in cols}
    if not filtered:
        return 0

    set_sql = ", ".join(f"{k} = ?" for k in filtered.keys())
    params = list(filtered.values()) + list(_params(where_params))
    sql = f"UPDATE {table_name} SET {set_sql} WHERE {where_sql}"
    return execute(sql, params)


def init_db() -> None:
    execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            project_key TEXT,
            adapter_key TEXT,
            goal TEXT,
            status TEXT,
            input_payload TEXT,
            output_payload TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            run_id TEXT,
            project_key TEXT,
            general_key TEXT,
            task_type TEXT,
            title TEXT,
            operator_message TEXT,
            payload_json TEXT,
            status TEXT,
            result_json TEXT,
            error_text TEXT,
            artifact_path TEXT,
            artifact_json TEXT,
            created_at TEXT,
            updated_at TEXT,
            lease_owner TEXT,
            lease_expires_at TEXT,
            assigned_agent TEXT,
            priority INTEGER DEFAULT 0,
            attempt_count INTEGER DEFAULT 0,
            input_payload TEXT,
            output_payload TEXT,
            error_payload TEXT
        )
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS memory_items (
            memory_id TEXT PRIMARY KEY,
            project_key TEXT,
            run_id TEXT,
            memory_type TEXT,
            title TEXT,
            body TEXT,
            source_task_id TEXT,
            created_at TEXT
        )
        """
    )

    execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            note_id TEXT PRIMARY KEY,
            project_key TEXT,
            title TEXT,
            body TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """
    )

    for name, typ in [
        ("project_key", "TEXT"),
        ("adapter_key", "TEXT"),
        ("goal", "TEXT"),
        ("status", "TEXT"),
        ("input_payload", "TEXT"),
        ("output_payload", "TEXT"),
        ("created_at", "TEXT"),
        ("updated_at", "TEXT"),
    ]:
        _ensure_column("runs", name, typ)

    for name, typ in [
        ("run_id", "TEXT"),
        ("project_key", "TEXT"),
        ("general_key", "TEXT"),
        ("task_type", "TEXT"),
        ("title", "TEXT"),
        ("operator_message", "TEXT"),
        ("payload_json", "TEXT"),
        ("status", "TEXT"),
        ("result_json", "TEXT"),
        ("error_text", "TEXT"),
        ("artifact_path", "TEXT"),
        ("artifact_json", "TEXT"),
        ("created_at", "TEXT"),
        ("updated_at", "TEXT"),
        ("lease_owner", "TEXT"),
        ("lease_expires_at", "TEXT"),
        ("assigned_agent", "TEXT"),
        ("priority", "INTEGER DEFAULT 0"),
        ("attempt_count", "INTEGER DEFAULT 0"),
        ("input_payload", "TEXT"),
        ("output_payload", "TEXT"),
        ("error_payload", "TEXT"),
    ]:
        _ensure_column("tasks", name, typ)

    for name, typ in [
        ("project_key", "TEXT"),
        ("run_id", "TEXT"),
        ("memory_type", "TEXT"),
        ("title", "TEXT"),
        ("body", "TEXT"),
        ("source_task_id", "TEXT"),
        ("created_at", "TEXT"),
    ]:
        _ensure_column("memory_items", name, typ)

    for name, typ in [
        ("project_key", "TEXT"),
        ("title", "TEXT"),
        ("body", "TEXT"),
        ("created_at", "TEXT"),
        ("updated_at", "TEXT"),
    ]:
        _ensure_column("notes", name, typ)


init_db()