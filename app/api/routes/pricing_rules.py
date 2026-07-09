from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_admin
from app.core.database import db
from app.models.schemas import PricingRuleCreate
from app.utils.datetime import new_id


router = APIRouter(tags=["pricing"])


@router.get("/pricing-rules")
async def list_rules():
    return await db.pricing_rules.find({}, {"_id": 0}).to_list(500)


@router.post("/pricing-rules")
async def create_rule(body: PricingRuleCreate, user: dict = Depends(require_admin)):
    doc = {"id": new_id(), **body.model_dump()}
    await db.pricing_rules.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.delete("/pricing-rules/{rid}")
async def delete_rule(rid: str, user: dict = Depends(require_admin)):
    result = await db.pricing_rules.delete_one({"id": rid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"ok": True}

