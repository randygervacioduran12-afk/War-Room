from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from f20_core_config import get_settings
from f11_api_runs import router as runs_router
from f12_api_tasks import router as tasks_router
from f13_api_memory import router as memory_router
from f14_api_health import router as health_router
from f16_api_ui import router as ui_router
from f17_api_workbench import router as workbench_router

settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", BASE_DIR / "artifacts")).resolve()
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


@asynccontextmanager
async def lifespan(_: FastAPI):
    background_tasks: list[asyncio.Task] = []

    # Replit is only launching the API process.
    # Embed the executor here so tasks actually complete in the same app.
    if _env_flag("EMBED_EXECUTOR", "true"):
        from f41_queue_executor import run_executor_loop

        background_tasks.append(
            asyncio.create_task(run_executor_loop(), name="warroom-executor")
        )

    # Optional scheduler for later. Leave off by default.
    if _env_flag("EMBED_SCHEDULER", "false"):
        from f40_queue_scheduler import run_scheduler_loop

        background_tasks.append(
            asyncio.create_task(run_scheduler_loop(), name="warroom-scheduler")
        )

    try:
        yield
    finally:
        for task in background_tasks:
            task.cancel()
        if background_tasks:
            await asyncio.gather(*background_tasks, return_exceptions=True)


app = FastAPI(
    title=getattr(settings, "app_name", "War Room"),
    version=getattr(settings, "app_version", "0.1.0"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Repo files
app.mount("/assets", StaticFiles(directory=str(BASE_DIR)), name="assets")
# Real generated artifact files
app.mount("/artifact-files", StaticFiles(directory=str(ARTIFACTS_DIR)), name="artifact-files")


@app.get("/f61_ui_styles.css", include_in_schema=False)
def ui_styles_redirect() -> RedirectResponse:
    return RedirectResponse(url="/assets/f61_ui_styles.css", status_code=307)


@app.get("/f62_ui_app.js", include_in_schema=False)
def ui_app_redirect() -> RedirectResponse:
    return RedirectResponse(url="/assets/f62_ui_app.js", status_code=307)


@app.get("/f63_ui_api.js", include_in_schema=False)
def ui_api_redirect() -> RedirectResponse:
    return RedirectResponse(url="/assets/f63_ui_api.js", status_code=307)


@app.get("/f64_ui_components.js", include_in_schema=False)
def ui_components_redirect() -> RedirectResponse:
    return RedirectResponse(url="/assets/f64_ui_components.js", status_code=307)


@app.get("/f65_ui_theme.js", include_in_schema=False)
def ui_theme_redirect() -> RedirectResponse:
    return RedirectResponse(url="/assets/f65_ui_theme.js", status_code=307)


@app.get("/f66_ui_workbench.js", include_in_schema=False)
def ui_workbench_redirect() -> RedirectResponse:
    return RedirectResponse(url="/assets/f66_ui_workbench.js", status_code=307)


@app.get("/f67_ui_artifacts.js", include_in_schema=False)
def ui_artifacts_redirect() -> RedirectResponse:
    return RedirectResponse(url="/assets/f67_ui_artifacts.js", status_code=307)


@app.get("/f68_ui_pets.js", include_in_schema=False)
def ui_pets_redirect() -> RedirectResponse:
    return RedirectResponse(url="/assets/f68_ui_pets.js", status_code=307)


@app.get("/f69_ui_motion.js", include_in_schema=False)
def ui_motion_redirect() -> RedirectResponse:
    return RedirectResponse(url="/assets/f69_ui_motion.js", status_code=307)


app.include_router(health_router)
app.include_router(runs_router)
app.include_router(tasks_router)
app.include_router(memory_router)
app.include_router(workbench_router)
app.include_router(ui_router)