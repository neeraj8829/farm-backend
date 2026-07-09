from fastapi import APIRouter

from app.core.database import db


router = APIRouter(tags=["reviews"])


@router.get("/reviews")
async def list_reviews():
    return await db.reviews.find({}, {"_id": 0}).to_list(200)

