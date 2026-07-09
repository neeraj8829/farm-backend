from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.core.database import db
from app.models.schemas import BlockedDateToggle
from app.utils.datetime import new_id


router = APIRouter(tags=["availability"])


@router.get("/blocked-dates")
async def list_blocked():
    return await db.blocked_dates.find({}, {"_id": 0}).to_list(1000)


@router.post("/blocked-dates/toggle")
async def toggle_block(body: BlockedDateToggle, user: dict = Depends(require_admin)):
    existing = await db.blocked_dates.find_one({"date": body.date})
    if existing:
        await db.blocked_dates.delete_one({"date": body.date})
        return {"date": body.date, "blocked": False}

    await db.blocked_dates.insert_one(
        {"id": new_id(), "date": body.date, "source": "direct"}
    )
    return {"date": body.date, "blocked": True}

