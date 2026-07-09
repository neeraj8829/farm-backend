from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_admin
from app.core.database import db
from app.models.schemas import PropertyUpdate


router = APIRouter(tags=["property"])


@router.get("/property")
async def get_property():
    doc = await db.property.find_one({"id": "prop-1"}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Property not configured")
    return doc


@router.patch("/property")
async def update_property(body: PropertyUpdate, user: dict = Depends(require_admin)):
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    await db.property.update_one({"id": "prop-1"}, {"$set": updates})
    return await db.property.find_one({"id": "prop-1"}, {"_id": 0})

