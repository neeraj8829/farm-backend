from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_admin
from app.core.database import db
from app.models.schemas import MediaCreate
from app.utils.datetime import new_id, now_utc


router = APIRouter(tags=["media"])


@router.get("/media")
async def list_media():
    return await db.media.find({}, {"_id": 0}).sort("sortOrder", 1).to_list(500)


@router.post("/media")
async def create_media(body: MediaCreate, user: dict = Depends(require_admin)):
    count = await db.media.count_documents({})
    doc = {
        "id": new_id(),
        "type": body.type,
        "category": body.category,
        "url": body.url,
        "alt": body.alt,
        "isHero": body.isHero,
        "sortOrder": count,
        "created_at": now_utc().isoformat(),
    }
    if body.isHero:
        await db.media.update_many({}, {"$set": {"isHero": False}})
    await db.media.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.patch("/media/{mid}/hero")
async def set_hero(mid: str, user: dict = Depends(require_admin)):
    if not await db.media.find_one({"id": mid}):
        raise HTTPException(status_code=404, detail="Media not found")
    await db.media.update_many({}, {"$set": {"isHero": False}})
    await db.media.update_one({"id": mid}, {"$set": {"isHero": True}})
    return {"ok": True}


@router.delete("/media/{mid}")
async def delete_media(mid: str, user: dict = Depends(require_admin)):
    result = await db.media.delete_one({"id": mid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Media not found")
    return {"ok": True}

