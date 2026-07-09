import asyncio
import contextlib
import logging
import os

import requests
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import close_db
from app.services.seed import seed_database


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("serenity")

KEEP_ALIVE_URL = os.environ.get(
    "KEEP_ALIVE_URL", "https://farm-backend-59r4.onrender.com/api/health"
)
KEEP_ALIVE_INTERVAL_SECONDS = int(os.environ.get("KEEP_ALIVE_INTERVAL_SECONDS", "840"))
KEEP_ALIVE_ENABLED = os.environ.get("KEEP_ALIVE_ENABLED", "true").lower() not in {
    "0",
    "false",
    "no",
    "off",
}


async def keep_render_awake() -> None:
    """Ping the public Render health URL while this instance is running."""
    if not KEEP_ALIVE_URL:
        log.info("Keep-alive disabled: KEEP_ALIVE_URL is empty")
        return

    while True:
        await asyncio.sleep(KEEP_ALIVE_INTERVAL_SECONDS)
        try:
            response = await asyncio.to_thread(
                requests.get, KEEP_ALIVE_URL, timeout=10
            )
            log.info(
                "Keep-alive ping to %s returned %s",
                KEEP_ALIVE_URL,
                response.status_code,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Keep-alive ping failed")


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_title)
    application.include_router(api_router)
    application.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origin_regex=".*",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.on_event("startup")
    async def on_startup():
        await seed_database()
        if KEEP_ALIVE_ENABLED:
            application.state.keep_alive_task = asyncio.create_task(keep_render_awake())
            log.info(
                "Keep-alive enabled: pinging %s every %s seconds",
                KEEP_ALIVE_URL,
                KEEP_ALIVE_INTERVAL_SECONDS,
            )

    @application.on_event("shutdown")
    async def on_shutdown():
        task = getattr(application.state, "keep_alive_task", None)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await close_db()

    return application


app = create_app()

