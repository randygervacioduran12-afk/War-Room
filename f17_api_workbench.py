from __future__ import annotations

import asyncio
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/workbench", tags=["workbench"])

WORKSPACE_ROOT = Path("/home/runner/workspace").resolve()

ALLOWED_COMMAND_PREFIXES = [
    "python -m py_compile ",
    "python ",
    "pytest",
    "ls",
    "pwd",
    "cat ",
    "grep ",
    "find ",
]

HIDDEN_PREFIXES = [
    ".pythonlibs",
    ".cache",
    ".git",
    "__pycache__",
    ".config",
    ".upm",
    ".local",
]

HIDDEN_SUFFIXES = [
    ".pyc",
    ".db",
    ".sqlite",
    ".sqlite3",
]


class FileWriteRequest(BaseModel):
    path: str
    content: str


class CommandRequest(BaseModel):
    command: str


def resolve_safe_path(user_path: str) -> Path:
    clean = (WORKSPACE_ROOT / user_path).resolve()
    if not str(clean).startswith(str(WORKSPACE_ROOT)):
        raise HTTPException(status_code=400, detail="Path escapes workspace")
    return clean


def should_hide_path(rel_path: str) -> bool:
    parts = rel_path.split("/")
    if any(part in HIDDEN_PREFIXES for part in parts):
        return True
    if any(rel_path.endswith(suffix) for suffix in HIDDEN_SUFFIXES):
        return True
    return False


@router.get("/status")
async def workbench_status() -> dict:
    return {
        "ok": True,
        "workspace_root": str(WORKSPACE_ROOT),
        "allowed_commands": ALLOWED_COMMAND_PREFIXES,
    }


@router.get("/files")
async def list_files(
    prefix: str = Query(default="", description="Optional relative folder prefix"),
    limit: int = Query(default=200, ge=1, le=1000),
) -> dict:
    base = resolve_safe_path(prefix or ".")
    if not base.exists():
        raise HTTPException(status_code=404, detail="Folder not found")
    if not base.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a folder")

    files: list[dict] = []
    for path in sorted(base.rglob("*")):
        rel = str(path.relative_to(WORKSPACE_ROOT))
        if should_hide_path(rel):
            continue
        if path.is_file():
            files.append(
                {
                    "path": rel,
                    "size": path.stat().st_size,
                    "modified_at": path.stat().st_mtime,
                }
            )
        if len(files) >= limit:
            break

    return {"items": files}


@router.get("/file")
async def read_file(path: str) -> dict:
    file_path = resolve_safe_path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not utf-8 text")

    return {
        "path": str(file_path.relative_to(WORKSPACE_ROOT)),
        "content": content,
    }


@router.post("/file")
async def write_file(payload: FileWriteRequest) -> dict:
    file_path = resolve_safe_path(payload.path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(payload.content, encoding="utf-8")
    return {
        "ok": True,
        "path": str(file_path.relative_to(WORKSPACE_ROOT)),
        "bytes_written": len(payload.content.encode("utf-8")),
    }


@router.delete("/file")
async def delete_file(path: str) -> dict:
    file_path = resolve_safe_path(path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    file_path.unlink()
    return {"ok": True, "deleted": str(file_path.relative_to(WORKSPACE_ROOT))}


def command_is_allowed(command: str) -> bool:
    stripped = command.strip()
    return any(
        stripped == prefix.strip() or stripped.startswith(prefix)
        for prefix in ALLOWED_COMMAND_PREFIXES
    )


@router.post("/command")
async def run_command(payload: CommandRequest) -> dict:
    command = payload.command.strip()

    if not command:
        raise HTTPException(status_code=400, detail="Command is empty")

    if not command_is_allowed(command):
        raise HTTPException(status_code=400, detail="Command not allowed")

    process = await asyncio.create_subprocess_shell(
        command,
        cwd=str(WORKSPACE_ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=os.environ.copy(),
    )
    stdout, stderr = await process.communicate()

    return {
        "ok": process.returncode == 0,
        "command": command,
        "returncode": process.returncode,
        "stdout": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
    }