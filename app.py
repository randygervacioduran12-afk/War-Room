import asyncio
import os

import uvicorn


def main() -> None:
    app_role = os.getenv("APP_ROLE", "api")

    if app_role == "api":
        uvicorn.run(
            "f10_api_main:app",
            host=os.getenv("APP_HOST", "0.0.0.0"),
            port=int(os.getenv("APP_PORT", "8000")),
            reload=os.getenv("APP_RELOAD", "false").lower() == "true",
        )
        return

    if app_role == "scheduler":
        from f40_queue_scheduler import run_scheduler_loop

        asyncio.run(run_scheduler_loop())
        return

    if app_role == "executor":
        from f41_queue_executor import run_executor_loop

        asyncio.run(run_executor_loop())
        return

    raise RuntimeError(f"Unsupported APP_ROLE={app_role}")


if __name__ == "__main__":
    main()