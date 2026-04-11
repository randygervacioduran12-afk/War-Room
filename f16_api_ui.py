from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

ROOT = Path(__file__).resolve().parent
SHELL_FILE = ROOT / "f60_ui_shell.html"


@router.get("/", response_class=HTMLResponse)
def ui_index() -> str:
    if not SHELL_FILE.exists():
        raise HTTPException(status_code=500, detail="UI shell file missing")
    return SHELL_FILE.read_text(encoding="utf-8")