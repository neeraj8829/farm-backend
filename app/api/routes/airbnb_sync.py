from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.core.database import db
from app.models.schemas import AirbnbSyncUpdate
from app.utils.datetime import now_utc


router = APIRouter(tags=["airbnb-sync"])


@router.get("/airbnb-sync")
async def get_sync(user: dict = Depends(require_admin)):
    return await db.airbnb_sync.find_one({"id": "sync-1"}, {"_id": 0})


@router.patch("/airbnb-sync")
async def update_sync(body: AirbnbSyncUpdate, user: dict = Depends(require_admin)):
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if updates:
        await db.airbnb_sync.update_one({"id": "sync-1"}, {"$set": updates})
    return await db.airbnb_sync.find_one({"id": "sync-1"}, {"_id": 0})


@router.post("/airbnb-sync/run")
async def run_sync(user: dict = Depends(require_admin)):
    await db.airbnb_sync.update_one(
        {"id": "sync-1"},
        {"$set": {"lastSyncedAt": now_utc().isoformat()}},
    )
    return await db.airbnb_sync.find_one({"id": "sync-1"}, {"_id": 0})

