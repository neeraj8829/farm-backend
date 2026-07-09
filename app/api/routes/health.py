from fastapi import APIRouter

from app.utils.datetime import now_utc


router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok", "time": now_utc().isoformat()}


@router.get("/")
async def root():
    return {"name": "Serenity Farmhouse API", "status": "ok"}
