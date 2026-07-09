import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import close_db
from app.services.seed import seed_database


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def create_app() -> FastAPI:
    application = FastAPI(title=settings.app_title)
    application.include_router(api_router)
    application.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.on_event("startup")
    async def on_startup():
        await seed_database()

    @application.on_event("shutdown")
    async def on_shutdown():
        await close_db()

    return application


app = create_app()
