from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from f20_core_config import get_settings
from f11_api_runs import router as runs_router
from f12_api_tasks import router as tasks_router
from f13_api_memory import router as memory_router
from f14_api_health import router as health_router
from f16_api_ui import router as ui_router
from f17_api_workbench import router as workbench_router

settings = get_settings()

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

# API routers first
app.include_router(health_router)
app.include_router(runs_router)
app.include_router(tasks_router)
app.include_router(memory_router)
app.include_router(workbench_router)

# UI router last so it owns "/" cleanly
app.include_router(ui_router)