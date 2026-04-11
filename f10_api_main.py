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

app = FastAPI(
    title=getattr(settings, "app_name", "War Room"),
    version=getattr(settings, "app_version", "0.1.0"),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve current custom-shell assets from the repo root.
app.mount("/assets", StaticFiles(directory=str(BASE_DIR)), name="assets")


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

# Keep UI router last so it owns "/".
app.include_router(ui_router)